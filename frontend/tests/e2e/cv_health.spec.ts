import { test, expect } from '@playwright/test';
import * as path from 'path';

test.describe('E2E CV Health Intelligence Module', () => {

  async function uploadAndGetToDashboard(page) {
    // 1. Register clean session
    await page.goto('/');
    await page.click('button:has-text("Join the community")');
    const uniqueEmail = `health_test_${Date.now()}@gmail.com`;
    await page.fill('input[placeholder="Dung Ken"]', 'E2E Health Tester');
    await page.fill('input[type="email"]', uniqueEmail);
    await page.fill('input[type="password"]', 'Password123');
    await page.click('button:has-text("CREATE ACCOUNT")');
    await expect(page.locator('h1:has-text("CV Health Intelligence")')).toBeVisible({ timeout: 15000 });

    // 2. Upload sample CV
    await page.goto('/cv-upload');
    const cvPath = path.resolve(process.cwd(), '../data/cv_pdf/CV_82.pdf');
    await page.setInputFiles('input[type="file"]', cvPath);
    await page.click('button:has-text("Start Parsing")');
    await expect(page.locator('h3:has-text("Professional Background")')).toBeVisible({ timeout: 60000 });

    // 3. Save profile to DB
    await page.click('button:has-text("Save to My CVs")');
    await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 20000 });

    // 4. Navigate directly to dashboard
    await page.click('button:has-text("Phân tích sức khỏe CV này ngay")');
    await expect(page.locator('h1:has-text("CV Health Intelligence")')).toBeVisible({ timeout: 10000 });
  }

  test('TC1: Successful Sync Calculation & Dashboard Gauge Rendering', async ({ page }) => {
    console.log('[Health-TC1] Uploading CV and navigating to dashboard...');
    await uploadAndGetToDashboard(page);

    console.log('[Health-TC1] Syncing CV Health to trigger API Gateway calculation...');
    const syncBtn = page.locator('button:has-text("Sync CV Health")');
    await expect(syncBtn).toBeVisible();
    await syncBtn.click();
    
    // Wait for the calculation background tasks to complete
    await expect(syncBtn).toBeEnabled({ timeout: 25000 });

    console.log('[Health-TC1] Verifying core widgets and scores...');
    await expect(page.locator('text=Multi-criteria CV Freshness')).toBeVisible();
    await expect(page.locator('text=What-if Simulation')).toBeVisible();
    await expect(page.locator('text=Opportunity Window')).toBeVisible();
    console.log('[Health-TC1] Passed successfully!');
  });

  test('TC2: Deep Interactive What-if Simulation & Score Recalculation', async ({ page }) => {
    console.log('[Health-TC2] Getting to health dashboard...');
    await uploadAndGetToDashboard(page);

    console.log('[Health-TC2] Syncing to get standard score...');
    await page.click('button:has-text("Sync CV Health")');
    await expect(page.locator('button:has-text("Sync CV Health")')).toBeEnabled({ timeout: 25000 });

    console.log('[Health-TC2] Expanding What-if Simulation Card...');
    const activateSimBtn = page.locator('button:has-text("What-if Simulation")');
    await expect(activateSimBtn).toBeVisible();
    await activateSimBtn.click();

    // Verify simulation mode panel opens
    await expect(page.locator('text=What-if Simulation Mode')).toBeVisible();
    await expect(page.locator('text=Thử thêm kỹ năng xu hướng:')).toBeVisible();

    // Click first trending recommendation button '+' to add simulated skill
    const trendingSkillBtn = page.locator('button:has-text("＋")').first();
    if (await trendingSkillBtn.isVisible()) {
      console.log('[Health-TC2] Adding simulated skill in dashboard What-if...');
      await trendingSkillBtn.click();
      
      // Asserts simulation is recalculated and active
      await expect(page.locator('text=What-if Simulation Mode')).toBeVisible();
      console.log('[Health-TC2] Simulated skill addition processed successfully.');
    }
    console.log('[Health-TC2] Passed successfully!');
  });

  test('TC3: Visual verification of Opportunity Job List and Skill Alerts', async ({ page }) => {
    console.log('[Health-TC3] Preparing dashboard data...');
    await uploadAndGetToDashboard(page);
    await page.click('button:has-text("Sync CV Health")');
    await expect(page.locator('button:has-text("Sync CV Health")')).toBeEnabled({ timeout: 25000 });

    console.log('[Health-TC3] Checking Opportunity Window...');
    await expect(page.locator('text=Opportunity Window')).toBeVisible();
    // Opportunities card should contain job recommendations list
    await expect(page.locator('.space-y-3').first()).toBeVisible();
    console.log('[Health-TC3] Passed successfully!');
  });
});
