import { test, expect } from '@playwright/test';
import * as path from 'path';

test.describe('E2E CV Upload & AI NER Parser Module', () => {

  async function performRegistration(page) {
    await page.goto('/');
    await page.click('button:has-text("Join the community")');
    const uniqueEmail = `upload_test_${Date.now()}@gmail.com`;
    await page.fill('input[placeholder="Dung Ken"]', 'E2E Upload Tester');
    await page.fill('input[type="email"]', uniqueEmail);
    await page.fill('input[type="password"]', 'Password123');
    await page.click('button:has-text("CREATE ACCOUNT")');
    await expect(page.locator('h1:has-text("CV Health Intelligence")')).toBeVisible({ timeout: 15000 });
  }

  test('TC1: Successful PDF CV Upload, AI NER Parsing, and DB Preservation', async ({ page }) => {
    console.log('[Upload-TC1] Registering clean user...');
    await performRegistration(page);

    console.log('[Upload-TC1] Navigating to CV Upload page...');
    await page.goto('/cv-upload');
    await expect(page.locator('h1')).toContainText('Upload & Review CV');

    const cvPath = path.resolve(process.cwd(), '../data/cv_pdf/CV_82.pdf');
    console.log('[Upload-TC1] Dragging/selecting PDF file:', cvPath);
    await page.setInputFiles('input[type="file"]', cvPath);
    await expect(page.locator('text=CV_82.pdf')).toBeVisible();

    console.log('[Upload-TC1] Clicking Start Parsing...');
    await page.click('button:has-text("Start Parsing")');
    
    // Wait for the AI segment results card to render (implies parsing finished successfully)
    await expect(page.locator('h3:has-text("Professional Background")')).toBeVisible({ timeout: 60000 });

    console.log('[Upload-TC1] Saving CV structured profile to DB...');
    await page.click('button:has-text("Save to My CVs")');
    await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 20000 });
    console.log('[Upload-TC1] Passed successfully!');
  });

  test('TC2: Rejection of parsing when no CV file is selected', async ({ page }) => {
    await performRegistration(page);
    await page.goto('/cv-upload');
    await expect(page.locator('h1')).toContainText('Upload & Review CV');

    console.log('[Upload-TC2] Verifying Start Parsing not shown on empty state...');
    // When no file is selected, "Start Parsing" button is NOT rendered — only "Select PDF" is visible
    await expect(page.locator('button:has-text("Select PDF")')).toBeVisible();
    await expect(page.locator('button:has-text("Start Parsing")')).not.toBeVisible();
    console.log('[Upload-TC2] Passed successfully!');
  });

  test('TC3: Editing CV form field before saving to profile', async ({ page }) => {
    await performRegistration(page);
    await page.goto('/cv-upload');

    const cvPath = path.resolve(process.cwd(), '../data/cv_pdf/CV_82.pdf');
    await page.setInputFiles('input[type="file"]', cvPath);
    await page.click('button:has-text("Start Parsing")');
    
    // Wait for form parsing results to load
    const summaryHeader = page.locator('h3:has-text("Professional Background")');
    await expect(summaryHeader).toBeVisible({ timeout: 60000 });

    console.log('[Upload-TC3] Editing Professional Summary section...');
    // Scroll to the Professional Summary h4 header
    const summaryH4 = page.locator('h4:has-text("Professional Summary")');
    await expect(summaryH4).toBeVisible();
    await summaryH4.scrollIntoViewIfNeeded();

    // The Edit button is in the same flex header div as the h4 — use XPath-like parent traversal
    // by targeting button that is a sibling within the same 'flex items-center justify-between' div
    const editBtn = page.locator('h4:has-text("Professional Summary")').locator('..').locator('button:has-text("Edit")');
    await expect(editBtn).toBeVisible({ timeout: 5000 });
    await editBtn.click();

    // After clicking Edit, a textarea appears with autoFocus in the section below the header
    const summaryTextarea = page.locator('textarea').first();
    await expect(summaryTextarea).toBeVisible({ timeout: 5000 });
    await summaryTextarea.fill('Fully edited E2E professional summary for UTC2 graduation thesis!');

    // Save the edit
    await page.locator('button:has-text("Save")').last().click();

    console.log('[Upload-TC3] Saving to My CVs...');
    await page.click('button:has-text("Save to My CVs")');
    await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 20000 });
    console.log('[Upload-TC3] Passed successfully!');
  });
});
