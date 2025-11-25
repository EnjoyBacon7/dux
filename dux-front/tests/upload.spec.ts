import { test, expect } from '@playwright/test';

test.describe('Upload Page', () => {
    test('should redirect to login when not authenticated', async ({ page }) => {
        await page.goto('/upload');

        // Should be redirected to login
        await page.waitForURL('/login');
        await expect(page.locator('h1')).toContainText('Authentication');
    });

    // This test would require authentication, skipping for now
    test.skip('should display upload form when authenticated', async ({ page }) => {
        // TODO: Implement authentication helper
        await page.goto('/upload');

        await expect(page.getByRole('heading', { name: /upload/i })).toBeVisible();
        await expect(page.locator('input[type="file"]')).toBeVisible();
        await expect(page.getByRole('button', { name: /upload/i })).toBeVisible();
    });
});
