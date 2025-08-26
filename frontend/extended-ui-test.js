import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runExtendedUITest() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  
  const screenshotsDir = path.join(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir);
  }

  const testResults = {
    timestamp: new Date().toISOString(),
    pages: [],
    navigationTests: [],
    interactionTests: [],
    errors: []
  };

  try {
    console.log('🔍 Running Extended UI Navigation Tests...\n');

    const page = await context.newPage();
    await page.setViewportSize({ width: 1280, height: 720 });

    // Test all navigation links
    const navigationLinks = [
      { name: 'Home', path: '/', expected: true },
      { name: 'Dashboard', path: '/dashboard', expected: true },
      { name: 'Portfolio', path: '/portfolio', expected: true },
      { name: 'Goals', path: '/goals', expected: true },
      { name: 'AI Chat', path: '/chat', expected: true },
      { name: 'Analytics', path: '/analytics', expected: true }
    ];

    for (const link of navigationLinks) {
      try {
        console.log(`📄 Testing ${link.name} page (${link.path})...`);
        
        await page.goto(`http://localhost:5173${link.path}`);
        await page.waitForLoadState('networkidle');
        
        // Wait a bit for any animations or dynamic content
        await page.waitForTimeout(1000);
        
        // Check if page loaded successfully
        const title = await page.title();
        const url = page.url();
        
        // Capture screenshot
        const screenshotPath = path.join(screenshotsDir, `${link.name.toLowerCase().replace(' ', '-')}-page.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        
        // Check for key elements on each page
        const elementCounts = {
          buttons: await page.locator('button').count(),
          inputs: await page.locator('input').count(),
          forms: await page.locator('form').count(),
          headings: await page.locator('h1, h2, h3, h4, h5, h6').count(),
          links: await page.locator('a').count(),
          canvases: await page.locator('canvas').count(),
          svgs: await page.locator('svg').count()
        };
        
        // Check for error messages
        const errorElements = await page.locator('[class*="error"], .error, [data-error]').count();
        
        testResults.pages.push({
          name: link.name,
          path: link.path,
          url: url,
          title: title,
          elements: elementCounts,
          errors: errorElements,
          screenshot: `${link.name.toLowerCase().replace(' ', '-')}-page.png`,
          loaded: true
        });
        
        console.log(`   ✅ ${link.name}: ${elementCounts.buttons} buttons, ${elementCounts.inputs} inputs, ${elementCounts.headings} headings`);
        
      } catch (error) {
        console.log(`   ❌ ${link.name}: Failed to load - ${error.message}`);
        testResults.pages.push({
          name: link.name,
          path: link.path,
          error: error.message,
          loaded: false
        });
      }
    }

    // Test navigation functionality
    console.log('\n🔗 Testing Navigation Functionality...');
    
    await page.goto('http://localhost:5173/');
    await page.waitForLoadState('networkidle');
    
    // Try to click navigation items
    const navItems = ['Dashboard', 'Portfolio', 'Goals', 'AI Chat', 'Analytics'];
    
    for (const navItem of navItems) {
      try {
        // Look for navigation links containing the text
        const navLink = page.locator(`nav a:has-text("${navItem}"), a:has-text("${navItem}")`).first();
        
        if (await navLink.count() > 0) {
          await navLink.click();
          await page.waitForLoadState('networkidle');
          await page.waitForTimeout(500);
          
          const currentUrl = page.url();
          testResults.navigationTests.push({
            item: navItem,
            success: true,
            url: currentUrl
          });
          
          console.log(`   ✅ ${navItem} navigation works - ${currentUrl}`);
        } else {
          console.log(`   ⚠️  ${navItem} navigation link not found`);
          testResults.navigationTests.push({
            item: navItem,
            success: false,
            reason: 'Link not found'
          });
        }
      } catch (error) {
        console.log(`   ❌ ${navItem} navigation failed - ${error.message}`);
        testResults.navigationTests.push({
          item: navItem,
          success: false,
          error: error.message
        });
      }
    }

    // Test interactive elements
    console.log('\n⚡ Testing Interactive Elements...');
    
    await page.goto('http://localhost:5173/');
    await page.waitForLoadState('networkidle');
    
    // Test buttons
    const buttons = await page.locator('button').count();
    console.log(`   Found ${buttons} buttons on main page`);
    
    // Try to interact with primary CTA buttons
    const ctaSelectors = [
      'button:has-text("Get Started")',
      'button:has-text("View Demo")',
      'button:has-text("Sign In")'
    ];
    
    for (const selector of ctaSelectors) {
      try {
        const button = page.locator(selector).first();
        if (await button.count() > 0) {
          const buttonText = await button.textContent();
          const isVisible = await button.isVisible();
          const isEnabled = await button.isEnabled();
          
          testResults.interactionTests.push({
            element: 'button',
            text: buttonText,
            visible: isVisible,
            enabled: isEnabled,
            selector: selector
          });
          
          console.log(`   ✅ Button "${buttonText}": visible=${isVisible}, enabled=${isEnabled}`);
        }
      } catch (error) {
        testResults.interactionTests.push({
          element: 'button',
          selector: selector,
          error: error.message
        });
      }
    }

    console.log('\n✅ Extended UI Testing Complete!');
    
  } catch (error) {
    console.error('❌ Extended test execution failed:', error.message);
    testResults.errors.push(error.message);
  }

  // Save extended test results
  const reportPath = path.join(__dirname, 'extended-ui-test-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(testResults, null, 2));

  await browser.close();
  return testResults;
}

// Run the extended test
runExtendedUITest().then(results => {
  console.log('\n📊 Extended Test Results Summary:');
  console.log('==========================================');
  console.log(`Pages Tested: ${results.pages.length}`);
  console.log(`Successful Navigations: ${results.navigationTests.filter(t => t.success).length}`);
  console.log(`Interactive Elements: ${results.interactionTests.length}`);
  console.log(`Total Errors: ${results.errors.length}`);
  console.log('==========================================\n');
  
  // Show page-by-page summary
  results.pages.forEach(page => {
    if (page.loaded) {
      console.log(`📄 ${page.name}: ✅ Loaded (${page.elements?.buttons || 0} buttons, ${page.elements?.headings || 0} headings)`);
    } else {
      console.log(`📄 ${page.name}: ❌ Failed to load`);
    }
  });
  
}).catch(console.error);