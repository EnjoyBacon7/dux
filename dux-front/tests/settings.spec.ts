import { test, expect } from '@playwright/test';
import { registerUser, loginAsTestUser } from './helpers/auth';

test.describe('Settings Page', () => {
    const testUsername = `testuser_${Date.now()}`;
    const testPassword = 'Xk9#mP2$qL7@wR5!';

    test.beforeAll(async ({ request }) => {
        // Register a test user for settings tests
        await registerUser(request, testUsername, testPassword);
    });

    test.beforeEach(async ({ page }) => {
        // Login via UI to establish proper session
        await loginAsTestUser(page, testUsername, testPassword);

        // Navigate to settings page
        await page.goto('/settings');
        
        // Wait for page to be fully loaded
        await expect(page.getByRole('heading', { name: /preferences/i })).toBeVisible();
    });

    test('should display settings page with preferences card', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /preferences/i })).toBeVisible();
        await expect(page.getByText(/language/i)).toBeVisible();
        await expect(page.getByText(/theme/i)).toBeVisible();
    });

    test('should display Latin language option', async ({ page }) => {
        const laButton = page.getByRole('button', { name: 'LA' });
        await expect(laButton).toBeVisible();
    });

    test('should switch to Latin language', async ({ page }) => {
        const laButton = page.getByRole('button', { name: 'LA' });
        await laButton.click();

        // Check if Latin translations are applied
        await expect(page.getByText(/praeferentiae/i)).toBeVisible();
    });

    test('should display debug card', async ({ page }) => {
        // Debug card should be visible
        await expect(page.getByRole('heading', { name: /debug information/i })).toBeVisible();

        // Should have a refresh button
        await expect(page.getByRole('button', { name: /refresh/i })).toBeVisible();

        // Should have show/hide details button
        const detailsButton = page.locator('button', { hasText: /show details|hide details/i }).first();
        await expect(detailsButton).toBeVisible();
    });

    test('should expand and show debug information', async ({ page }) => {
        // Click to show details
        const showButton = page.locator('button', { hasText: /show details/i }).first();
        await showButton.click();

        // Should display user information table
        await expect(page.getByText(/user information/i)).toBeVisible();
        await expect(page.getByText(/session information/i)).toBeVisible();
    });

    test('should refresh debug information', async ({ page }) => {
        const refreshButton = page.getByRole('button', { name: /refresh/i });
        await refreshButton.click();

        // Wait for refresh to complete (button should not be disabled after)
        await expect(refreshButton).not.toBeDisabled();
    });

    test('should display danger zone for delete account', async ({ page }) => {
        await expect(page.getByText(/danger zone/i)).toBeVisible();
        await expect(page.getByText(/once you delete your account/i)).toBeVisible();
        await expect(page.getByRole('button', { name: /delete account/i })).toBeVisible();
    });

    test('should show delete confirmation modal', async ({ page }) => {
        const deleteButton = page.getByRole('button', { name: /delete account/i }).first();
        await deleteButton.click();

        // Modal should appear
        await expect(page.getByText(/are you sure/i)).toBeVisible();
        await expect(page.getByText(/this will permanently delete/i)).toBeVisible();
        await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /delete permanently/i })).toBeVisible();
    });

    test('should cancel delete account', async ({ page }) => {
        const deleteButton = page.getByRole('button', { name: /delete account/i }).first();
        await deleteButton.click();

        // Click cancel
        const cancelButton = page.getByRole('button', { name: /cancel/i });
        await cancelButton.click();

        // Modal should be closed, settings page still visible
        await expect(page.getByRole('heading', { name: /preferences/i })).toBeVisible();
    });

    test('should delete account button have danger styling', async ({ page }) => {
        // Wait for danger zone to be visible
        await expect(page.getByText(/danger zone/i)).toBeVisible();
        
        const deleteButton = page.getByRole('button', { name: /delete account/i }).first();
        await expect(deleteButton).toBeVisible();

        // Check if button has danger class
        await expect(deleteButton).toHaveClass(/nb-btn--danger/);
    });
});

