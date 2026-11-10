
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import './App.css'

type Aircraft = {
  id: number
  registration: string
  aircraft_type: string
  manufacturer: string
  status: 'operational' | 'maintenance' | 'grounded'
  created_at: string
}

type WorkOrder = {
  id: number
  work_order_number: string
  aircraft_id: number
  title: string
  description: string | null
  priority: 'low' | 'normal' | 'high' | 'critical'
  status: 'open' | 'in_progress' | 'blocked' | 'completed' | 'cancelled'
  due_date: string
  created_at: string
}

type ApiState = 'loading' | 'connected' | 'error'
const REPORTING_DATE = new Date()

function formatDate(value: string) {
  return new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString(
    'en-GB',
    { day: '2-digit', month: 'short', year: 'numeric' },
  )
}

function App() {
  const [aircraft, setAircraft] = useState<Aircraft[]>([])
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [apiState, setApiState] = useState<ApiState>('loading')
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [submitSuccess, setSubmitSuccess] = useState('')

  const [updatingWorkOrderId, setUpdatingWorkOrderId] = useState<number | null>(null)
  const [updateError, setUpdateError] = useState('')
  const [updateSuccess, setUpdateSuccess] = useState('')

  const [formAircraftId, setFormAircraftId] = useState('')
  const [formTitle, setFormTitle] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formPriority, setFormPriority] = useState<
    'low' | 'normal' | 'high' | 'critical'
  >('normal')
  const [formDueDate, setFormDueDate] = useState('')

  const loadDashboard = useCallback(async () => {
    try {
      const [aircraftResponse, workOrderResponse] = await Promise.all([
        fetch('/api/v1/aircraft'),
        fetch('/api/v1/work-orders?limit=100&sort_by=due_date&sort_order=asc'),
      ])

      if (!aircraftResponse.ok || !workOrderResponse.ok) {
        throw new Error('The aviation operations API returned an error.')
      }

      const aircraftData: Aircraft[] = await aircraftResponse.json()
      const workOrderData: WorkOrder[] = await workOrderResponse.json()

      setAircraft(aircraftData)
      setWorkOrders(workOrderData)
      setApiState('connected')
      setLastUpdated(new Date())
    } catch (err) {
      setApiState('error')
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to connect to the backend API.',
      )
    }
  }, [])


  const handleCreateWorkOrder = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    setSubmitting(true)
    setSubmitError('')
    setSubmitSuccess('')

    try {
      const response = await fetch('/api/v1/work-orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          aircraft_id: Number(formAircraftId),
          title: formTitle.trim(),
          description: formDescription.trim() || null,
          priority: formPriority,
          status: 'open',
          due_date: formDueDate,
        }),
      })

      if (!response.ok) {
        let message = 'Unable to create work order.'

        try {
          const payload = await response.json()

          if (Array.isArray(payload.detail)) {
            message = payload.detail
              .map(
                (item: {
                  loc?: (string | number)[]
                  msg?: string
                }) =>
                  `${item.loc?.slice(1).join('.') || 'Field'}: ${item.msg || 'Invalid value'}`,
              )
              .join('; ')
          } else if (typeof payload.detail === 'string') {
            message = payload.detail
          }
        } catch {
          // Keep the default error message if the response is not JSON.
        }

        throw new Error(message)
      }

      const created: WorkOrder = await response.json()

      setSubmitSuccess(
        `Work order ${created.work_order_number} created successfully.`,
      )

      setShowCreateForm(false)
      setFormAircraftId('')
      setFormTitle('')
      setFormDescription('')
      setFormPriority('normal')
      setFormDueDate('')

      await loadDashboard()
    } catch (err) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred while creating the work order.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateWorkOrder = async (
    workOrderId: number,
    changes: {
      status?: WorkOrder['status']
      priority?: WorkOrder['priority']
    },
  ) => {
    setUpdatingWorkOrderId(workOrderId)
    setUpdateError('')
    setUpdateSuccess('')

    try {
      const response = await fetch(`/api/v1/work-orders/${workOrderId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(changes),
      })

      if (!response.ok) {
        let message = 'Unable to update work order.'

        try {
          const payload = await response.json()
          if (typeof payload.detail === 'string') {
            message = payload.detail
          } else if (Array.isArray(payload.detail)) {
            message = payload.detail
              .map((item: { msg?: string }) => item.msg || 'Invalid value')
              .join('; ')
          }
        } catch {
          // Keep the default error message if the response is not JSON.
        }

        throw new Error(`HTTP ${response.status}: ${message}`)
      }

      const updated: WorkOrder = await response.json()

      setUpdateSuccess(
        `Work order ${updated.work_order_number} updated successfully.`,
      )

      await loadDashboard()
    } catch (err) {
      setUpdateError(
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred while updating the work order.',
      )
    } finally {
      setUpdatingWorkOrderId(null)
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [loadDashboard])

  const operationalAircraft = aircraft.filter(
    (item) => item.status === 'operational',
  ).length

  const maintenanceAircraft = aircraft.filter(
    (item) => item.status === 'maintenance',
  ).length

  const openOrders = workOrders.filter(
    (item) => item.status === 'open' || item.status === 'in_progress',
  ).length

  const blockedOrders = workOrders.filter(
    (item) => item.status === 'blocked',
  ).length

  const criticalOrders = workOrders.filter(
    (item) => item.priority === 'critical' &&
      !['completed', 'cancelled'].includes(item.status),
  ).length

  const today = REPORTING_DATE.toISOString().slice(0, 10)
  const overdueOrders = workOrders.filter(
    (item) =>
      item.due_date < today &&
      !['completed', 'cancelled'].includes(item.status),
  ).length

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-symbol">A</div>
          <div>
            <div className="brand-name">AERO<span>OPS</span></div>
            <div className="brand-caption">AVIATION OPERATIONS</div>
          </div>
        </div>

        <div className="nav-section-label">WORKSPACE</div>
        <nav className="navigation">
          <a className="nav-item active" href="#overview">
            <span className="nav-icon">O</span>
            Overview
          </a>
          <a className="nav-item" href="#fleet">
            <span className="nav-icon">O</span>
            Aircraft fleet
          </a>
          <a className="nav-item" href="#work-orders">
            <span className="nav-icon">O</span>
            Maintenance orders
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="environment-card">
            <span className="environment-dot" />
            <div>
              <strong>Development</strong>
              <span>Local environment</span>
            </div>
          </div>
          <div className="sidebar-footer">
            Independent portfolio project<br />
            Aviation Operations Platform
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> Overview
          </div>
          <div className="topbar-right">
            <div className={`api-indicator ${apiState}`}>
              <span className="api-dot" />
              API {apiState === 'connected'
                ? 'Connected'
                : apiState === 'loading'
                  ? 'Connecting'
                  : 'Disconnected'}
            </div>
            <button
              className="refresh-button"
              onClick={() => void loadDashboard()}
              disabled={apiState === 'loading'}
            >
              R <span>Refresh</span>
            </button>
            <div className="user-avatar">AT</div>
          </div>
        </header>

        <div className="page-content" id="overview">
          <section className="page-heading">
            <div>
              <div className="eyebrow">OPERATIONS CONTROL CENTRE</div>
              <h1>Overview</h1>
              <p className="page-description">
                Monitor fleet readiness and maintenance activity.
              </p>
            </div>
            <div className="heading-date">
              <span>REPORTING DATE</span>
              <strong>
                {REPORTING_DATE.toLocaleDateString('en-GB', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric',
                })}
              </strong>
            </div>
          </section>

          {apiState === 'error' && (
            <div className="error-banner">
              <strong>Connection problem</strong>
              <span>{error}</span>
              <button onClick={() => {
  setApiState('loading')
  void loadDashboard()
}}>Try again</button>
            </div>
          )}

          <section className="metrics-grid" aria-label="Operations statistics">
            <article className="metric-card">
              <div className="metric-top">
                <span>Total aircraft</span>
                <span className="metric-icon blue">A</span>
              </div>
              <div className="metric-value">{aircraft.length}</div>
              <div className="metric-note">Registered in fleet</div>
            </article>

            <article className="metric-card">
              <div className="metric-top">
                <span>Operational fleet</span>
                <span className="metric-icon green">OK</span>
              </div>
              <div className="metric-value">{operationalAircraft}</div>
              <div className="metric-note">Aircraft ready for service</div>
            </article>

            <article className="metric-card">
              <div className="metric-top">
                <span>Active work orders</span>
                <span className="metric-icon orange">WO</span>
              </div>
              <div className="metric-value">{openOrders}</div>
              <div className="metric-note">Open and in progress</div>
            </article>

            <article className="metric-card">
              <div className="metric-top">
                <span>Critical priorities</span>
                <span className="metric-icon red">!</span>
              </div>
              <div className="metric-value">{criticalOrders}</div>
              <div className="metric-note">Require close attention</div>
            </article>
          </section>

          <section className="secondary-metrics">
            <div>
              <span className="secondary-label">Aircraft in maintenance</span>
              <strong>{maintenanceAircraft}</strong>
            </div>
            <div>
              <span className="secondary-label">Overdue work orders</span>
              <strong className={overdueOrders > 0 ? 'danger-text' : ''}>
                {overdueOrders}
              </strong>
            </div>
            <div>
              <span className="secondary-label">Blocked work orders</span>
              <strong className={blockedOrders > 0 ? 'danger-text' : ''}>
                {blockedOrders}
              </strong>
            </div>
            <div>
              <span className="secondary-label">Completed work orders</span>
              <strong>
                {workOrders.filter((item) => item.status === 'completed').length}
              </strong>
            </div>
          </section>

          <section className="content-panel" id="fleet">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">FLEET MANAGEMENT</div>
                <h2>Aircraft fleet</h2>
                <p>Aircraft registered in the operations database.</p>
              </div>
              <span className="record-count">{aircraft.length} RECORDS</span>
            </div>

                        <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>REGISTRATION</th>
                    <th>AIRCRAFT TYPE</th>
                    <th>MANUFACTURER</th>
                    <th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {aircraft.map((item) => (
                    <tr key={item.id}>
                      <td className="registration-cell">{item.registration}</td>
                      <td>{item.aircraft_type}</td>
                      <td>{item.manufacturer}</td>
                      <td>
                        <span className={`status-badge ${item.status}`}>
                          {item.status.replace('_', ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {aircraft.length === 0 && apiState !== 'loading' && (
                    <tr>
                      <td colSpan={4} className="empty-state">
                        No aircraft records found.
                      </td>
                    </tr>
                  )}
                  {apiState === 'loading' && aircraft.length === 0 && (
                    <tr>
                      <td colSpan={4} className="empty-state">
                        Loading aircraft data...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="content-panel" id="work-orders">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">MAINTENANCE CONTROL</div>
                <h2>Recent work orders</h2>
                <p>Track scheduled inspections and maintenance tasks.</p>
              </div>
              <div className="work-order-actions">
                <span className="record-count">{workOrders.length} RECORDS</span>
                <button
                  type="button"
                  className="create-button"
                  onClick={() => {
                    setSubmitError('')
                    setSubmitSuccess('')
                    setShowCreateForm((current) => !current)
                  }}
                >
                  {showCreateForm ? 'Cancel' : '+ Create Work Order'}
                </button>
              </div>
            </div>

            {submitSuccess && (
              <div className="form-success" role="status">
                {submitSuccess}
              </div>
            )}

            {showCreateForm && (
              <form
                className="create-work-order-form"
                onSubmit={handleCreateWorkOrder}
              >
                <div className="form-heading">
                  <h3>Create maintenance work order</h3>
                  <p>
                    Register a new maintenance task against an aircraft in the fleet.
                  </p>
                </div>

                {submitError && (
                  <div className="form-error" role="alert">
                    {submitError}
                  </div>
                )}

                <div className="form-grid">
                  <div className="form-field">
                    <label htmlFor="form-aircraft">Aircraft</label>
                    <select
                      id="form-aircraft"
                      value={formAircraftId}
                      onChange={(event) => setFormAircraftId(event.target.value)}
                      required
                      disabled={aircraft.length === 0}
                    >
                      <option value="">Select an aircraft</option>
                      {aircraft.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.registration} - {item.aircraft_type}
                        </option>
                      ))}
                    </select>
                    {aircraft.length === 0 && (
                      <small>No aircraft are currently available.</small>
                    )}
                  </div>

                  <div className="form-field">
                    <label htmlFor="form-title">Work order title</label>
                    <input
                      id="form-title"
                      type="text"
                      value={formTitle}
                      onChange={(event) => setFormTitle(event.target.value)}
                      minLength={4}
                      maxLength={160}
                      placeholder="e.g. Scheduled engine inspection"
                      required
                    />
                  </div>

                  <div className="form-field">
                    <label htmlFor="form-priority">Priority</label>
                    <select
                      id="form-priority"
                      value={formPriority}
                      onChange={(event) =>
                        setFormPriority(
                          event.target.value as 'low' | 'normal' | 'high' | 'critical',
                        )
                      }
                    >
                      <option value="low">Low</option>
                      <option value="normal">Normal</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>

                  <div className="form-field">
                    <label htmlFor="form-due-date">Due date</label>
                    <input
                      id="form-due-date"
                      type="date"
                      value={formDueDate}
                      onChange={(event) => setFormDueDate(event.target.value)}
                      min={today}
                      required
                    />
                  </div>

                  <div className="form-field form-field-full">
                    <label htmlFor="form-description">Description</label>
                    <textarea
                      id="form-description"
                      value={formDescription}
                      onChange={(event) => setFormDescription(event.target.value)}
                      rows={3}
                      placeholder="Add maintenance details or inspection notes..."
                    />
                  </div>
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    className="cancel-button"
                    onClick={() => {
                      setShowCreateForm(false)
                      setSubmitError('')
                    }}
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="create-button"
                    disabled={submitting || aircraft.length === 0}
                  >
                    {submitting ? 'Creating...' : 'Create Work Order'}
                  </button>
                </div>
              </form>
            )}
            {updateError && (
              <div className="update-feedback error" role="alert">
                {updateError}
              </div>
            )}
            {updateSuccess && (
              <div className="update-feedback success" role="status">
                {updateSuccess}
              </div>
            )}            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>WORK ORDER</th>
                    <th>TASK</th>
                    <th>PRIORITY</th>
                    <th>STATUS</th>
                    <th>DUE DATE</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {workOrders.map((item) => (
                    <tr key={item.id}>
                      <td className="registration-cell">{item.work_order_number}</td>
                      <td>
                        <div className="task-title">{item.title}</div>
                        <div className="task-subtitle">
                          Aircraft ID: {item.aircraft_id}
                        </div>
                      </td>
                      <td>
                        <span className={`priority-badge ${item.priority}`}>
                          {item.priority}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${item.status}`}>
                          {item.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>{formatDate(item.due_date)}</td>
                      <td>
                        <div className="work-order-action-cell">
                          <select
                            className="work-order-control"
                            aria-label={`Update status for ${item.work_order_number}`}
                            value={item.status}
                            disabled={
                              updatingWorkOrderId === item.id ||
                              ['completed', 'cancelled'].includes(item.status)
                            }
                            onChange={(event) =>
                              void handleUpdateWorkOrder(item.id, {
                                status: event.target.value as WorkOrder['status'],
                              })
                            }
                          >
                            {item.status === 'open' && (
                              <>
                                <option value="open">Open</option>
                                <option value="in_progress">In Progress</option>
                                <option value="cancelled">Cancelled</option>
                              </>
                            )}
                            {item.status === 'in_progress' && (
                              <>
                                <option value="in_progress">In Progress</option>
                                <option value="blocked">Blocked</option>
                                <option value="completed">Completed</option>
                                <option value="cancelled">Cancelled</option>
                              </>
                            )}
                            {item.status === 'blocked' && (
                              <>
                                <option value="blocked">Blocked</option>
                                <option value="in_progress">In Progress</option>
                                <option value="cancelled">Cancelled</option>
                              </>
                            )}
                            {item.status === 'completed' && (
                              <option value="completed">Completed</option>
                            )}
                            {item.status === 'cancelled' && (
                              <option value="cancelled">Cancelled</option>
                            )}
                          </select>
                          <select
                            className="work-order-control"
                            aria-label={`Update priority for ${item.work_order_number}`}
                            value={item.priority}
                            disabled={updatingWorkOrderId !== null}
                            onChange={(event) =>
                              void handleUpdateWorkOrder(item.id, {
                                priority: event.target.value as WorkOrder['priority'],
                              })
                            }
                          >
                            <option value="low">Low Priority</option>
                            <option value="normal">Normal Priority</option>
                            <option value="high">High Priority</option>
                            <option value="critical">Critical Priority</option>
                          </select>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {workOrders.length === 0 && apiState !== 'loading' && (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        No work orders found.
                      </td>
                    </tr>
                  )}
                  {apiState === 'loading' && workOrders.length === 0 && (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        Loading maintenance data...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <footer className="page-footer">
            <span>AVIATION OPERATIONS PLATFORM</span>
            <span>
              {lastUpdated
                ? `Last synchronised ${lastUpdated.toLocaleTimeString()}`
                : 'Waiting for API synchronisation'}
            </span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
