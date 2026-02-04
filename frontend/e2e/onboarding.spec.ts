import { test, expect } from '@playwright/test'

test.describe('VentureBot Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('displays the app header and branding', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('VentureBot')
    await expect(page.locator('.logo-icon')).toContainText('🚀')
  })

  test('shows journey progress with all stages', async ({ page }) => {
    await expect(page.locator('.journey-progress')).toBeVisible()
    await expect(page.locator('.step-label').filter({ hasText: 'Discovery' })).toBeVisible()
    await expect(page.locator('.step-label').filter({ hasText: 'Ideas' })).toBeVisible()
    await expect(page.locator('.step-label').filter({ hasText: 'Validate' })).toBeVisible()
    await expect(page.locator('.step-label').filter({ hasText: 'PRD' })).toBeVisible()
    await expect(page.locator('.step-label').filter({ hasText: 'Build' })).toBeVisible()
    await expect(page.locator('.step-label').filter({ hasText: 'Launch' })).toBeVisible()
  })

  test('shows empty state when starting fresh', async ({ page }) => {
    await expect(page.getByText('Ready to unlock your startup idea?')).toBeVisible()
    await expect(page.getByText('Discover pain points')).toBeVisible()
    await expect(page.getByText('Validate ideas')).toBeVisible()
    await expect(page.getByText('Build with AI')).toBeVisible()
  })

  test('has a message input and send button', async ({ page }) => {
    const textarea = page.locator('textarea[name="message"]')
    await expect(textarea).toBeVisible()

    const sendButton = page.locator('button[type="submit"]')
    await expect(sendButton).toBeVisible()
  })

  test('send button is disabled when input is empty', async ({ page }) => {
    const sendButton = page.locator('button[type="submit"]')
    await expect(sendButton).toBeDisabled()
  })

  test('shows connection status indicator', async ({ page }) => {
    const connectionPill = page.locator('.connection-pill')
    await expect(connectionPill).toBeVisible()
  })

  test('can type in the message input', async ({ page }) => {
    const textarea = page.locator('textarea[name="message"]')
    await textarea.fill('Hello, I want to start a business')
    await expect(textarea).toHaveValue('Hello, I want to start a business')
  })

  test('send button becomes enabled when input has text', async ({ page }) => {
    const textarea = page.locator('textarea[name="message"]')
    const sendButton = page.locator('button[type="submit"]')

    // Wait for connection
    await page.waitForSelector('.connection-pill--ready', { timeout: 10000 }).catch(() => {
      // Connection might not be ready in test environment
    })

    await textarea.fill('Test message')

    // Button should be enabled if connected, or still disabled if not
    const isConnected = await page.locator('.connection-pill--ready').isVisible().catch(() => false)
    if (isConnected) {
      await expect(sendButton).toBeEnabled()
    }
  })

  test('displays helper text for keyboard shortcuts', async ({ page }) => {
    await expect(page.getByText('to send')).toBeVisible()
    await expect(page.getByText('for new line')).toBeVisible()
  })
})

test.describe('VentureBot Chat Interaction', () => {
  test('can send a message and receive response', async ({ page }) => {
    await page.goto('/')

    // Wait for WebSocket connection
    await page.waitForSelector('.connection-pill--ready', { timeout: 15000 }).catch(() => {
      test.skip(true, 'Backend not available')
    })

    const textarea = page.locator('textarea[name="message"]')
    const sendButton = page.locator('button[type="submit"]')

    // Type and send message
    await textarea.fill('Hi, my name is Alex and I hate managing spreadsheets')
    await sendButton.click()

    // Wait for user message to appear
    await expect(page.locator('.message--user').first()).toBeVisible({ timeout: 5000 })

    // Wait for assistant response
    await expect(page.locator('.message--assistant').first()).toBeVisible({ timeout: 30000 })
  })
})

test.describe('Journey Stage Progression', () => {
  test('starts in onboarding/discovery stage', async ({ page }) => {
    await page.goto('/')

    // The first stage should be highlighted as current
    const discoveryStep = page.locator('.journey-step').first()
    await expect(discoveryStep).toContainText('Discovery')
  })
})
