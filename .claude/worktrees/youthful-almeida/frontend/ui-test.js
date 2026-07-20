import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runUITest() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  
  // Create screenshots directory
  const screenshotsDir = path.join(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir);
  }

  // Test results object
  const testResults = {
    timestamp: new Date().toISOString(),
    url: 'http://localhost:5173',
    tests: [],
    errors: [],
    screenshots: []
  };

  try {
    console.log('🚀 Starting Visual UI Testing for Financial Planning Application...\n');

    // Desktop Testing (1280x720)
    console.log('📱 Testing Desktop Viewport (1280x720)...');
    const desktopPage = await context.newPage();
    await desktopPage.setViewportSize({ width: 1280, height: 720 });
    
    await desktopPage.goto('http://localhost:5173');
    await desktopPage.waitForLoadState('networkidle');
    
    // Capture console errors
    const desktopConsoleErrors = [];
    desktopPage.on('console', msg => {
      if (msg.type() === 'error') {
        desktopConsoleErrors.push(msg.text());
      }
    });

    // Take desktop screenshot
    const desktopScreenshot = path.join(screenshotsDir, 'desktop-main.png');
    await desktopPage.screenshot({ path: desktopScreenshot, fullPage: true });
    testResults.screenshots.push('desktop-main.png');

    // Check for key UI elements
    const elementsToCheck = [
      'header', '[data-testid="header"]', 'h1', 'h2',
      'form', 'input', 'button', 'select',
      'canvas', 'svg', '.chart', '[class*="chart"]',
      'nav', '.navigation', '[class*="nav"]'
    ];

    const foundElements = {};
    for (const selector of elementsToCheck) {
      try {
        const element = await desktopPage.locator(selector).first();
        const count = await desktopPage.locator(selector).count();
        foundElements[selector] = count;
      } catch (e) {
        foundElements[selector] = 0;
      }
    }

    testResults.tests.push({
      viewport: 'desktop',
      elementsFound: foundElements,
      consoleErrors: desktopConsoleErrors,
      screenshot: 'desktop-main.png'
    });

    // Test form interactions if forms exist
    const formCount = await desktopPage.locator('form').count();
    if (formCount > 0) {
      console.log(`   ✅ Found ${formCount} form(s) - Testing interactions...`);
      
      // Test first form
      const firstForm = desktopPage.locator('form').first();
      const inputs = await firstForm.locator('input').count();
      const buttons = await firstForm.locator('button').count();
      
      // Take form screenshot
      const formScreenshot = path.join(screenshotsDir, 'desktop-form-interaction.png');
      await desktopPage.screenshot({ path: formScreenshot, fullPage: true });
      testResults.screenshots.push('desktop-form-interaction.png');
      
      console.log(`   📝 Form has ${inputs} inputs and ${buttons} buttons`);
    }

    // Tablet Testing
    console.log('\n📱 Testing Tablet Viewport (768x1024)...');
    const tabletPage = await context.newPage();
    await tabletPage.setViewportSize({ width: 768, height: 1024 });
    
    await tabletPage.goto('http://localhost:5173');
    await tabletPage.waitForLoadState('networkidle');
    
    const tabletScreenshot = path.join(screenshotsDir, 'tablet-main.png');
    await tabletPage.screenshot({ path: tabletScreenshot, fullPage: true });
    testResults.screenshots.push('tablet-main.png');

    // Mobile Testing
    console.log('\n📱 Testing Mobile Viewport (375x667)...');
    const mobilePage = await context.newPage();
    await mobilePage.setViewportSize({ width: 375, height: 667 });
    
    await mobilePage.goto('http://localhost:5173');
    await mobilePage.waitForLoadState('networkidle');
    
    const mobileScreenshot = path.join(screenshotsDir, 'mobile-main.png');
    await mobilePage.screenshot({ path: mobileScreenshot, fullPage: true });
    testResults.screenshots.push('mobile-main.png');

    // Performance and accessibility checks
    console.log('\n⚡ Running Performance Analysis...');
    const performanceMetrics = await desktopPage.evaluate(() => {
      const perfData = performance.getEntriesByType('navigation')[0];
      return {
        loadTime: perfData ? perfData.loadEventEnd - perfData.loadEventStart : null,
        domContentLoaded: perfData ? perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart : null,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || null,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || null
      };
    });

    testResults.performance = performanceMetrics;

    // Check for accessibility issues
    console.log('\n♿ Running Basic Accessibility Checks...');
    const accessibilityIssues = await desktopPage.evaluate(() => {
      const issues = [];
      
      // Check for missing alt attributes on images
      const images = document.querySelectorAll('img');
      images.forEach((img, index) => {
        if (!img.alt && !img.getAttribute('aria-label')) {
          issues.push(`Image ${index + 1} missing alt text`);
        }
      });
      
      // Check for missing labels on form inputs
      const inputs = document.querySelectorAll('input, select, textarea');
      inputs.forEach((input, index) => {
        const hasLabel = input.labels && input.labels.length > 0;
        const hasAriaLabel = input.getAttribute('aria-label');
        const hasAriaLabelledBy = input.getAttribute('aria-labelledby');
        
        if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
          issues.push(`Form input ${index + 1} missing label`);
        }
      });
      
      // Check for heading structure
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      if (headings.length === 0) {
        issues.push('No heading elements found');
      }
      
      return issues;
    });

    testResults.accessibilityIssues = accessibilityIssues;

    console.log('\n✅ Visual UI Testing Complete!');
    console.log(`📸 Screenshots saved: ${testResults.screenshots.length}`);
    console.log(`🐛 Console errors found: ${desktopConsoleErrors.length}`);
    console.log(`♿ Accessibility issues: ${accessibilityIssues.length}`);

  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
    testResults.errors.push(error.message);
  }

  // Save test results
  const reportPath = path.join(__dirname, 'visual-ui-test-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(testResults, null, 2));

  await browser.close();
  return testResults;
}

// Run the test
runUITest().then(results => {
  console.log('\n📊 Test Results Summary:');
  console.log('==========================================');
  console.log(`Total Screenshots: ${results.screenshots.length}`);
  console.log(`Total Errors: ${results.errors.length}`);
  if (results.performance) {
    console.log(`Load Time: ${results.performance.loadTime}ms`);
    console.log(`First Paint: ${results.performance.firstPaint}ms`);
  }
  console.log('==========================================\n');
}).catch(console.error);