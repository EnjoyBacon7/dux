import { test, expect } from '@playwright/test';

const API_TIMEOUT = 30000;
const VALID_PASSWORD = 'StrongT3st!P@ss';

test.describe('API Integration', () => {
    test('should respond to healthcheck endpoint', async ({ request }) => {
        const response = await request.get('/api/healthcheck', { timeout: API_TIMEOUT });

        expect(response.ok()).toBeTruthy();
        expect(await response.text()).toBe('"OK"');
    });

    test('should return 401 for /auth/me when not authenticated', async ({ request }) => {
        const response = await request.get('/auth/me');
        expect(response.status()).toBe(401);
    });

    test('should validate registration with invalid username', async ({ request }) => {
        const response = await request.post('/auth/register', {
            data: { username: 'ab', password: VALID_PASSWORD },
            timeout: API_TIMEOUT,
        });

        expect(response.status()).toBe(400);
        const data = await response.json();
        expect(data.detail).toContain('at least 3 characters');
    });

    test('should validate registration with weak password', async ({ request }) => {
        const response = await request.post('/auth/register', {
            data: { username: 'testuser', password: 'weak' },
            timeout: API_TIMEOUT,
        });

        expect(response.status()).toBe(400);
        const data = await response.json();
        expect(data.detail).toBeTruthy();
    });

    test('should handle login with invalid credentials', async ({ request }) => {
        const response = await request.post('/auth/login', {
            data: { username: 'nonexistent_user', password: 'WrongPassword123!' },
        });

        expect(response.status()).toBe(401);
        const data = await response.json();
        expect(data.detail).toContain('Invalid credentials');
    });
});
