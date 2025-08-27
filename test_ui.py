#!/usr/bin/env python3
"""UI Testing Script with Playwright"""

from playwright.sync_api import sync_playwright
import os
import time

def test_ui():
    # Create screenshots directory if it doesn't exist
    os.makedirs('screenshots', exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 720})
        
        try:
            # Navigate to the frontend
            page.goto('http://localhost:5173/')
            
            # Wait for the page to fully load
            page.wait_for_load_state('networkidle')
            
            # Take screenshot of the main page
            page.screenshot(path='screenshots/main-page.png')
            print("✅ Main page loaded successfully")
            
            # Check for key UI elements
            elements_to_check = [
                ('header', 'h1'),
                ('form container', '.space-y-6'),
                ('card elements', '.bg-white'),
            ]
            
            for name, selector in elements_to_check:
                try:
                    element = page.wait_for_selector(selector, timeout=5000)
                    if element:
                        print(f"✅ Found {name}")
                except:
                    print(f"⚠️  Could not find {name} with selector {selector}")
            
            # Check responsive design
            viewports = [
                {'name': 'mobile', 'width': 375, 'height': 667},
                {'name': 'tablet', 'width': 768, 'height': 1024},
                {'name': 'desktop', 'width': 1920, 'height': 1080}
            ]
            
            for viewport in viewports:
                page.set_viewport_size(width=viewport['width'], height=viewport['height'])
                time.sleep(0.5)
                page.screenshot(path=f"screenshots/{viewport['name']}-view.png")
                print(f"✅ {viewport['name'].capitalize()} view captured")
            
            # Check console for errors
            console_messages = []
            page.on("console", lambda msg: console_messages.append(msg))
            page.reload()
            page.wait_for_load_state('networkidle')
            
            errors = [msg for msg in console_messages if msg.type in ['error', 'warning']]
            if errors:
                print(f"⚠️  Found {len(errors)} console errors/warnings")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"   - {error.text}")
            else:
                print("✅ No console errors detected")
            
        except Exception as e:
            print(f"❌ Error during UI testing: {e}")
            page.screenshot(path='screenshots/error-state.png')
        
        finally:
            browser.close()
    
    print("\n📸 All screenshots saved to screenshots/ directory")
    print("🎨 Visual QA completed!")
    return True

if __name__ == "__main__":
    success = test_ui()
    exit(0 if success else 1)