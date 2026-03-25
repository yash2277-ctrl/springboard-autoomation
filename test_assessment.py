"""
Test script to capture the actual quiz DOM from Springboard.
Navigates to a quiz module, waits for content to load (including iframes),
and dumps ALL frame content to quiz_dom.html for analysis.
"""
from playwright.sync_api import sync_playwright
import time

def test_assessment():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Logging in...")
        page.goto("https://infyspringboard.onwingspan.com/web/en/login")
        time.sleep(2)
        
        # Click LOGIN on landing page
        try:
            page.locator(".login-btn, button:has-text('LOGIN'), button:has-text('Login'), a:has-text('LOGIN')").first.click(timeout=5000)
            time.sleep(2)
        except Exception as e:
            print(f"Could not click LOGIN: {e}")
        
        # Fill credentials
        try:
            page.locator("#username").fill("sahu446688@gmail.com")
            page.locator("#password").fill("Yash112233@")
            page.locator("#kc-login").click()
        except Exception as e:
            print(f"Login form error: {e}")
            
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        print("Going to course...")
        page.goto("https://infyspringboard.onwingspan.com/web/en/app/toc/lex_auth_0127667384693882883448_shared/overview")
        time.sleep(5)
        
        # Open TOC
        print("Opening TOC...")
        try:
            page.locator('mat-icon:has-text("menu_book")').nth(0).click(timeout=3000)
            time.sleep(2)
        except:
            pass
            
        # Click the assessment/quiz module
        print("Clicking Quiz...")
        quiz_names = ["Hash Table - Quiz", "Quiz", "Assessment", "Test"]
        for qname in quiz_names:
            try:
                el = page.locator(f'text="{qname}"').first
                if el.is_visible(timeout=2000):
                    el.click()
                    print(f"Clicked: {qname}")
                    break
            except:
                continue

        # Wait for quiz to fully load (including iframes)
        time.sleep(8)
        
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except:
            pass
        
        # Wait MORE for iframe content
        time.sleep(5)
        
        print(f"\n=== DOM EXPLORATION ===")
        print(f"Total frames: {len(page.frames)}")
        
        for i, frame in enumerate(page.frames):
            try:
                url = frame.url[:80] if frame.url else "about:blank"
                # Count quiz-relevant elements
                info = frame.evaluate("""() => {
                    return {
                        radios: document.querySelectorAll('mat-radio-button, input[type="radio"], [role="radio"]').length,
                        checkboxes: document.querySelectorAll('mat-checkbox, input[type="checkbox"]').length,
                        radioGroups: document.querySelectorAll('mat-radio-group, fieldset, [role="radiogroup"]').length,
                        buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(t => t).slice(0, 15),
                        headings: Array.from(document.querySelectorAll('h1,h2,h3,h4')).map(h => h.innerText.trim()).slice(0, 10),
                        bodyLen: document.body ? document.body.innerHTML.length : 0,
                    };
                }""")
                print(f"\n  Frame #{i}: {url}")
                print(f"    Body size: {info['bodyLen']} chars")
                print(f"    Radios: {info['radios']}, Groups: {info['radioGroups']}, Checkboxes: {info['checkboxes']}")
                print(f"    Buttons: {info['buttons']}")
                print(f"    Headings: {info['headings']}")
            except Exception as e:
                print(f"  Frame #{i}: ERROR - {e}")
        
        print("\n=== SAVING DOM ===")
        try:
            htmls = []
            htmls.append(f"<!-- MAIN PAGE: {page.url} -->\n")
            htmls.append(page.content())
            
            for i, frame in enumerate(page.frames):
                try:
                    htmls.append(f"\n\n<!-- FRAME #{i}: {frame.url} -->\n\n")
                    htmls.append(frame.content())
                except:
                    htmls.append(f"\n\n<!-- FRAME #{i}: COULD NOT GET CONTENT -->\n\n")
                    
            with open("quiz_dom.html", "w", encoding="utf-8") as f:
                f.write("\n".join(htmls))
            print("Saved DOM to quiz_dom.html")
        except Exception as e:
            print(f"Error dumping: {e}")
        
        print("\n=== INTERACTIVE MODE ===")
        print("Browser is open. Inspect the quiz manually.")
        print("Press ENTER to close...")
        input()
        
        browser.close()

if __name__ == "__main__":
    test_assessment()
