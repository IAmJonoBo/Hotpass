/**
 * ARC status API client
 *
 * Reads lifecycle verification summaries emitted by the CLI helper.
 */

export interface ArcStatus {
  success: boolean
  verifiedAt: string
  identityArn?: string
  identityAccount?: string
  identitySource?: string
  notes?: string
}

const getStatusUrl = (): string => {
  return (
    import.meta.env.ARC_STATUS_URL ||
    import.meta.env.VITE_ARC_STATUS_URL ||
    '/arc/status.json'
  )
}

export async function fetchArcStatus(): Promise<ArcStatus | null> {
  const url = getStatusUrl()
  try {
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' },
    })
    if (!response.ok) {
      throw new Error(`ARC status request failed: ${response.statusText}`)
    }
    const payload = await response.json()
    return {
      success: Boolean(payload?.success),
      verifiedAt: payload?.verified_at || payload?.verifiedAt || new Date().toISOString(),
      identityArn: payload?.identity?.arn,
      identityAccount: payload?.identity?.account,
      identitySource: payload?.identity?.source,
      notes: payload?.notes,
    }
  } catch (error) {
    console.warn('Failed to load ARC status', error)
    return null
  }
}
