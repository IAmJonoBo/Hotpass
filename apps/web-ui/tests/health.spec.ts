import { test, expect } from '@playwright/test'

const healthyPayload = { status: 'healthy' }

test.describe('Health page', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/prefect/health', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(healthyPayload) })
    })
    await page.route('**/api/marquez/api/v1/namespaces', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ namespaces: [] }) })
    })
    await page.route('**/arc/status.json', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, verified_at: new Date().toISOString() }),
      })
    })
  })

  test('shows service cards', async ({ page }) => {
    await page.goto('/health')
    await expect(page.getByRole('heading', { name: 'Prefect API' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Marquez / OpenLineage' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'ARC Runner Lifecycle' })).toBeVisible()
  })
})
