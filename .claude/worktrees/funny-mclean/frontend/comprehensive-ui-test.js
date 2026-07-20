import { chromium, devices } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create screenshots directory if it doesn't exist
const screenshotsDir = path.join(__dirname, 'screenshots');
if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
}

async function runComprehensiveUITest() {
    const report = {
        timestamp: new Date().toISOString(),
        testResults: [],
        summary: {
            totalTests: 0,
            passed: 0,
            failed: 0,
            warnings: 0
        },
        screenshots: [],
        consoleErrors: [],
        networkErrors: [],
        performanceMetrics: {},
        accessibilityIssues: []
    };

    console.log('🚀 Starting Comprehensive UI Testing...');
    
    const browser = await chromium.launch({ 
        headless: false,
        args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
    });

    // Test configurations for different viewport sizes
    const testConfigs = [
        { name: 'Desktop', viewport: { width: 1920, height: 1080 } },
        { name: 'Tablet', viewport: { width: 768, height: 1024 } },
        { name: 'Mobile', viewport: { width: 375, height: 667 } }
    ];

    // Routes to test
    const routesToTest = [
        { path: '/', name: 'Home Page' },
        { path: '/dashboard', name: 'Dashboard' },
        { path: '/portfolio', name: 'Portfolio' },
        { path: '/goals', name: 'Goals' },
        { path: '/chat', name: 'AI Chat' },
        { path: '/analytics', name: 'Analytics' }
    ];

    for (const config of testConfigs) {
        console.log(`\n📱 Testing ${config.name} viewport (${config.viewport.width}x${config.viewport.height})`);
        
        const context = await browser.newContext({
            viewport: config.viewport,
            deviceScaleFactor: 1
        });

        const page = await context.newPage();

        // Capture console messages and errors
        page.on('console', (msg) => {
            if (msg.type() === 'error') {
                report.consoleErrors.push({
                    viewport: config.name,
                    message: msg.text(),
                    location: msg.location()
                });
            }
        });

        // Capture network errors
        page.on('response', (response) => {
            if (response.status() >= 400) {
                report.networkErrors.push({
                    viewport: config.name,
                    url: response.url(),
                    status: response.status(),
                    statusText: response.statusText()
                });
            }
        });

        for (const route of routesToTest) {
            try {
                console.log(`  🧪 Testing ${route.name} (${route.path})`);
                
                const testResult = {
                    viewport: config.name,
                    route: route.name,
                    path: route.path,
                    status: 'passed',
                    issues: [],
                    loadTime: 0,
                    screenshot: null
                };

                const startTime = Date.now();
                
                // Navigate to the page
                const response = await page.goto(`http://localhost:5173${route.path}`, {
                    waitUntil: 'networkidle',
                    timeout: 30000
                });

                testResult.loadTime = Date.now() - startTime;

                // Check if page loaded successfully
                if (!response || response.status() >= 400) {
                    testResult.status = 'failed';
                    testResult.issues.push(`HTTP ${response?.status() || 'No response'}`);
                }

                // Wait for page to be fully loaded
                await page.waitForLoadState('domcontentloaded');
                await page.waitForTimeout(2000); // Wait for dynamic content

                // Take screenshot
                const screenshotPath = `${config.name.toLowerCase()}-${route.name.toLowerCase().replace(/\s+/g, '-')}.png`;
                await page.screenshot({ 
                    path: path.join(screenshotsDir, screenshotPath),
                    fullPage: true 
                });
                testResult.screenshot = screenshotPath;
                report.screenshots.push(screenshotPath);

                // Test 1: Check page title
                const title = await page.title();
                if (!title || title === '') {
                    testResult.issues.push('Missing or empty page title');
                }

                // Test 2: Check for main navigation
                const navigation = await page.locator('[data-testid="navigation"], nav, header').count();
                if (navigation === 0) {
                    testResult.issues.push('Navigation not found');
                }

                // Test 3: Check for main content area
                const mainContent = await page.locator('main, [role="main"], .main-content').count();
                if (mainContent === 0) {
                    testResult.issues.push('Main content area not found');
                }

                // Test 4: Check for responsive layout
                if (config.name === 'Mobile') {
                    // Check if mobile menu exists or navigation is responsive
                    const mobileMenu = await page.locator('[aria-label*="menu"], .mobile-menu, .hamburger').count();
                    const navItems = await page.locator('nav a, nav button').count();
                    
                    if (navItems > 5 && mobileMenu === 0) {
                        testResult.issues.push('Mobile navigation may not be responsive');
                    }
                }

                // Test 5: Check for accessibility attributes
                const elementsWithoutAlt = await page.locator('img:not([alt])').count();
                if (elementsWithoutAlt > 0) {
                    testResult.issues.push(`${elementsWithoutAlt} images without alt attributes`);
                }

                const buttonsWithoutLabel = await page.locator('button:not([aria-label]):not([title])').filter({ hasText: /^\s*$/ }).count();
                if (buttonsWithoutLabel > 0) {
                    testResult.issues.push(`${buttonsWithoutLabel} buttons without accessible labels`);
                }

                // Test 6: Check for form validation (if forms exist)
                const forms = await page.locator('form').count();
                if (forms > 0) {
                    const requiredFields = await page.locator('input[required], select[required], textarea[required]').count();
                    const fieldLabels = await page.locator('label, [for]').count();
                    
                    if (requiredFields > fieldLabels) {
                        testResult.issues.push('Some required form fields may be missing labels');
                    }
                }

                // Test 7: Interactive elements test
                if (route.path === '/') {
                    // Test main CTA buttons
                    const ctaButtons = await page.locator('button, a[href]').count();
                    if (ctaButtons === 0) {
                        testResult.issues.push('No interactive elements found on homepage');
                    }
                }

                // Test 8: Check for loading states
                const loadingElements = await page.locator('[data-testid*="loading"], .loading, .spinner').count();
                // This is informational - loading states are good to have

                // Test 9: Performance metrics
                if (config.name === 'Desktop' && route.path === '/') {
                    const performanceEntries = await page.evaluate(() => {
                        const entries = performance.getEntriesByType('navigation')[0];
                        return {
                            domContentLoaded: entries?.domContentLoadedEventEnd - entries?.fetchStart || 0,
                            loadComplete: entries?.loadEventEnd - entries?.fetchStart || 0
                        };
                    });
                    report.performanceMetrics[route.name] = performanceEntries;
                }

                // Test 10: Check for error boundaries or error states
                const errorElements = await page.locator('[data-testid*="error"], .error, .alert-error').count();
                if (errorElements > 0) {
                    const errorText = await page.locator('[data-testid*="error"], .error, .alert-error').first().textContent();
                    testResult.issues.push(`Error state detected: ${errorText}`);
                }

                // Determine overall test status
                if (testResult.issues.length === 0) {
                    testResult.status = 'passed';
                    report.summary.passed++;
                } else if (testResult.issues.some(issue => 
                    issue.includes('HTTP') || 
                    issue.includes('not found') || 
                    issue.includes('Error state detected')
                )) {
                    testResult.status = 'failed';
                    report.summary.failed++;
                } else {
                    testResult.status = 'warning';
                    report.summary.warnings++;
                }

                report.summary.totalTests++;
                report.testResults.push(testResult);

                console.log(`    ✅ ${testResult.status.toUpperCase()}: ${testResult.issues.length} issues found`);
                
            } catch (error) {
                console.error(`    ❌ FAILED: ${error.message}`);
                report.summary.totalTests++;
                report.summary.failed++;
                report.testResults.push({
                    viewport: config.name,
                    route: route.name,
                    path: route.path,
                    status: 'failed',
                    issues: [error.message],
                    loadTime: 0,
                    screenshot: null
                });
            }
        }

        await context.close();
    }

    await browser.close();

    // Generate detailed report
    console.log('\n📊 Generating Test Report...');
    
    const reportPath = path.join(__dirname, 'comprehensive-ui-test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    // Generate summary
    console.log('\n🎯 TEST SUMMARY');
    console.log('================');
    console.log(`Total Tests: ${report.summary.totalTests}`);
    console.log(`✅ Passed: ${report.summary.passed}`);
    console.log(`⚠️  Warnings: ${report.summary.warnings}`);
    console.log(`❌ Failed: ${report.summary.failed}`);
    console.log(`🖼️  Screenshots: ${report.screenshots.length}`);
    console.log(`💬 Console Errors: ${report.consoleErrors.length}`);
    console.log(`🌐 Network Errors: ${report.networkErrors.length}`);
    
    console.log('\n📋 DETAILED FINDINGS');
    console.log('====================');

    // Group results by status
    const failedTests = report.testResults.filter(t => t.status === 'failed');
    const warningTests = report.testResults.filter(t => t.status === 'warning');
    
    if (failedTests.length > 0) {
        console.log('\n❌ FAILED TESTS:');
        failedTests.forEach(test => {
            console.log(`  • ${test.viewport} - ${test.route}: ${test.issues.join(', ')}`);
        });
    }

    if (warningTests.length > 0) {
        console.log('\n⚠️  WARNING TESTS:');
        warningTests.forEach(test => {
            console.log(`  • ${test.viewport} - ${test.route}: ${test.issues.join(', ')}`);
        });
    }

    if (report.consoleErrors.length > 0) {
        console.log('\n💬 CONSOLE ERRORS:');
        report.consoleErrors.forEach(error => {
            console.log(`  • ${error.viewport}: ${error.message}`);
        });
    }

    if (report.networkErrors.length > 0) {
        console.log('\n🌐 NETWORK ERRORS:');
        report.networkErrors.forEach(error => {
            console.log(`  • ${error.viewport}: ${error.url} (${error.status})`);
        });
    }

    console.log('\n📈 PERFORMANCE METRICS:');
    Object.entries(report.performanceMetrics).forEach(([page, metrics]) => {
        console.log(`  • ${page}:`);
        console.log(`    - DOM Content Loaded: ${metrics.domContentLoaded}ms`);
        console.log(`    - Load Complete: ${metrics.loadComplete}ms`);
    });

    console.log(`\n📁 Report saved to: ${reportPath}`);
    console.log(`📸 Screenshots saved to: ${screenshotsDir}`);
    
    return report;
}

// Run the test
runComprehensiveUITest().catch(console.error);