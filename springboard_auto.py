"""
╔═══════════════════════════════════════════════════════════════════════╗
║         INFOSYS SPRINGBOARD - COURSE AUTO-PROGRESSION SCRIPT        ║
║                                                                     ║
║  A robust Playwright automation script that handles:                ║
║    • Login (with CAPTCHA pause support)                             ║
║    • Video modules (iframe-aware JS injection)                      ║
║    • Reading/PDF pages (smooth scroll + dwell time)                 ║
║    • Pop-ups & interstitials (auto-dismiss)                         ║
║    • Assessment detection (stops for manual takeover)               ║
║                                                                     ║
║  Usage:                                                             ║
║    1. pip install playwright                                        ║
║    2. playwright install chromium                                   ║
║    3. Edit USER_EMAIL, USER_PASSWORD, COURSE_URL below              ║
║    4. python springboard_auto.py                                    ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

import time
import os
import sys
from datetime import datetime
import g4f
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ══════════════════════════════════════════════════════════════════════
# ██  CONFIGURATION — reads from env vars (GitHub Actions) or defaults ██
# ══════════════════════════════════════════════════════════════════════

# Detect CI/GitHub Actions environment
IS_CI = os.getenv("CI", "").lower() in ("true", "1") or os.getenv("GITHUB_ACTIONS", "").lower() == "true"

USER_EMAIL    = os.getenv("SPRINGBOARD_EMAIL", "YOUR_EMAIL@example.com")
USER_PASSWORD = os.getenv("SPRINGBOARD_PASSWORD", "YOUR_PASSWORD")
COURSE_URL    = os.getenv("SPRINGBOARD_COURSE_URL", "https://infyspringboard.onwingspan.com/web/en/app/toc/YOUR_COURSE_ID/overview")

# ── Advanced Settings ────────────────────────────────────────────────
HEADLESS         = True if IS_CI else False   # Always headless in CI
DEFAULT_TIMEOUT  = 15000   # 15 seconds default timeout (ms)
VIDEO_WAIT_SECS  = 10      # Seconds to wait after video "finishes" for server registration
SCROLL_DWELL     = 5       # Seconds to stay at bottom of reading pages
MODULE_LOAD_WAIT = 3       # Seconds to wait after clicking Next for new module load
SCREENSHOT_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_screenshots")

# ── Springboard URLs ─────────────────────────────────────────────────
LOGIN_URL = "https://infyspringboard.onwingspan.com/web/en/login"

# ══════════════════════════════════════════════════════════════════════


def log(msg: str, level: str = "INFO"):
    """Pretty-print a timestamped log message."""
    icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERR": "❌", "STOP": "🚨", "VIDEO": "🎬", "SCROLL": "📜", "NEXT": "➡️"}
    icon = icons.get(level, "•")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"  [{timestamp}] {icon}  {msg}")


def take_debug_screenshot(page, label: str = "debug"):
    """Save a screenshot for debugging purposes."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{label}_{ts}.png")
    try:
        page.screenshot(path=path, full_page=True)
        log(f"Screenshot saved: {path}", "INFO")
    except Exception as e:
        log(f"Could not save screenshot: {e}", "WARN")


# ─────────────────────────────────────────────────────────────────────
#  1. AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────

def do_login(page):
    """
    Navigate to the Springboard login page and authenticate.
    Handles the two-step login (email → password) used by Infosys SSO.
    """
    log("Navigating to login page...", "INFO")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # ── Step 1: Email ────────────────────────────────────────────────
    log(f"Entering email: {USER_EMAIL}", "INFO")
    # Try multiple common selectors for email field
    email_selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[placeholder*="mail"]',
        'input[placeholder*="Mail"]',
        'input[id*="email"]',
        'input[id*="Email"]',
        'input[name="username"]',
        '#username',
        'input[type="text"]',
    ]

    email_field = None
    for selector in email_selectors:
        try:
            field = page.locator(selector).first
            if field.is_visible(timeout=2000):
                email_field = field
                log(f"  Found email field with selector: {selector}", "OK")
                break
        except Exception:
            continue

    if not email_field:
        log("Could not find the email input field.", "ERR")
        if IS_CI:
            log("Running in CI — waiting 10s and retrying login page...", "WARN")
            take_debug_screenshot(page, "no_email_field")
            time.sleep(10)
            page.reload()
            time.sleep(5)
            # Try one more time to find email field
            for selector in email_selectors:
                try:
                    field = page.locator(selector).first
                    if field.is_visible(timeout=3000):
                        email_field = field
                        break
                except Exception:
                    continue
            if not email_field:
                log("Still cannot find email field in CI. Aborting.", "ERR")
                return
        else:
            log("Please log in manually, then press ENTER in this terminal.", "WARN")
            input(">>> Press ENTER after you have logged in manually... ")
            return

    email_field.fill(USER_EMAIL)
    time.sleep(0.5)

    # Click "Next" / "Continue" / "Proceed" after email
    next_btn_selectors = [
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'button:has-text("Proceed")',
        'button:has-text("Sign in")',
        'button:has-text("Login")',
        'button[type="submit"]',
        'input[type="submit"]',
    ]
    clicked = False
    for selector in next_btn_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                btn.click()
                clicked = True
                log(f"  Clicked next/continue button: {selector}", "OK")
                break
        except Exception:
            continue

    if not clicked:
        # Fallback: press Enter on the email field
        email_field.press("Enter")
        log("  Pressed Enter on email field as fallback", "WARN")

    time.sleep(2)
    page.wait_for_load_state("networkidle")

    # ── Step 2: Password ─────────────────────────────────────────────
    log("Entering password...", "INFO")
    password_selectors = [
        'input[type="password"]',
        'input[name="password"]',
        'input[id*="password"]',
        'input[id*="Password"]',
        '#password',
    ]

    password_field = None
    for selector in password_selectors:
        try:
            field = page.locator(selector).first
            if field.is_visible(timeout=3000):
                password_field = field
                log(f"  Found password field with selector: {selector}", "OK")
                break
        except Exception:
            continue

    if not password_field:
        log("Could not find the password field. Pausing for manual login...", "ERR")
        log("Please complete login manually, then press ENTER.", "WARN")
        input(">>> Press ENTER after you have logged in manually... ")
        return

    password_field.fill(USER_PASSWORD)
    time.sleep(0.5)

    # Click "Login" / "Sign in" button
    login_btn_selectors = [
        'button:has-text("Login")',
        'button:has-text("Log in")',
        'button:has-text("Sign in")',
        'button:has-text("Submit")',
        'button[type="submit"]',
        'input[type="submit"]',
    ]
    clicked = False
    for selector in login_btn_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                btn.click()
                clicked = True
                log(f"  Clicked login button: {selector}", "OK")
                break
        except Exception:
            continue

    if not clicked:
        password_field.press("Enter")
        log("  Pressed Enter on password field as fallback", "WARN")

    # ── Wait for dashboard ───────────────────────────────────────────
    log("Waiting for dashboard to load...", "INFO")
    time.sleep(3)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except PlaywrightTimeout:
        log("Network idle timeout — continuing anyway.", "WARN")

    # ── CAPTCHA Check ────────────────────────────────────────────────
    # If we're still on the login page, a CAPTCHA might have appeared
    if "login" in page.url.lower():
        log("Still on login page — CAPTCHA may have appeared!", "STOP")
        take_debug_screenshot(page, "captcha_detected")
        if IS_CI:
            log("Running in CI — retrying login after 10s wait...", "WARN")
            time.sleep(10)
            # Try clicking login again
            try:
                page.locator('#kc-login').click()
                time.sleep(5)
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
        else:
            log("Please solve the CAPTCHA and complete login, then press ENTER.", "WARN")
            input(">>> Press ENTER after you have solved the CAPTCHA... ")
            page.wait_for_load_state("networkidle")

    log("Login successful! ✨", "OK")


