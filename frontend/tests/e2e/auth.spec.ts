import { test, expect } from '@playwright/test';

test.describe('E2E Authentication & Security Module', () => {

  test('TC1: Successful Registration and Auto-Login redirect', async ({ page }) => {
    console.log('[Auth-TC1] Navigating to landing page...');
    await page.goto('/');
    await expect(page.locator('h2')).toContainText('Welcome back.');

    console.log('[Auth-TC1] Switching to register view...');
    await page.click('button:has-text("Join the community")');
    await expect(page.locator('h2')).toContainText('Start here.');

    const uniqueEmail = `auth_test_${Date.now()}@gmail.com`;
    console.log('[Auth-TC1] Registering fresh user:', uniqueEmail);
    await page.fill('input[placeholder="Dung Ken"]', 'E2E Auth Tester');
    await page.fill('input[type="email"]', uniqueEmail);
    await page.fill('input[type="password"]', 'Password123');
    await page.click('button:has-text("CREATE ACCOUNT")');

    // Should redirect to dashboard immediately
    await expect(page.locator('h1:has-text("CV Health Intelligence")')).toBeVisible({ timeout: 15000 });
    console.log('[Auth-TC1] Passed successfully!');
  });

  test('TC2: Rejection of short password (minLength validation)', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("Join the community")');

    console.log('[Auth-TC2] Inputting short password...');
    await page.fill('input[placeholder="Dung Ken"]', 'Short Password User');
    await page.fill('input[type="email"]', `short_pwd_${Date.now()}@test.com`);
    await page.fill('input[type="password"]', '1234'); // 4 characters (min=8)

    const createBtn = page.locator('button:has-text("CREATE ACCOUNT")');
    await createBtn.click();

    // Verify registration was blocked (we are still on the register view)
    await expect(page.locator('h2')).toContainText('Start here.');
    console.log('[Auth-TC2] Passed successfully!');
  });

  test('TC3: Rejection of invalid email format', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("Join the community")');

    console.log('[Auth-TC3] Inputting malformed email...');
    await page.fill('input[placeholder="Dung Ken"]', 'Invalid Email User');
    await page.fill('input[type="email"]', 'not_a_valid_email');
    await page.fill('input[type="password"]', 'Password123');

    const createBtn = page.locator('button:has-text("CREATE ACCOUNT")');
    await createBtn.click();

    // Still blocked on sign up view due to HTML5 email validator
    await expect(page.locator('h2')).toContainText('Start here.');
    console.log('[Auth-TC3] Passed successfully!');
  });

  test('TC4: Login with incorrect credentials fails gracefully', async ({ page }) => {
    console.log('[Auth-TC4] Trying to log in with wrong password...');
    await page.goto('/');
    await page.fill('input[type="email"]', 'auth_test_user@gmail.com');
    await page.fill('input[type="password"]', 'totally_wrong_password');
    await page.click('button:has-text("SIGN IN")');

    // verify we remain on login view
    await expect(page.locator('h2')).toContainText('Welcome back.');
    console.log('[Auth-TC4] Passed successfully!');
  });

  test('TC5: Successful Sign Out destroys session state', async ({ page }) => {
    console.log('[Auth-TC5] Creating user session...');
    await page.goto('/');
    await page.click('button:has-text("Join the community")');
    await page.fill('input[placeholder="Dung Ken"]', 'Sign Out Tester');
    await page.fill('input[type="email"]', `sign_out_${Date.now()}@gmail.com`);
    await page.fill('input[type="password"]', 'Password123');
    await page.click('button:has-text("CREATE ACCOUNT")');
    await expect(page.locator('h1:has-text("CV Health Intelligence")')).toBeVisible({ timeout: 15000 });

    console.log('[Auth-TC5] Triggering sign out...');
    // Click the TopNav avatar button (contains user name span)
    await page.locator('header button:has(span.font-semibold)').click();

    // Dropdown panel appears — wait for Đăng xuất button with generous timeout
    await page.locator('button:has-text("Đăng xuất")').waitFor({ state: 'visible', timeout: 8000 });
    await page.locator('button:has-text("Đăng xuất")').click();

    // Redirected back to landing page — either 'Welcome back.' or 'Start here.'
    await expect(page.locator('h2')).toBeVisible();
    const h2Text = await page.locator('h2').textContent();
    expect(['Welcome back.', 'Start here.']).toContain(h2Text?.trim());
    console.log('[Auth-TC5] Passed successfully! Landing page h2:', h2Text);
  });
});
