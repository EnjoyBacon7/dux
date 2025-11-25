import { test, expect } from '@playwright/test';
import { generateTestCredentials, registerUser, loginUser } from './helpers/auth';

test.describe('Complete Auth Flow', () => {
    test('should complete full registration and login flow', async ({ request }) => {
        const { username, password } = generateTestCredentials();

        // Register new user
        const registerResult = await registerUser(request, username, password);
        expect(registerResult.success).toBeTruthy();

        // Login with new credentials
        const loginResult = await loginUser(request, username, password);
        expect(loginResult.success).toBeTruthy();
    });

    test('should prevent duplicate registration', async ({ request }) => {
        const { username, password } = generateTestCredentials();

        // Register once
        await registerUser(request, username, password);

        // Try to register again
        const secondRegister = await registerUser(request, username, password);
        expect(secondRegister.success).toBeFalsy();
        expect(secondRegister.error).toContain('already exists');
    });

    test('should enforce password requirements', async ({ request }) => {
        const username = `user_${Date.now()}`;

        // Test weak password
        const weakPassword = await registerUser(request, username, 'weak');
        expect(weakPassword.success).toBeFalsy();

        // Test short password
        const shortPassword = await registerUser(request, username, 'Short1!');
        expect(shortPassword.success).toBeFalsy();
    });

    test('should enforce username requirements', async ({ request }) => {
        const password = 'ValidPass123!@#';

        // Test short username
        const shortUsername = await registerUser(request, 'ab', password);
        expect(shortUsername.success).toBeFalsy();

        // Test invalid characters
        const invalidUsername = await registerUser(request, 'user@name!', password);
        expect(invalidUsername.success).toBeFalsy();
    });
});