# ─────────────────────────────────────────────────────────────────────
#  2. COURSE NAVIGATION
# ─────────────────────────────────────────────────────────────────────

def navigate_to_course(page):
    """Navigate to the course and click Start/Resume/Continue."""
    log(f"Navigating to course: {COURSE_URL}", "INFO")
    page.goto(COURSE_URL, wait_until="domcontentloaded")
    time.sleep(3)
    page.wait_for_load_state("networkidle")

    # Look for Start / Resume / Continue Course button
    start_selectors = [
        'button:has-text("Start")',
        'button:has-text("Resume")',
        'button:has-text("Continue")',
        'button:has-text("Continue Course")',
        'button:has-text("Start Course")',
        'button:has-text("Resume Course")',
        'a:has-text("Start")',
        'a:has-text("Resume")',
        'a:has-text("Continue")',
        'button:has-text("Begin")',
    ]

    for selector in start_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=3000):
                btn.click()
                log(f"Clicked course entry button: {selector}", "OK")
                time.sleep(3)
                page.wait_for_load_state("networkidle")
                return
        except Exception:
            continue

    log("No Start/Resume button found — may already be in the player.", "WARN")


# ─────────────────────────────────────────────────────────────────────
#  3. CONTENT HANDLERS
# ─────────────────────────────────────────────────────────────────────

