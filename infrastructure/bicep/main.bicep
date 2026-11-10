@description('Azure region for the AeroOps deployment.')
param location string = resourceGroup().location

@description('Name of the Azure Container Apps environment.')
param environmentName string = 'aeroops-container-env'

@description('Project metadata.')
param tags object = {
  project: 'AeroOps'
  environment: 'development'
  managedBy: 'Bicep'
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    zoneRedundant: false
  }
}

output environmentId string = containerAppsEnvironment.id
output environmentName string = containerAppsEnvironment.name
output deploymentLocation string = containerAppsEnvironment.location
