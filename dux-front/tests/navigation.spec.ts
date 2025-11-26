import { test, expect } from '@playwright/test';
import { loginAsTestUser, registerUser } from './helpers/auth';

test.describe('Navigation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
    });

    test('should display header on all pages', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /dux/i })).toBeVisible();
    });

    test('should have correct page title', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle(/dux/i);
    });
});

test.describe('Navigation - Settings Language and Theme', () => {
    const testUsername = `navtest_${Date.now()}`;
    const testPassword = 'Xk9#mP2$qL7@wR5!';

    test.beforeAll(async ({ request }) => {
        await registerUser(request, testUsername, testPassword);
    });

    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page, testUsername, testPassword);
        await page.goto('/settings');
    });

    test('should have language selector', async ({ page }) => {
        const languageButtons = page.locator('.nb-theme-selector button');
        await expect(languageButtons.first()).toBeVisible();
    });

    test('should have theme selector', async ({ page }) => {
        const themeButtons = page.locator('.nb-theme-selector').last().locator('button');
        await expect(themeButtons.first()).toBeVisible();
    });

    test('should toggle theme', async ({ page }) => {
        const html = page.locator('html');
        const lightButton = page.getByTitle(/light mode/i);

        if (await lightButton.isVisible()) {
            await lightButton.click();
            await expect(html).toHaveAttribute('data-theme', 'light');
        }
    });

    test('should change language', async ({ page }) => {
        const enButton = page.locator('button[title="EN"]').first();
        const esButton = page.locator('button[title="ES"]').first();

        if (await enButton.isVisible()) {
            await enButton.click();
            await expect(page.getByRole('heading', { name: /preferences/i })).toBeVisible();
        }

        if (await esButton.isVisible()) {
            await esButton.click();
            await expect(page.getByRole('heading', { name: /preferencias/i })).toBeVisible();
        }
    });

    test('should support Latin language', async ({ page }) => {
        const laButton = page.getByRole('button', { name: 'LA' });

        if (await laButton.isVisible()) {
            await laButton.click();
            // Check for Latin translation of "Preferences"
            await expect(page.getByRole('heading', { name: /praeferentiae/i })).toBeVisible();
        }
    });
});

