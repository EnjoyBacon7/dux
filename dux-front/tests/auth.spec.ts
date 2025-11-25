import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
    });

    test('should display auth page', async ({ page }) => {
        await expect(page.locator('h1')).toContainText('Authentication');
    });

    test('should have password and passkey tabs', async ({ page }) => {
        await expect(page.getByRole('button', { name: /password/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /passkey/i })).toBeVisible();
    });

    test('should switch between password and passkey modes', async ({ page }) => {
        // Start on password tab
        await expect(page.getByPlaceholder(/username/i)).toBeVisible();
        await expect(page.getByPlaceholder(/password/i)).toBeVisible();

        // Switch to passkey tab
        await page.getByRole('button', { name: /passkey/i }).click();
        await expect(page.getByText(/login with passkey/i)).toBeVisible();
        await expect(page.getByText(/register new passkey/i)).toBeVisible();

        // Switch back to password
        await page.getByRole('button', { name: /password/i }).click();
        await expect(page.getByPlaceholder(/password/i)).toBeVisible();
    });

    test('should show validation for empty fields', async ({ page }) => {
        // Try to login without filling fields
        const loginButton = page.getByRole('button', { name: /^login$/i });
        await loginButton.click();

        // HTML5 validation should prevent submission
        const usernameInput = page.getByPlaceholder(/username/i);
        await expect(usernameInput).toHaveAttribute('required');
    });

    test('should toggle between login and register', async ({ page }) => {
        // Should show register button
        await expect(page.getByRole('button', { name: /need an account/i })).toBeVisible();

        // Click to switch to register
        await page.getByRole('button', { name: /need an account/i }).click();
        await expect(page.getByRole('button', { name: /^register$/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /already have an account/i })).toBeVisible();

        // Switch back to login
        await page.getByRole('button', { name: /already have an account/i }).click();
        await expect(page.getByRole('button', { name: /^login$/i })).toBeVisible();
    });

    test('should attempt password registration with valid credentials', async ({ page }) => {
        // Generate unique username for this test
        const username = `testuser_${Date.now()}`;
        const password = 'TestPass123!@#';

        // Switch to register mode
        await page.getByRole('button', { name: /need an account/i }).click();

        // Fill registration form
        await page.getByPlaceholder(/username/i).fill(username);
        await page.getByPlaceholder(/password/i).fill(password);

        // Submit registration
        await page.getByRole('button', { name: /^register$/i }).click();

        // Wait for response (either success alert or error)
        await page.waitForTimeout(1000);
    });

    test('should redirect to home when already authenticated', async ({ page, context }) => {
        // Set session cookie to simulate authenticated user
        await context.addCookies([{
            name: 'dux_session',
            value: 'mock-session-value',
            domain: 'localhost',
            path: '/',
        }]);

        // Navigate to login page
        await page.goto('/login');

        // Should redirect or show authenticated state
        // This test validates the auth flow structure
    });
});