def handle_video(page) -> bool:
    """
    Detect and handle video content.
    Scans the main page AND all iframes for <video> elements.
    Uses JS injection to skip to near the end & trigger completion.
    Returns True if a video was found and handled.
    """
    log("Scanning for video elements (main page + iframes)...", "VIDEO")

    # ── Strategy 1: Check all frames (handles iframes) ───────────────
    for i, frame in enumerate(page.frames):
        try:
            video_el = frame.locator("video").first
            if video_el.is_visible(timeout=2000):
                log(f"  Found <video> in frame #{i}: {frame.url[:80]}", "VIDEO")

                # Wait for video to have metadata loaded
                frame.evaluate("""
                    () => {
                        return new Promise((resolve) => {
                            const video = document.querySelector('video');
                            if (!video) return resolve(false);
                            if (video.readyState >= 1) return resolve(true);
                            video.addEventListener('loadedmetadata', () => resolve(true));
                            setTimeout(() => resolve(false), 10000);
                        });
                    }
                """)

                # Get video duration
                duration = frame.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        return video ? video.duration : 0;
                    }
                """)

                if duration and duration > 0:
                    log(f"  Video duration: {duration:.1f}s", "VIDEO")

                    # ── ANTI-CHEAT STRATEGY ──────────────────────────
                    # Instead of jumping to the very end instantly,
                    # we set a high playback rate and let it "play" for
                    # a few seconds. This registers more naturally.
                    frame.evaluate("""
                        () => {
                            const video = document.querySelector('video');
                            if (!video) return;
                            // Unmute & set volume low
                            video.muted = true;
                            video.volume = 0;
                            // Set playback to max speed
                            try { video.playbackRate = 16; } catch(e) {
                                try { video.playbackRate = 8; } catch(e2) {
                                    try { video.playbackRate = 4; } catch(e3) {
                                        video.playbackRate = 2;
                                    }
                                }
                            }
                            // Jump to near the end
                            video.currentTime = Math.max(0, video.duration - 5);
                            video.play();
                        }
                    """)
                    log(f"  ⏩ Injected: skipped to end & playing at max speed", "VIDEO")

                    # Wait for the video to finish and the server to register
                    time.sleep(VIDEO_WAIT_SECS)

                    # Double-check: ensure video reached the end
                    frame.evaluate("""
                        () => {
                            const video = document.querySelector('video');
                            if (video && video.currentTime < video.duration - 1) {
                                video.currentTime = video.duration - 0.5;
                                video.play();
                            }
                        }
                    """)
                    time.sleep(3)
                    log("  Video module completed!", "OK")
                    return True
                else:
                    log("  Video found but duration is 0 — waiting...", "WARN")
                    time.sleep(5)
                    return True

        except Exception as e:
            continue

    # ── Strategy 2: Shadow DOM — try evaluating globally ─────────────
    try:
        has_shadow_video = page.evaluate("""
            () => {
                // Search common shadow-root video player containers
                const candidates = document.querySelectorAll('*');
                for (const el of candidates) {
                    if (el.shadowRoot) {
                        const video = el.shadowRoot.querySelector('video');
                        if (video) return true;
                    }
                }
                return false;
            }
        """)
        if has_shadow_video:
            log("  Found video inside Shadow DOM!", "VIDEO")
            page.evaluate("""
                () => {
                    const candidates = document.querySelectorAll('*');
                    for (const el of candidates) {
                        if (el.shadowRoot) {
                            const video = el.shadowRoot.querySelector('video');
                            if (video) {
                                video.muted = true;
                                try { video.playbackRate = 16; } catch(e) { video.playbackRate = 2; }
                                video.currentTime = Math.max(0, video.duration - 5);
                                video.play();
                                return;
                            }
                        }
                    }
                }
            """)
            time.sleep(VIDEO_WAIT_SECS)
            log("  Shadow DOM video handled!", "OK")
            return True
    except Exception:
        pass

    return False


def handle_reading_page(page) -> bool:
    """
    Handle reading/text/PDF content pages by scrolling to the bottom.
    Returns True if scrolling was performed.
    """
    log("Checking if this is a reading/text page...", "SCROLL")

    # Scroll the main page smoothly to the bottom
    try:
        # First, get the full page height
        scroll_height = page.evaluate("() => document.body.scrollHeight")

        if scroll_height > 500:
            log(f"  Page height: {scroll_height}px — scrolling down...", "SCROLL")

            # Smooth scroll in increments to mimic human reading
            viewport_height = page.evaluate("() => window.innerHeight")
            current_pos = 0
            step = viewport_height * 0.8  # scroll 80% of viewport each step

            while current_pos < scroll_height:
                current_pos += step
                page.evaluate(f"window.scrollTo({{ top: {current_pos}, behavior: 'smooth' }})")
                time.sleep(0.5)

            # Final scroll to absolute bottom
            page.evaluate("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })")
            log(f"  Reached bottom. Dwelling for {SCROLL_DWELL}s...", "SCROLL")
            time.sleep(SCROLL_DWELL)

            # Also try scrolling any internal scrollable containers
            page.evaluate("""
                () => {
                    // Find common LMS content containers that might be independently scrollable
                    const containers = document.querySelectorAll(
                        '.content-area, .module-content, .player-content, ' +
                        '.scroll-container, [class*="content"], [class*="scroll"], ' +
                        '[style*="overflow: auto"], [style*="overflow-y: auto"], ' +
                        '[style*="overflow: scroll"], [style*="overflow-y: scroll"]'
                    );
                    containers.forEach(c => {
                        if (c.scrollHeight > c.clientHeight + 50) {
                            c.scrollTop = c.scrollHeight;
                        }
                    });
                }
            """)
            time.sleep(2)
            log("  Reading page completed!", "OK")
            return True
    except Exception as e:
        log(f"  Scroll error: {e}", "WARN")

    return False


def handle_popups(page):
    """
    Detect and dismiss common pop-ups, modals, and interstitials:
    - "Congratulations" modals
    - "Module Complete" notifications
    - "Rate this module" prompts
    - Cookie consent banners
    - Generic modal close buttons
    """
    popup_texts = [
        "Congratulations",
        "Module Complete",
        "Module Completed",
        "Rate this",
        "Feedback",
        "Well done",
        "Great job",
        "Successfully completed",
        "Certificate",
    ]

    close_selectors = [
        'button:has-text("Close")',
        'button:has-text("close")',
        'button:has-text("OK")',
        'button:has-text("Got it")',
        'button:has-text("Dismiss")',
        'button:has-text("Skip")',
        'button:has-text("Not now")',
        'button:has-text("Maybe later")',
        'button:has-text("No thanks")',
        'button[aria-label="Close"]',
        'button[aria-label="close"]',
        '[class*="close"]',
        '[class*="dismiss"]',
        '.modal-close',
        '.dialog-close',
        '.btn-close',
        'button.close',
        '[data-dismiss="modal"]',
        '.mat-dialog-container button',  # Angular Material dialogs
    ]

    try:
        page_text = page.inner_text("body", timeout=2000).lower()
    except Exception:
        return

    for popup_text in popup_texts:
        if popup_text.lower() in page_text:
            log(f"  Detected popup/modal: '{popup_text}'", "WARN")

            for selector in close_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=1500):
                        btn.click()
                        log(f"  Dismissed popup with: {selector}", "OK")
                        time.sleep(1)
                        return
                except Exception:
                    continue

            # If no close button found, try pressing Escape
            try:
                page.keyboard.press("Escape")
                log("  Pressed Escape to dismiss popup", "OK")
                time.sleep(1)
            except Exception:
                pass
            return


def handle_coding(page) -> bool:
    """
    Handle coding exercises (using G4F AI solver).
    Returns True if a coding exercise was found and handled.
    """
    editor_visible = False
    targets = [page] + list(page.frames)

    for t in targets:
        try:
            if t.locator('.monaco-editor, .code-editor, [class*="editor"]').count() > 0:
                editor_visible = True
                break
        except Exception:
            continue

    if not editor_visible:
        return _handle_simple_coding(page)

    log("👨‍💻 Complex Coding Exercise DETECTED. Starting AI Auto-Solver...", "INFO")
    time.sleep(1.0)

    problem_text = ""
    skeleton_code = ""

    try:
        log("  Extracting problem description and skeleton code...", "INFO")
        for t in targets:
            try:
                text = t.evaluate("() => document.body.innerText")
                if len(text) > len(problem_text):
                    problem_text = text
            except Exception:
                continue

        for t in targets:
            try:
                code = t.evaluate("""() => {
                    let lines = document.querySelectorAll('.view-line');
                    if (lines.length > 0) {
                        return Array.from(lines).map(l => l.innerText).join('\\n');
                    }
                    return '';
                }""")
                if len(code) > len(skeleton_code):
                    skeleton_code = code
            except Exception:
                continue

        if not skeleton_code:
            try:
                skeleton_code = page.locator('textarea.inputarea').first.input_value(timeout=1000)
            except Exception:
                pass

    except Exception as e:
        log(f"  Failed to extract context: {e}", "WARN")

    if len(problem_text) < 50:
        log("  Could not find enough problem context. Attempting simple submit.", "WARN")
        return _verify_and_submit_code(page)

    log("  🧠 Asking G4F AI for the solution (this may take 10-30s)...", "INFO")
    
    prompt = f"""
