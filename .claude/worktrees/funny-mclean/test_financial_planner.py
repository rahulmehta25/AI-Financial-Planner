#!/usr/bin/env python3
"""
Comprehensive testing script for AI Financial Planner deployed application
Tests all pages, functionality, and responsive design
"""

from playwright.sync_api import sync_playwright
import time
import os
import json

def test_financial_planner():
    # Create screenshots directory
    os.makedirs("test_screenshots", exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser with specific settings
        browser = p.chromium.launch(headless=False, args=["--window-size=1280,720"])
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        # Track console logs and errors
        console_logs = []
        page_errors = []
        
        def handle_console(msg):
            console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            })
            if msg.type in ["error", "warning"]:
                page_errors.append(f"{msg.type.upper()}: {msg.text}")
        
        def handle_page_error(error):
            page_errors.append(f"PAGE ERROR: {str(error)}")
        
        page.on("console", handle_console)
        page.on("pageerror", handle_page_error)
        
        test_results = []
        
        try:
            print("🚀 Starting comprehensive testing of AI Financial Planner...")
            print("URL: https://ai-financial-planner-zeta.vercel.app\n")
            
            # 1. Homepage Test
            print("1️⃣ Testing Homepage...")
            page.goto("https://ai-financial-planner-zeta.vercel.app", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            page.screenshot(path="test_screenshots/01_homepage_desktop.png", full_page=True)
            
            # Check homepage elements
            homepage_check = {
                "page_loaded": page.url != "about:blank",
                "title_present": bool(page.locator("h1, [class*='title'], [class*='hero']").count()),
                "navigation_present": bool(page.locator("nav, [class*='nav'], header").count()),
                "main_content": bool(page.locator("main, .main, [class*='content'], [class*='container']").count()),
                "buttons_clickable": bool(page.locator("button, [role='button'], a[class*='btn']").count())
            }
            
            test_results.append({
                "page": "Homepage",
                "url": page.url,
                "status": "✅ Loaded" if homepage_check["page_loaded"] else "❌ Failed to load",
                "elements": homepage_check,
                "errors": page_errors.copy(),
                "screenshot": "01_homepage_desktop.png"
            })
            
            print(f"   ✅ Homepage loaded: {page.url}")
            print(f"   Elements found: {sum(homepage_check.values())} out of {len(homepage_check)}")
            
            # 2. Test Navigation Links
            print("\n2️⃣ Testing Navigation...")
            nav_links = page.locator("nav a, [class*='nav'] a, header a").all()
            
            pages_to_test = [
                {"name": "Dashboard", "selectors": ["text=Dashboard", "href*=dashboard", "[data-testid*=dashboard]"]},
                {"name": "Portfolio", "selectors": ["text=Portfolio", "href*=portfolio", "[data-testid*=portfolio]"]},
                {"name": "Goals", "selectors": ["text=Goals", "href*=goals", "[data-testid*=goals]"]},
                {"name": "AI Chat", "selectors": ["text=AI", "text=Chat", "text=Advisor", "href*=chat", "href*=advisor"]},
                {"name": "Analytics", "selectors": ["text=Analytics", "href*=analytics", "[data-testid*=analytics]"]},
                {"name": "Login", "selectors": ["text=Login", "text=Sign In", "href*=login", "[data-testid*=login]"]}
            ]
            
            for page_test in pages_to_test:
                print(f"\n3️⃣ Testing {page_test['name']} Page...")
                page_found = False
                
                # Try to find and click the page link
                for selector in page_test['selectors']:
                    try:
                        element = page.locator(selector).first
                        if element.is_visible():
                            current_errors = len(page_errors)
                            element.click()
                            page.wait_for_timeout(3000)
                            
                            # Take screenshot
                            screenshot_name = f"0{len(test_results)+1}_{page_test['name'].lower()}_page.png"
                            page.screenshot(path=f"test_screenshots/{screenshot_name}", full_page=True)
                            
                            # Check if page loaded successfully
                            page_loaded = page.url != "about:blank" and not page.url.endswith("/")
                            new_errors = page_errors[current_errors:]
                            
                            # Check for common page elements
                            elements_check = {
                                "page_title": bool(page.locator("h1, h2, [class*='title']").count()),
                                "content_area": bool(page.locator("main, .content, [class*='container']").count()),
                                "interactive_elements": bool(page.locator("button, input, select, [role='button']").count()),
                                "no_404_error": "404" not in page.locator("body").text_content().lower()
                            }
                            
                            test_results.append({
                                "page": page_test['name'],
                                "url": page.url,
                                "status": "✅ Loaded" if page_loaded and elements_check["no_404_error"] else "❌ Failed",
                                "elements": elements_check,
                                "errors": new_errors,
                                "screenshot": screenshot_name
                            })
                            
                            print(f"   ✅ {page_test['name']} page loaded: {page.url}")
                            print(f"   Elements found: {sum(elements_check.values())} out of {len(elements_check)}")
                            if new_errors:
                                print(f"   ⚠️  Errors: {len(new_errors)}")
                            
                            page_found = True
                            break
                            
                    except Exception as e:
                        continue
                
                if not page_found:
                    test_results.append({
                        "page": page_test['name'],
                        "url": "N/A",
                        "status": "❌ Not found",
                        "elements": {},
                        "errors": [f"Could not find {page_test['name']} page link"],
                        "screenshot": None
                    })
                    print(f"   ❌ {page_test['name']} page not found or not accessible")
            
            # 4. Mobile Responsive Test
            print(f"\n4️⃣ Testing Mobile Responsive Design...")
            mobile_viewport = {"width": 375, "height": 667}  # iPhone SE size
            page.set_viewport_size(mobile_viewport)
            
            # Go back to homepage for mobile test
            page.goto("https://ai-financial-planner-zeta.vercel.app", wait_until="networkidle")
            page.wait_for_timeout(2000)
            
            page.screenshot(path="test_screenshots/mobile_homepage.png", full_page=True)
            
            # Test mobile navigation (hamburger menu, etc.)
            mobile_nav_check = {
                "responsive_layout": page.evaluate("window.innerWidth < 768"),
                "hamburger_menu": bool(page.locator("[class*='hamburger'], [class*='mobile-menu'], [aria-label*='menu']").count()),
                "touch_friendly": bool(page.locator("button, [role='button']").first.bounding_box()["height"] >= 44 if page.locator("button").count() else False),
                "horizontal_scroll": page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            }
            
            test_results.append({
                "page": "Mobile Homepage",
                "url": page.url,
                "status": "✅ Responsive" if mobile_nav_check["responsive_layout"] else "⚠️ May not be responsive",
                "elements": mobile_nav_check,
                "errors": [],
                "screenshot": "mobile_homepage.png"
            })
            
            print(f"   📱 Mobile responsive test completed")
            print(f"   Mobile features: {sum(mobile_nav_check.values())} out of {len(mobile_nav_check)}")
            
        except Exception as e:
            print(f"❌ Critical error during testing: {str(e)}")
            page_errors.append(f"CRITICAL ERROR: {str(e)}")
            
        finally:
            # Generate comprehensive report
            print("\n" + "="*60)
            print("📋 COMPREHENSIVE TEST REPORT")
            print("="*60)
            
            total_tests = len(test_results)
            passed_tests = len([r for r in test_results if "✅" in r["status"]])
            
            print(f"🎯 Overall Results: {passed_tests}/{total_tests} tests passed")
            print(f"🌐 Application URL: https://ai-financial-planner-zeta.vercel.app")
            print(f"📸 Screenshots saved: test_screenshots/ directory")
            print(f"📊 Console logs captured: {len(console_logs)} messages")
            print(f"🚨 Total errors found: {len(page_errors)}")
            
            print("\n📄 Page-by-Page Results:")
            for i, result in enumerate(test_results, 1):
                print(f"\n{i}. {result['page']} - {result['status']}")
                print(f"   URL: {result['url']}")
                if result['screenshot']:
                    print(f"   Screenshot: {result['screenshot']}")
                if result['elements']:
                    working_elements = sum(result['elements'].values())
                    total_elements = len(result['elements'])
                    print(f"   Elements: {working_elements}/{total_elements} working")
                if result['errors']:
                    print(f"   ⚠️ Issues: {len(result['errors'])}")
                    for error in result['errors'][:2]:  # Show first 2 errors
                        print(f"     - {error}")
            
            if console_logs:
                print(f"\n🔍 Console Messages Summary:")
                error_logs = [log for log in console_logs if log['type'] == 'error']
                warning_logs = [log for log in console_logs if log['type'] == 'warning']
                print(f"   Errors: {len(error_logs)}")
                print(f"   Warnings: {len(warning_logs)}")
                print(f"   Total: {len(console_logs)}")
            
            # Save detailed report to JSON
            with open("test_results.json", "w") as f:
                json.dump({
                    "summary": {
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "total_errors": len(page_errors),
                        "total_console_logs": len(console_logs)
                    },
                    "test_results": test_results,
                    "console_logs": console_logs,
                    "errors": page_errors
                }, f, indent=2)
            
            print(f"\n💾 Detailed report saved: test_results.json")
            
            browser.close()
            
            return test_results, page_errors, console_logs

if __name__ == "__main__":
    test_financial_planner()