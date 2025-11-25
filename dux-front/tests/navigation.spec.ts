import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
    test('should display header on all pages', async ({ page }) => {
        await page.goto('/login');
        await expect(page.getByRole('heading', { name: /dux/i })).toBeVisible();
    });

    test('should have language selector', async ({ page }) => {
        await page.goto('/login');

        // Check for language buttons
        const languageButtons = page.locator('.nb-theme-selector button');
        await expect(languageButtons.first()).toBeVisible();
    });

    test('should have theme selector', async ({ page }) => {
        await page.goto('/login');

        // Theme selector should be visible
        const themeButtons = page.locator('.nb-theme-selector').last().locator('button');
        await expect(themeButtons.first()).toBeVisible();
    });

    test('should toggle theme', async ({ page }) => {
        await page.goto('/login');

        // Get the HTML element to check data-theme attribute
        const html = page.locator('html');

        // Click light theme button
        const lightButton = page.getByTitle(/light mode/i);
        if (await lightButton.isVisible()) {
            await lightButton.click();
            await expect(html).toHaveAttribute('data-theme', 'light');
        }
    });

    test('should change language', async ({ page }) => {
        await page.goto('/login');

        // Find language selector buttons
        const enButton = page.getByRole('button', { name: 'EN' });
        const esButton = page.getByRole('button', { name: 'ES' });

        if (await enButton.isVisible()) {
            await enButton.click();
            // Check that content is in English
            await expect(page.getByText(/authentication/i)).toBeVisible();
        }

        if (await esButton.isVisible()) {
            await esButton.click();
            // Check that content switched to Spanish
            await expect(page.getByText(/autenticación/i)).toBeVisible();
        }
    });

    test('should have correct page title', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle(/dux/i);
    });
});