test.describe('Settings Page - Delete Account Flow', () => {
    test('should successfully delete account and redirect to login', async ({ page, request }) => {
        // Create a unique user for this test
        const deleteTestUsername = `deletetest_${Date.now()}`;
        const deleteTestPassword = 'Xk9#mP2$qL7@wR5!';

        // Register user
        const registerResult = await registerUser(request, deleteTestUsername, deleteTestPassword);
        expect(registerResult.success).toBeTruthy();

        // Login via UI
        await loginAsTestUser(page, deleteTestUsername, deleteTestPassword);

        // Navigate to settings
        await page.goto('/settings');

        // Click delete account
        const deleteButton = page.getByRole('button', { name: /delete account/i }).first();
        await deleteButton.click();

        // Confirm deletion
        const confirmButton = page.getByRole('button', { name: /delete permanently/i });
        await confirmButton.click();

        // Should redirect to login page
        await page.waitForURL('/login', { timeout: 10000 });
        await expect(page).toHaveURL('/login');

        // Try to login with deleted account - should fail
        await page.getByPlaceholder(/username/i).fill(deleteTestUsername);
        await page.getByPlaceholder(/password/i).fill(deleteTestPassword);
        await page.getByRole('button', { name: /^login$/i }).click();

        // Should show error (user no longer exists)
        await expect(page.getByText(/invalid|not found|error/i)).toBeVisible({ timeout: 5000 });
    });
});

test.describe('Settings Page - Debug API', () => {
    const apiTestUsername = `apitest_${Date.now()}`;
    const apiTestPassword = 'Xk9#mP2$qL7@wR5!';

    test.beforeAll(async ({ request }) => {
        // Register a test user
        await registerUser(request, apiTestUsername, apiTestPassword);
    });

    test('should fetch debug information from API', async ({ request }) => {
        // Login first
        const loginResponse = await request.post('/auth/login', {
            data: {
                username: apiTestUsername,
                password: apiTestPassword
            }
        });
        expect(loginResponse.ok()).toBeTruthy();

        // Fetch debug info
        const debugResponse = await request.get('/auth/debug/user-info');
        expect(debugResponse.ok()).toBeTruthy();

        const debugData = await debugResponse.json();

        // Verify structure
        expect(debugData).toHaveProperty('user_info');
        expect(debugData).toHaveProperty('passkey_credentials');
        expect(debugData).toHaveProperty('recent_login_attempts');
        expect(debugData).toHaveProperty('session_info');

        // Verify user info contains expected fields
        expect(debugData.user_info).toHaveProperty('id');
        expect(debugData.user_info).toHaveProperty('username');
        expect(debugData.user_info.username).toBe(apiTestUsername);
        expect(debugData.user_info).toHaveProperty('has_password');
        expect(debugData.user_info.has_password).toBe(true);
    });

    test('should require authentication for debug endpoint', async ({ request }) => {
        // Try to access debug endpoint without authentication
        const response = await request.get('/auth/debug/user-info');
        expect(response.status()).toBe(401);
    });
});

test.describe('Settings Page - Delete Account API', () => {
    test('should delete account via API', async ({ request }) => {
        // Create unique user for deletion
        const deleteApiUsername = `deleteapi_${Date.now()}`;
        const deleteApiPassword = 'Xk9#mP2$qL7@wR5!';

        // Register
        const registerResult = await registerUser(request, deleteApiUsername, deleteApiPassword);
        expect(registerResult.success).toBeTruthy();

        // Login
        const loginResponse = await request.post('/auth/login', {
            data: {
                username: deleteApiUsername,
                password: deleteApiPassword
            }
        });
        expect(loginResponse.ok()).toBeTruthy();

        // Delete account
        const deleteResponse = await request.delete('/auth/account');
        expect(deleteResponse.ok()).toBeTruthy();

        const deleteData = await deleteResponse.json();
        expect(deleteData.success).toBe(true);
        expect(deleteData.message).toContain('deleted');

        // Verify account is deleted - try to login again
        const retryLogin = await request.post('/auth/login', {
            data: {
                username: deleteApiUsername,
                password: deleteApiPassword
            }
        });
        expect(retryLogin.ok()).toBeFalsy();
    });

    test('should require authentication for delete account endpoint', async ({ request }) => {
        // Try to delete without authentication
        const response = await request.delete('/auth/account');
        expect(response.status()).toBe(401);
    });

    test('should clear session after account deletion', async ({ request }) => {
        // Create unique user
        const sessionTestUsername = `sessiontest_${Date.now()}`;
        const sessionTestPassword = 'Xk9#mP2$qL7@wR5!';

        // Register and login
        await registerUser(request, sessionTestUsername, sessionTestPassword);
        await request.post('/auth/login', {
            data: {
                username: sessionTestUsername,
                password: sessionTestPassword
            }
        });

        // Verify authenticated
        const meResponse = await request.get('/auth/me');
        expect(meResponse.ok()).toBeTruthy();

        // Delete account
        await request.delete('/auth/account');

        // Try to access authenticated endpoint - should fail
        const meAfterDelete = await request.get('/auth/me');
        expect(meAfterDelete.status()).toBe(401);
    });
});
