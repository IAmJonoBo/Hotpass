/**
 * Admin Page
 *
 * Configuration interface for:
 * - Prefect API URL and key
 * - Marquez/OpenLineage API URL
 * - Environment settings
 *
 * Settings are persisted to localStorage
 */

import { useState, useEffect } from 'react'
import { Save, Check, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { LLMProviderSelector } from '@/components/settings/LLMProviderSelector'

interface ConfigSettings {
  prefectApiUrl: string
  marquezApiUrl: string
  environment: 'local' | 'staging' | 'prod'
  telemetryEnabled: boolean
}

const DEFAULT_SETTINGS: ConfigSettings = {
  prefectApiUrl: import.meta.env.VITE_PREFECT_API_URL || 'http://localhost:4200',
  marquezApiUrl: import.meta.env.VITE_MARQUEZ_API_URL || 'http://localhost:5000',
  environment: (import.meta.env.VITE_ENVIRONMENT as ConfigSettings['environment']) || 'local',
  telemetryEnabled: true,
}

export function Admin() {
  const [settings, setSettings] = useState<ConfigSettings>(DEFAULT_SETTINGS)
  const [saved, setSaved] = useState(false)
  const [testingConnection, setTestingConnection] = useState<{
    prefect: boolean
    marquez: boolean
  }>({ prefect: false, marquez: false })
  const [connectionStatus, setConnectionStatus] = useState<{
    prefect: 'unknown' | 'success' | 'error'
    marquez: 'unknown' | 'success' | 'error'
  }>({ prefect: 'unknown', marquez: 'unknown' })

  // Load settings from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('hotpass_config')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setSettings({ ...DEFAULT_SETTINGS, ...parsed })
      } catch (error) {
        console.error('Failed to parse stored config:', error)
      }
    }
  }, [])

  const handleSave = () => {
    // Save to localStorage
    localStorage.setItem('hotpass_config', JSON.stringify(settings))
    localStorage.setItem('hotpass_environment', settings.environment)

    setSaved(true)
    setTimeout(() => setSaved(false), 2000)

    // In a real implementation, you might also want to reload the page
    // or update a global config context
  }

  const testConnection = async (type: 'prefect' | 'marquez') => {
    setTestingConnection(prev => ({ ...prev, [type]: true }))

    try {
      const url = type === 'prefect' ? settings.prefectApiUrl : settings.marquezApiUrl
      const testEndpoint = type === 'prefect'
        ? `${url}/health`
        : `${url}/api/v1/namespaces`

      const response = await fetch(testEndpoint, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      })

      if (response.ok) {
        setConnectionStatus(prev => ({ ...prev, [type]: 'success' }))
      } else {
        setConnectionStatus(prev => ({ ...prev, [type]: 'error' }))
      }
    } catch {
      setConnectionStatus(prev => ({ ...prev, [type]: 'error' }))
    } finally {
      setTestingConnection(prev => ({ ...prev, [type]: false }))
    }
  }

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS)
    localStorage.removeItem('hotpass_config')
    localStorage.removeItem('hotpass_environment')
    setConnectionStatus({ prefect: 'unknown', marquez: 'unknown' })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Settings</h1>
        <p className="text-muted-foreground">
          Configure API endpoints and environment settings
        </p>
      </div>

      {/* Alert - Settings are local */}
      <Card className="border-yellow-500/50 bg-yellow-500/10">
        <CardContent className="flex items-start gap-3 pt-6">
          <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
          <div className="flex-1">
            <div className="font-semibold text-sm">Local Configuration</div>
            <p className="text-xs text-muted-foreground mt-1">
              Settings are stored in your browser's localStorage. They will not sync across devices
              or be shared with other users.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* LLM Provider Selector */}
      <LLMProviderSelector />

      {/* Environment Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Environment</CardTitle>
          <CardDescription>
            Select the current environment for proper labeling and behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Current Environment</label>
            <div className="flex gap-2">
              {(['local', 'staging', 'prod'] as const).map((env) => (
                <Button
                  key={env}
                  variant={settings.environment === env ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSettings({ ...settings, environment: env })}
                >
                  {env === 'prod' ? 'Production' : env.charAt(0).toUpperCase() + env.slice(1)}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Prefect API Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Prefect API</CardTitle>
          <CardDescription>
            Configure connection to Prefect Cloud or Server for flow run data
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="prefectUrl" className="text-sm font-medium mb-2 block">
              API URL
            </label>
            <Input
              id="prefectUrl"
              type="url"
              placeholder="http://localhost:4200"
              value={settings.prefectApiUrl}
              onChange={(e) => setSettings({ ...settings, prefectApiUrl: e.target.value })}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Base URL for the Prefect API (e.g., http://localhost:4200 or https://api.prefect.cloud)
            </p>
            {settings.prefectApiUrl.includes('.internal') && (
              <div className="mt-2 bg-yellow-500/10 border border-yellow-500/20 rounded p-2 text-xs">
                <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400 font-medium">
                  <AlertCircle className="h-3 w-3" />
                  VPC/Internal URL Detected
                </div>
                <p className="text-muted-foreground mt-1">
                  This URL appears to be in a private VPC. Make sure you're connected via VPN or
                  bastion tunnel before testing the connection.
                </p>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => testConnection('prefect')}
              disabled={testingConnection.prefect}
            >
              {testingConnection.prefect ? 'Testing...' : 'Test Connection'}
            </Button>
            {connectionStatus.prefect === 'success' && (
              <Badge variant="outline" className="text-green-600 dark:text-green-400">
                <Check className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            )}
            {connectionStatus.prefect === 'error' && (
              <Badge variant="outline" className="text-red-600 dark:text-red-400">
                <AlertCircle className="h-3 w-3 mr-1" />
                Failed
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Marquez API Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Marquez / OpenLineage API</CardTitle>
          <CardDescription>
            Configure connection to Marquez backend for lineage data
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="marquezUrl" className="text-sm font-medium mb-2 block">
              API URL
            </label>
            <Input
              id="marquezUrl"
              type="url"
              placeholder="http://localhost:5000"
              value={settings.marquezApiUrl}
              onChange={(e) => setSettings({ ...settings, marquezApiUrl: e.target.value })}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Base URL for the Marquez API (e.g., http://localhost:5000 or https://marquez.staging.internal)
            </p>
            {settings.marquezApiUrl.includes('.internal') && (
              <div className="mt-2 bg-yellow-500/10 border border-yellow-500/20 rounded p-2 text-xs">
                <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400 font-medium">
                  <AlertCircle className="h-3 w-3" />
                  VPC/Internal URL Detected
                </div>
                <p className="text-muted-foreground mt-1">
                  This URL appears to be in a private VPC. Make sure you're connected via VPN or
                  bastion tunnel before testing the connection.
                </p>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => testConnection('marquez')}
              disabled={testingConnection.marquez}
            >
              {testingConnection.marquez ? 'Testing...' : 'Test Connection'}
            </Button>
            {connectionStatus.marquez === 'success' && (
              <Badge variant="outline" className="text-green-600 dark:text-green-400">
                <Check className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            )}
            {connectionStatus.marquez === 'error' && (
              <Badge variant="outline" className="text-red-600 dark:text-red-400">
                <AlertCircle className="h-3 w-3 mr-1" />
                Failed
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* UI Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>UI Preferences</CardTitle>
          <CardDescription>
            Customize the user interface behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">Telemetry Strip</label>
              <p className="text-xs text-muted-foreground mt-1">
                Show system status bar at the top of each page
              </p>
            </div>
            <Button
              variant={settings.telemetryEnabled ? 'default' : 'outline'}
              size="sm"
              onClick={() =>
                setSettings({ ...settings, telemetryEnabled: !settings.telemetryEnabled })
              }
            >
              {settings.telemetryEnabled ? 'Enabled' : 'Disabled'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={handleReset}>
          Reset to Defaults
        </Button>
        <Button onClick={handleSave} className="min-w-[100px]">
          {saved ? (
            <>
              <Check className="mr-2 h-4 w-4" />
              Saved!
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
