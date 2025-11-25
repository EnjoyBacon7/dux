import { Page, APIRequestContext } from '@playwright/test';

/**
 * Helper functions for authentication in tests
 */

/**
 * Retry wrapper with exponential backoff
 */
async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    initialDelay: number = 1000
): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error as Error;
            if (attempt < maxRetries - 1) {
                const delay = initialDelay * Math.pow(2, attempt);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    throw lastError;
}

export async function registerUser(
    request: APIRequestContext,
    username: string,
    password: string
): Promise<{ success: boolean; error?: string }> {
    try {
        const response = await retryWithBackoff(async () => {
            return await request.post('/auth/register', {
                data: { username, password },
                timeout: 30000,
            });
        });

        if (response.ok()) {
            return { success: true };
        } else {
            const data = await response.json();
            return { success: false, error: data.detail };
        }
    } catch (error) {
        return { success: false, error: String(error) };
    }
}

export async function loginUser(
    request: APIRequestContext,
    username: string,
    password: string
): Promise<{ success: boolean; error?: string }> {
    try {
        const response = await retryWithBackoff(async () => {
            return await request.post('/auth/login', {
                data: { username, password },
                timeout: 30000,
            });
        });

        if (response.ok()) {
            return { success: true };
        } else {
            const data = await response.json();
            return { success: false, error: data.detail };
        }
    } catch (error) {
        return { success: false, error: String(error) };
    }
}

export async function loginAsTestUser(
    page: Page,
    username?: string,
    password?: string
): Promise<void> {
    const testUsername = username || `testuser_${Date.now()}`;
    const testPassword = password || 'StrongT3st!P@ssword';

    await page.goto('/login');
    await page.getByPlaceholder(/username/i).fill(testUsername);
    await page.getByPlaceholder(/password/i).fill(testPassword);
    await page.getByRole('button', { name: /^login$/i }).click();

    // Wait for navigation or error
    await page.waitForTimeout(1000);
}

export async function logout(page: Page): Promise<void> {
    const logoutButton = page.getByTitle(/logout/i);
    if (await logoutButton.isVisible()) {
        await logoutButton.click();
        await page.waitForURL('/login');
    }
}

export function generateTestCredentials(): { username: string; password: string } {
    // Generate password using timestamp + random to avoid sequential patterns
    const timestamp = Date.now().toString();
    const random1 = Math.random().toString(36).substring(2, 6);
    const random2 = Math.random().toString(36).substring(2, 5);

    return {
        username: `test_${Date.now()}_${Math.random().toString(36).substring(7)}`,
        password: `Secure${random1.toUpperCase()}${timestamp.substring(timestamp.length - 3)}${random2}!@Pass`,
    };
}
