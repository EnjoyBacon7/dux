import { test, expect } from '@playwright/test';
import { generateTestCredentials, registerUser, loginUser } from './helpers/auth';

const VALID_PASSWORD = 'StrongT3st!P@ssword';

test.describe('Complete Auth Flow', () => {
    test('should complete full registration and login flow', async ({ request }) => {
        const { username, password } = generateTestCredentials();

        const registerResult = await registerUser(request, username, password);
        expect(registerResult.success).toBeTruthy();

        const loginResult = await loginUser(request, username, password);
        expect(loginResult.success).toBeTruthy();
    });

    test('should prevent duplicate registration', async ({ request }) => {
        const { username, password } = generateTestCredentials();

        await registerUser(request, username, password);

        const secondRegister = await registerUser(request, username, password);
        expect(secondRegister.success).toBeFalsy();
        expect(secondRegister.error).toContain('already exists');
    });

    test('should enforce password requirements', async ({ request }) => {
        const username = `user_${Date.now()}`;

        const weakPassword = await registerUser(request, username, 'weak');
        expect(weakPassword.success).toBeFalsy();

        const shortPassword = await registerUser(request, username, 'Short1!');
        expect(shortPassword.success).toBeFalsy();
    });

    test('should enforce username requirements', async ({ request }) => {
        const shortUsername = await registerUser(request, 'ab', VALID_PASSWORD);
        expect(shortUsername.success).toBeFalsy();

        const invalidUsername = await registerUser(request, 'user@name!', VALID_PASSWORD);
        expect(invalidUsername.success).toBeFalsy();
    });
});
