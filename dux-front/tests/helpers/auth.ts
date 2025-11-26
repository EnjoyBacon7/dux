import { Page, APIRequestContext } from '@playwright/test';

/**
 * Authentication helper functions for E2E tests
 */

const API_TIMEOUT = 30000;
const DEFAULT_PASSWORD = 'StrongT3st!P@ssword';

interface AuthResult {
    success: boolean;
    error?: string;
}

/**
 * Register a new user via API
 */
export async function registerUser(
    request: APIRequestContext,
    username: string,
    password: string
): Promise<AuthResult> {
    try {
        const response = await request.post('/auth/register', {
            data: { username, password },
            timeout: API_TIMEOUT,
        });

        if (response.ok()) {
            return { success: true };
        }

        const data = await response.json();
        return { success: false, error: data.detail };
    } catch (error) {
        return { success: false, error: String(error) };
    }
}

/**
 * Login a user via API
 */
export async function loginUser(
    request: APIRequestContext,
    username: string,
    password: string
): Promise<AuthResult> {
    try {
        const response = await request.post('/auth/login', {
            data: { username, password },
            timeout: API_TIMEOUT,
        });

        if (response.ok()) {
            return { success: true };
        }

        const data = await response.json();
        return { success: false, error: data.detail };
    } catch (error) {
        return { success: false, error: String(error) };
    }
}

/**
 * Login through the UI
 */
export async function loginAsTestUser(
    page: Page,
    username?: string,
    password?: string
): Promise<void> {
    const testUsername = username || `testuser_${Date.now()}`;
    const testPassword = password || DEFAULT_PASSWORD;

    await page.goto('/login');
    await page.getByPlaceholder(/username/i).fill(testUsername);
    await page.getByPlaceholder(/password/i).fill(testPassword);
    await page.getByRole('button', { name: /^login$/i }).click();
    await page.waitForTimeout(1000);
}

/**
 * Logout through the UI
 */
export async function logout(page: Page): Promise<void> {
    const logoutButton = page.getByTitle(/logout/i);
    if (await logoutButton.isVisible()) {
        await logoutButton.click();
        await page.waitForURL('/login');
    }
}

/**
 * Generate unique test credentials with secure password
 * Password avoids sequential patterns that validator rejects
 */
export function generateTestCredentials(): { username: string; password: string } {
    const timestamp = Date.now().toString();
    const random1 = Math.random().toString(36).substring(2, 6);
    const random2 = Math.random().toString(36).substring(2, 5);
    const timestampPart = timestamp.substring(timestamp.length - 3);

    return {
        username: `test_${timestamp}_${Math.random().toString(36).substring(7)}`,
        password: `Secure${random1.toUpperCase()}${timestampPart}${random2}!@Pass`,
    };
}
