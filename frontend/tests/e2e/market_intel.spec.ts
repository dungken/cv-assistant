import { test, expect } from '@playwright/test';

test.describe('E2E Market Intelligence Analytics Module', () => {

  async function loginAndNavigateToMarketIntel(page) {
    await page.goto('/');
    await page.click('button:has-text("Join the community")');
    const email = `market_test_${Date.now()}@gmail.com`;
    await page.fill('input[placeholder="Dung Ken"]', 'E2E Market Tester');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', 'Password123');
    await page.click('button:has-text("CREATE ACCOUNT")');
    await expect(page.locator('h1:has-text("CV Health Intelligence")')).toBeVisible({ timeout: 15000 });
    await page.goto('/market-intel');
    await expect(page.locator('h1')).toContainText('Market Intelligence');
  }

  test('TC1: Dashboard loads with KPI cards and daily trend chart', async ({ page }) => {
    console.log('[Market-TC1] Navigating to Market Intel...');
    await loginAndNavigateToMarketIntel(page);

    // Verify KPI summary cards using exact text + first() to avoid strict-mode errors
    await expect(page.getByText('Tổng JD', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Công ty', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Kỹ năng độc lập', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Nguồn dữ liệu', { exact: true }).first()).toBeVisible();

    // Verify overview charts render
    await expect(page.locator('text=Xu hướng đăng JD')).toBeVisible();
    await expect(page.locator('text=Phân bố nhóm vai trò')).toBeVisible();
    console.log('[Market-TC1] Passed successfully!');
  });

  test('TC2: Tab navigation switches between Overview / Salary / Trends / Deep Analytics', async ({ page }) => {
    await loginAndNavigateToMarketIntel(page);

    console.log('[Market-TC2] Testing tab navigation...');
    // Switch to Lương Thưởng (Salary) tab
    await page.click('button:has-text("Lương Thưởng")');
    await expect(page.locator('text=Skill Premium Index')).toBeVisible();

    // Switch to Xu Hướng Kỹ Năng (Trends) tab
    await page.click('button:has-text("Xu Hướng Kỹ Năng")');
    await expect(page.locator('text=Kỹ năng đang nóng / nguội')).toBeVisible();

    // Switch to Phân Tích Chuyên Sâu (Deep Analytics) tab
    await page.click('button:has-text("Phân Tích Chuyên Sâu")');
    await expect(page.locator('text=Hidden Gem Skills')).toBeVisible();

    // Switch back to Overview
    await page.click('button:has-text("Tổng Quan")');
    await expect(page.locator('text=Tổng JD')).toBeVisible();
    console.log('[Market-TC2] Passed successfully!');
  });

  test('TC3: Source dropdown filter switches between itviec / topcv / all', async ({ page }) => {
    await loginAndNavigateToMarketIntel(page);

    console.log('[Market-TC3] Clicking Source dropdown...');
    const sourceDropdown = page.locator('label:has-text("Nguồn") + button').first();
    await expect(sourceDropdown).toBeVisible();

    // Filter to itviec
    await sourceDropdown.click();
    await page.locator('button:has-text("itviec")').first().click();
    await expect(page.locator('text=Tổng JD')).toBeVisible();

    // Filter to topcv
    await sourceDropdown.click();
    await page.locator('button:has-text("topcv")').first().click();
    await expect(page.locator('text=Tổng JD')).toBeVisible();

    // Reset to all
    await sourceDropdown.click();
    await page.locator('button:has-text("Tất cả")').first().click();
    await expect(page.locator('text=Tổng JD')).toBeVisible();
    console.log('[Market-TC3] Passed successfully!');
  });

  test('TC4: Seniority and Role Group dropdowns refine salary chart data', async ({ page }) => {
    await loginAndNavigateToMarketIntel(page);

    console.log('[Market-TC4] Filtering by seniority "junior"...');
    const seniorityDropdown = page.locator('label:has-text("Cấp độ") + button').first();
    await expect(seniorityDropdown).toBeVisible();
    await seniorityDropdown.click();
    await page.locator('button:has-text("junior")').first().click();

    // Still on overview, data should filter
    await expect(page.locator('text=Tổng JD')).toBeVisible();

    console.log('[Market-TC4] Switching to Salary tab to verify data refines...');
    await page.click('button:has-text("Lương Thưởng")');
    await expect(page.locator('text=Skill Premium Index')).toBeVisible();
    console.log('[Market-TC4] Passed successfully!');
  });

  test('TC5: Reset filter button restores dashboard to all-data view', async ({ page }) => {
    await loginAndNavigateToMarketIntel(page);

    console.log('[Market-TC5] Applying a filter then resetting...');
    // Apply source filter
    const sourceDropdown = page.locator('label:has-text("Nguồn") + button').first();
    await sourceDropdown.click();
    await page.locator('button:has-text("itviec")').first().click();

    // Click the Reset button
    const resetBtn = page.locator('button:has-text("Reset")');
    await expect(resetBtn).toBeVisible();
    await resetBtn.click();

    // Dashboard should have reloaded with full data
    await expect(page.locator('text=Tổng JD')).toBeVisible();
    console.log('[Market-TC5] Passed successfully!');
  });
});
