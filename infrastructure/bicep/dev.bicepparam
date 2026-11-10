using './main.bicep'

param location = 'centralindia'
param environmentName = 'aeroops-dev-container-env'

param tags = {
  project: 'AeroOps'
  environment: 'development'
  managedBy: 'Bicep'
}