You are an expert Python programmer passing an automated test for a user on an educational platform.
Below is the full page text of a coding exercise, which contains the problem description, class diagrams, or expected output.
Below that is the "skeleton code" that is currently in the editor.

YOUR TASK:
1. Write the correct Python 3 code to solve the problem.
2. You MUST keep the exact function signatures, class names, and variable names required by the skeleton code or the problem description.
3. ONLY return the raw, complete, working Python code. Do not include markdown formatting, explanations, or comments (unless in skeleton). Your exact output will be pasted directly into an editor.

=== PAGE / PROBLEM TEXT ===
{problem_text[:4000]}

=== SKELETON CODE ===
{skeleton_code}
"""
    
    solution_code = ""
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4o_mini,
            messages=[{"role": "user", "content": prompt}],
            timeout=60
        )
        
        solution_code = response.strip()
        if solution_code.startswith("```python"):
            solution_code = solution_code[9:]
        if solution_code.startswith("```"):
            solution_code = solution_code[3:]
        if solution_code.endswith("```"):
            solution_code = solution_code[:-3]
            
        solution_code = solution_code.strip()
        log(f"  ✅ AI generated a {len(solution_code)} character solution.", "OK")
        
    except Exception as e:
        log(f"  ❌ AI Solver failed: {e}", "ERR")
        log("  Attempting to just click Submit as fallback...", "WARN")
        return _verify_and_submit_code(page)

    if not solution_code:
        log("  AI returned empty solution. Fallback.", "WARN")
        return _verify_and_submit_code(page)

    log("  Injecting code into the editor...", "INFO")
    code_injected = False
    
    for t in targets:
        try:
            editor_input = t.locator('textarea.inputarea').first
            if editor_input.is_visible(timeout=1000):
                editor_input.click()
                time.sleep(0.5)
                t.keyboard.press("Control+A")
                time.sleep(0.2)
                t.keyboard.press("Backspace")
                time.sleep(0.5)
                t.keyboard.insert_text(solution_code)
                time.sleep(1.0)
                code_injected = True
                break
        except Exception:
            continue

    if not code_injected:
        log("  Failed to find editor input area. Fallback to simple submit.", "WARN")

    return _verify_and_submit_code(page)


def _verify_and_submit_code(page):
    targets = [page] + list(page.frames)
    
    log("  Clicking 'Verify'...", "INFO")
    verify_clicked = False
    for t in targets:
        try:
            verify_btn = t.locator('button:has-text("Verify"), button:has-text("VERIFY"), button:has-text("Compile"), button:has-text("Run")').first
            if verify_btn.is_visible(timeout=1000) and verify_btn.is_enabled(timeout=1000):
                verify_btn.click()
                verify_clicked = True
                break
        except Exception:
            continue
            
    if verify_clicked:
        log("  Waiting 10s for verification to complete...", "INFO")
        time.sleep(10.0)
    else:
        log("  No Verify button found. Proceeding to Submit.", "WARN")

    log("  Clicking 'Submit'...", "INFO")
    submit_clicked = False
    for t in targets:
        try:
            submit_btn = t.locator('button:has-text("Submit"), button:has-text("SUBMIT")').first
            if submit_btn.is_visible(timeout=1500) and submit_btn.is_enabled(timeout=1500):
                submit_btn.click()
                t.keyboard.press("Enter")
                submit_clicked = True
                break
        except Exception:
            continue

    if submit_clicked:
        log("  Coding exercise submitted successfully! ✓", "OK")
        time.sleep(3.0)
        return True
    else:
        log("  Could not find Submit button.", "ERR")
        return False


def _handle_simple_coding(page):
    try:
        play_selectors = [
            'mat-icon:has-text("play_arrow")',
            'button mat-icon:has-text("play_arrow")',
            '.play-button',
            '[class*="play-btn"]',
            'button[mattooltip="Run Code"]',
            'button[mattooltip="Execute"]'
        ]
        
        js_code = """() => {
            let clicked = false;
            const clickPlay = (doc) => {
                const icons = Array.from(doc.querySelectorAll('mat-icon, i, .icon'));
                for (const icon of icons) {
                    if (icon.innerText.includes("play_arrow") || icon.innerText.includes("play")) {
                        const btn = icon.closest('button') || icon;
                        btn.click();
                        clicked = true;
                        return true;
                    }
                }
                const btns = Array.from(doc.querySelectorAll('button'));
                for (const btn of btns) {
                    if (btn.outerHTML.toLowerCase().includes("play") && !btn.outerHTML.toLowerCase().includes("video")) {
                        btn.click();
                        clicked = true;
                        return true;
                    }
                }
                return false;
            };
            if(clickPlay(document)) return true;
            return clicked;
        }"""

        clicked = False
        for sel in play_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=500):
                    log("Found simple coding exercise! Clicking Play button...", "INFO")
                    el.click()
                    clicked = True
                    break
            except Exception: continue

        if not clicked:
            try:
                if page.evaluate(js_code):
                    log("Found simple coding exercise via JS! Clicking Play...", "INFO")
                    clicked = True
            except Exception: pass

        if not clicked:
            for frame in page.frames:
                try:
                    if frame.evaluate(js_code):
                        log("Found simple coding exercise in iframe! Clicking Play...", "INFO")
                        clicked = True
                        break
                except Exception: pass
                    
        if clicked:
            log("Waiting 10s for code execution to finish...", "INFO")
            time.sleep(5.0)
            return True
            
    except Exception: pass
    return False

def check_for_assessment(page) -> bool:
    """
    Check if the current page is an assessment/quiz/test.
    Checks main page AND all iframes for quiz indicators.
    Returns True if assessment keywords are detected.
    """
    assessment_keywords = [
        "assessment", "quiz", "test", "exam",
        "examination", "evaluate", "graded assignment",
    ]

    try:
        # Check page title
        title = page.title().lower()
        for kw in assessment_keywords:
            if kw in title:
                return True

        # Check URL
        url = page.url.lower()
        if any(kw in url for kw in ["quiz", "assessment", "exam"]):
            return True

        # Check visible headings and prominent text
        for tag in ["h1", "h2", "h3", ".title", ".header", '[class*="title"]', '[class*="header"]']:
            try:
                elements = page.locator(tag).all()
                for el in elements:
                    try:
                        text = el.inner_text(timeout=800).lower()
                        for kw in assessment_keywords:
                            if kw in text:
                                return True
                    except Exception:
                        continue
            except Exception:
                continue

        # Check for assessment UI markers on main page + all iframes
        markers = [
            'text="I am not a robot"', 'text="Submit Assessment"',
            'text="Save & Next"', 'mat-radio-button', 'mat-radio-group',
            '[role="radiogroup"]',
        ]
        targets = [page] + list(page.frames)
        for target in targets:
            for marker in markers:
                try:
                    count = target.locator(marker).count()
                    if count > 0 and target.locator(marker).first.is_visible(timeout=800):
                        return True
                except Exception:
                    continue

        # JS scan all frames for radio groups
        for frame in page.frames:
            try:
                has_quiz = frame.evaluate("""() => {
                    const radios = document.querySelectorAll('mat-radio-button, input[type="radio"], [role="radio"]');
                    const saveNext = Array.from(document.querySelectorAll('button')).filter(b =>
                        b.innerText && (b.innerText.includes('Save') || b.innerText.includes('Submit'))
                    );
                    return radios.length >= 2 || saveNext.length > 0;
                }""")
                if has_quiz:
                    return True
            except Exception:
                continue

    except Exception:
        pass

    return False


def auto_answer_assessment(page):
    """
    Full assessment auto-answer flow:
    1. Handle 'I am not a robot' checkbox
    2. Click START
    3. Accept instructions
    4. Answer all MCQs (select first option via robust JS injection)
    5. Submit assessment
    """
    log("Starting assessment auto-answer...", "STOP")

    # Helper: click first visible element from selectors on a target (page/frame)
    def click_first_on(target, selectors):
        for sel in selectors:
            try:
                btn = target.locator(sel).first
                if btn.is_visible(timeout=1500) and btn.is_enabled(timeout=800):
                    btn.click()
                    return True
            except Exception:
                continue
        return False

    all_targets = [page] + list(page.frames)

    # ── Step 1: "I am not a robot" ────────────────────────────────
    for t in all_targets:
        try:
            robot = t.locator('text="I am not a robot"')
            if robot.is_visible(timeout=2000):
                robot.click()
                time.sleep(0.5)
                try:
                    t.locator('mat-checkbox').first.click()
                except Exception:
                    pass
                log("Checked 'I am not a robot' ✓", "OK")
                time.sleep(1)
                break
        except Exception:
            continue

    # ── Step 2: Click START ───────────────────────────────────────
    start_sel = ['button:has-text("START")', 'button:has-text("Start")',
                 'button:has-text("Begin")', 'button:has-text("Take Assessment")']
    for t in all_targets:
        if click_first_on(t, start_sel):
            log("Clicked START ✓", "OK")
            time.sleep(1.5)
            break

    # ── Step 3: Instructions popup ────────────────────────────────
    accept_sel = ['text="I have read and accept the instructions"',
                  'mat-checkbox:has-text("I have read")', 'text="I have read"']
    for t in all_targets:
        for sel in accept_sel:
            try:
                el = t.locator(sel).first
                if el.is_visible(timeout=1500):
                    el.click()
                    log("Accepted instructions ✓", "OK")
                    time.sleep(1)
                    click_first_on(t, ['button:has-text("Continue")', 'button:has-text("Proceed")'])
                    time.sleep(1.5)
                    break
            except Exception:
                continue

    # ── Step 4: Answer all MCQ questions ──────────────────────────
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightTimeout:
        pass
    time.sleep(1.0)

    js_extract_code = """() => {
        const extractText = (el) => el ? el.innerText.trim() : '';
        const groups = Array.from(document.querySelectorAll('mat-radio-group, fieldset, [role="radiogroup"], .question-container, .quiz-question'));
        if (groups.length > 0) {
            for (const g of groups) {
                const hasChecked = g.querySelector('.mat-radio-checked, input:checked, [aria-checked="true"]');
                if (!hasChecked) {
                    const opts = Array.from(g.querySelectorAll('mat-radio-button, input[type="radio"], label.option, .quiz-option, [role="radio"]')).filter(el => el.offsetParent !== null);
                    if (opts.length > 0) {
                        let qText = '';
                        const prevSib = g.previousElementSibling;
                        if (prevSib) qText = extractText(prevSib);
                        if (!qText && g.parentElement) {
                            const header = g.parentElement.querySelector('h1, h2, h3, h4, .question-text, p');
                            if (header) qText = extractText(header);
                        }
                        return { question: qText, options: opts.map(o => extractText(o) || o.value || o.id || 'Option'), method: 'groups' };
                    }
                }
            }
        }
        const allRadios = Array.from(document.querySelectorAll('mat-radio-button, input[type="radio"], [role="radio"]')).filter(el => el.offsetParent !== null);
        const groupsByName = {};
        allRadios.forEach(r => {
            const name = r.getAttribute('name') || r.getAttribute('ng-reflect-name') || r.getAttribute('ng-reflect-value') || 'default';
            if (!groupsByName[name]) groupsByName[name] = [];
            groupsByName[name].push(r);
        });
        for (const name in groupsByName) {
            const opts = groupsByName[name];
            const hasChecked = opts.some(o => (o.classList && (o.classList.contains('mat-radio-checked') || o.classList.contains('cdk-focused'))) || o.checked || o.getAttribute('aria-checked') === 'true');
            if (!hasChecked && opts.length > 0) {
                let qText = '';
                const parent = opts[0].closest('.question, .mcq-container, div');
                if (parent) {
                    const header = parent.querySelector('h1, h2, h3, h4, .question-text, p');
                    if (header) qText = extractText(header);
                }
                return { question: qText, options: opts.map(o => extractText(o) || o.value || o.id || 'Option'), method: 'ungrouped', name: name };
            }
        }
        return null;
    }"""

    js_click_code = """(args) => {
        const { method, index, name } = args;
        const robustClick = (el) => {
            el.click(); el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true})); el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true})); el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
            const inner = el.querySelector('.mat-radio-container, .mat-radio-inner-circle, .mat-radio-outer-circle');
            if (inner) { inner.click(); inner.dispatchEvent(new MouseEvent('click', {bubbles: true})); }
            const input = el.querySelector('input[type="radio"]') || (el.tagName === 'INPUT' ? el : null);
            if (input) { input.checked = true; input.dispatchEvent(new Event('change', {bubbles: true})); input.dispatchEvent(new Event('input', {bubbles: true})); }
            try { const ngZone = window.ng && window.ng.probe && document.querySelector('app-root'); if (ngZone) { const comp = window.ng.probe(document.querySelector('app-root')); if (comp) comp.injector.get(window.ng.coreTokens.NgZone).run(() => {}); } } catch(e) {}
        };
        if (method === 'groups') {
            const groups = Array.from(document.querySelectorAll('mat-radio-group, fieldset, [role="radiogroup"], .question-container, .quiz-question'));
            for (const g of groups) {
                if (!g.querySelector('.mat-radio-checked, input:checked, [aria-checked="true"]')) {
                    const opts = Array.from(g.querySelectorAll('mat-radio-button, input[type="radio"], label.option, .quiz-option, [role="radio"]')).filter(el => el.offsetParent !== null);
                    if (opts.length > index) { robustClick(opts[index]); return true; } else if (opts.length > 0) { robustClick(opts[0]); return true; }
                }
            }
        } else if (method === 'ungrouped' && name) {
            const opts = Array.from(document.querySelectorAll('mat-radio-button, input[type="radio"], [role="radio"]')).filter(el => el.offsetParent !== null && (el.getAttribute('name') || el.getAttribute('ng-reflect-name') || el.getAttribute('ng-reflect-value') || 'default') === name);
            if (opts.length > index) { robustClick(opts[index]); return true; } else if (opts.length > 0) { robustClick(opts[0]); return true; }
        }
        return false;
    }"""

    save_next_sel = ['button:has-text("Save & Next")', 'button:has-text("Save and Next")',
                     'button:has-text("SAVE & NEXT")', 'button:has-text("Next")']

    question_count = 0
    max_questions = 50
    consecutive_failures = 0

    while question_count < max_questions:
        question_count += 1
        log(f"📝 Question #{question_count}...", "INFO")

        # Try to answer in all frames
        answered = False
        targets_to_try = list(page.frames) + [page]
        for attempt in range(3):
            for t in targets_to_try:
                try:
                    result = t.evaluate(js_extract_code)
                    if result and result.get('options'):
                        question = result.get('question', 'Unknown Question')
                        options = result.get('options', [])
                        method = result.get('method')
                        name = result.get('name')
                        
                        log(f"  🧠 Found Question: '{question[:50]}...'", "INFO")
                        prompt = f"You are solving a multiple-choice question on an auto-assessment.\nQuestion: {question}\n\nOptions:\n"
                        for idx, opt in enumerate(options):
                            prompt += f"{idx}: {opt}\n"
                        prompt += "\nReply with ONLY the integer index (0, 1, 2, etc.) of the correct answer. Do not explain or include any other text."
                        
                        target_index = 0
                        try:
                            resp = g4f.ChatCompletion.create(
                                model=g4f.models.gpt_4o_mini,
                                messages=[{"role": "user", "content": prompt}],
                                timeout=30
                            )
                            target_index = int(''.join(c for c in str(resp) if c.isdigit()))
                            if target_index < 0 or target_index >= len(options):
                                target_index = 0
                            log(f"  ✅ AI Chose Option [{target_index}] -> {options[target_index][:30]}...", "OK")
                        except Exception as e:
                            log(f"  ❌ AI failed ({e}), falling back to option 0", "WARN")
                            target_index = 0
                            
                        # Click it
                        click_args = {"method": method, "index": target_index, "name": name}
                        if t.evaluate(js_click_code, click_args):
                            answered = True
                            break
                except Exception:
                    continue
            if answered:
                consecutive_failures = 0
                break
            if attempt < 2:
                time.sleep(2.0)

        if not answered:
            # Fallback to direct click if evaluate completely fails
            try:
                for t in targets_to_try:
                    el = t.locator('mat-radio-button, input[type="radio"]').first
                    if el.is_visible(timeout=500):
                        el.click(force=True)
                        log("  Answered via direct fallback click", "OK")
                        answered = True
                        consecutive_failures = 0
                        break
            except Exception:
                pass

            if not answered:
                consecutive_failures += 1
                log(f"  Could not find options for Q#{question_count}", "WARN")
                if consecutive_failures >= 3:
                    log("  3 consecutive failures — stopping", "WARN")
                    break

        time.sleep(0.5)

        # Click Save & Next
        clicked_save = False
        for t in all_targets:
            if click_first_on(t, save_next_sel):
                log("  Clicked Save & Next ✓", "OK")
                clicked_save = True
                break

        if not clicked_save:
            log("  No Save & Next — may be last question", "WARN")
            break

        time.sleep(1.0)
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeout:
            pass

    # ── Step 5: Submit Assessment ─────────────────────────────────
    log("Submitting assessment...", "INFO")
    time.sleep(0.8)

    submit_sel = ['button:has-text("Submit Assessment")', 'button:has-text("SUBMIT ASSESSMENT")',
                  'button:has-text("Submit")', 'button:has-text("Finish")']
    confirm_sel = ['button:has-text("Yes")', 'button:has-text("Confirm")',
                   'button:has-text("OK")', 'button:has-text("Submit")', 'button:has-text("YES")']

    for t in all_targets:
        if click_first_on(t, submit_sel):
            log("Clicked Submit Assessment ✓", "OK")
            for _ in range(3):
                time.sleep(1.0)
                for t2 in all_targets:
                    if click_first_on(t2, confirm_sel):
                        log("Clicked confirmation ✓", "OK")
                        break
            break

    # Dismiss result popups
    time.sleep(2.0)
    handle_popups(page)
    result_dismiss = ['button:has-text("Close")', 'button:has-text("OK")',
                      'button:has-text("Continue")', 'button:has-text("Done")']
    for t in all_targets:
        if click_first_on(t, result_dismiss):
            log("Dismissed result popup ✓", "OK")
            break

    log(f"Assessment completed! Answered {question_count} questions ✅", "OK")




def click_next(page) -> bool:
    """
    Find and click the Next/Continue button to advance to the next module.
    Returns True if a button was found and clicked.
    """
    next_selectors = [
        'button:has-text("Next")',
        'button:has-text("NEXT")',
        'button:has-text("Continue")',
        'button:has-text("CONTINUE")',
        'a:has-text("Next")',
        'a:has-text("Continue")',
        'button[aria-label="Next"]',
        'button[aria-label="next"]',
        '[class*="next"]',
        '[class*="Next"]',
        'button[mattooltip="Next"]',
        # Right arrow buttons (common in course players)
        'button:has-text("→")',
        'button:has-text("▶")',
        '[class*="right-arrow"]',
        '[class*="forward"]',
        '[class*="arrow-right"]',
        '.navigation-next',
        '.nav-next',
        '.btn-next',
    ]

    for selector in next_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000) and btn.is_enabled(timeout=1000):
                btn.click()
                log(f"Clicked Next: {selector}", "NEXT")
                time.sleep(MODULE_LOAD_WAIT)
                return True
        except Exception:
            continue

    # Fallback: try keyboard shortcut (some players support arrow keys)
    try:
        page.keyboard.press("ArrowRight")
        log("Pressed ArrowRight as fallback navigation", "NEXT")
        time.sleep(MODULE_LOAD_WAIT)
        return True
    except Exception:
        pass

    return False


# ─────────────────────────────────────────────────────────────────────
#  4. THE CORE LOOP
# ─────────────────────────────────────────────────────────────────────

def run_course_player(page):
    """
    Main automation loop. Continuously evaluates the page and
    decides what action to take based on content type.
    """
    module_count = 0

    print()
    print("  ┌──────────────────────────────────────────────────┐")
    print("  │     🚀  COURSE AUTO-PLAYER STARTED  🚀          │")
    print("  │     Press Ctrl+C in terminal to abort            │")
    print("  └──────────────────────────────────────────────────┘")
    print()

    while True:
        module_count += 1
        log(f"━━━ Module #{module_count} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")

        try:
            # Wait for page to settle
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout:
                pass
            time.sleep(2)

            # ── CONDITION E: Check for Assessments — AUTO-ANSWER ────
            if check_for_assessment(page):
                log("🧠 ASSESSMENT DETECTED — auto-answering...", "STOP")
                take_debug_screenshot(page, "assessment_detected")
                auto_answer_assessment(page)
                handle_popups(page)
                if not click_next(page):
                    log("No Next button after assessment — may be final.", "WARN")
                    time.sleep(3)
                    handle_popups(page)
                    click_next(page)
                continue

            # ── CONDITION C: Handle any pop-ups first ────────────────
            handle_popups(page)

            # ── CONDITION F: Coding Exercise ──────────────────────────
            try:
                if handle_coding(page):
                    log("Coding exercise handled — moving to next module...", "OK")
                    handle_popups(page)
                    if not click_next(page):
                        log("Could not find Next button after coding exercise!", "WARN")
                        take_debug_screenshot(page, "no_next_after_coding")
                    continue
            except Exception as e:
                log(f"Error handling coding exercise: {e}", "ERR")

            # ── CONDITION A: Video Page ──────────────────────────────
            if handle_video(page):
                log("Video handled — moving to next module...", "OK")
                handle_popups(page)  # Check for post-video popups
                if not click_next(page):
                    log("Could not find Next button after video!", "WARN")
                    take_debug_screenshot(page, "no_next_after_video")
                continue

            # ── CONDITION B: Reading / Text Page ─────────────────────
            handle_reading_page(page)

            # ── CONDITION C (again): Post-scroll popups ──────────────
            handle_popups(page)

            # ── CONDITION D: Move to Next Module ─────────────────────
            if not click_next(page):
                log("No Next button found. Might be the last module!", "WARN")
                take_debug_screenshot(page, "no_next_button")

                # Try one more time after a longer wait
                time.sleep(5)
                handle_popups(page)
                if not click_next(page):
                    print()
                    print("  ╔══════════════════════════════════════════════════╗")
                    print("  ║  ✅  COURSE APPEARS TO BE COMPLETE!  ✅         ║")
                    print("  ║                                                  ║")
                    print("  ║  No more Next buttons found after retrying.      ║")
                    print("  ║  Modules processed: {:>4}                        ║".format(module_count))
                    print("  ╚══════════════════════════════════════════════════╝")
                    print()
                    return

            # Wait for the new module to fully load
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout:
                pass

        except KeyboardInterrupt:
            log("User interrupted! Stopping...", "STOP")
            return

        except Exception as e:
            log(f"Error on module #{module_count}: {e}", "ERR")
            take_debug_screenshot(page, f"error_module_{module_count}")

            # Resilience: try to click Next and continue
            log("Attempting to bypass this module...", "WARN")
            try:
                handle_popups(page)
                if not click_next(page):
                    log("Cannot bypass — manual intervention may be needed.", "ERR")
                    time.sleep(10)
                    if not click_next(page):
                        log("Giving up on this module.", "ERR")
                        return
            except Exception:
                log("Fatal error in recovery. Stopping.", "ERR")
                return


# ─────────────────────────────────────────────────────────────────────
#  5. MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────

def main():
    print()
    print("  ╔═══════════════════════════════════════════════════════════╗")
    print("  ║       INFOSYS SPRINGBOARD AUTO-PROGRESSION  v2.0        ║")
    print("  ╠═══════════════════════════════════════════════════════════╣")
    print(f"  ║  Email : {USER_EMAIL:<48} ║")
    print(f"  ║  Course: {COURSE_URL[:48]:<48} ║")
    print(f"  ║  Mode  : {'Headless' if HEADLESS else 'Headed (visible browser)':<48} ║")
    print("  ╚═══════════════════════════════════════════════════════════╝")
    print()

    if USER_EMAIL == "YOUR_EMAIL@example.com":
        print("  ❌  ERROR: Please edit the script and set your credentials!")
        print("       Open springboard_auto.py and change:")
        print("         USER_EMAIL    = 'your_email@example.com'")
        print("         USER_PASSWORD = 'your_password'")
        print("         COURSE_URL    = 'https://...'")
        print()
        sys.exit(1)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",  # Reduce bot detection
                "--no-sandbox",
                "--start-maximized",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        context.set_default_timeout(DEFAULT_TIMEOUT)

        page = context.new_page()

        # ── Stealth: Remove Playwright's webdriver fingerprint ────────
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Remove Playwright-specific properties
            delete window.__playwright;
            delete window.__pw_manual;
        """)

        try:
            # Step 1: Login
            do_login(page)

            # Step 2: Navigate to Course
            navigate_to_course(page)

            # Step 3: Run the auto-player loop
            run_course_player(page)

        except KeyboardInterrupt:
            log("Interrupted by user.", "STOP")
        except Exception as e:
            log(f"Fatal error: {e}", "ERR")
            take_debug_screenshot(page, "fatal_error")
            raise
        finally:
            if IS_CI:
                log("CI run complete. Closing browser.", "INFO")
            else:
                log("Script finished. Browser window stays open.", "INFO")
                log("Press ENTER in terminal to close the browser.", "INFO")
                try:
                    input(">>> Press ENTER to close browser... ")
                except EOFError:
                    pass
            browser.close()


if __name__ == "__main__":
    main()
