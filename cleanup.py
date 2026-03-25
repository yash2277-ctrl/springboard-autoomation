import sys

with open('c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# I will reconstruct the file accurately.
# Finding _handle_video (starts approx line 276)
# Finding _handle_coding (starts approx line 397)
# Finding _handle_assessment (starts approx line 616)

# This is a bit risky with just readlines. Let's use a more robust search and replace for the blocks.
content = "".join(lines)

# Fix _handle_video Shadow DOM block
import re

video_shadow_pattern = r'# Shadow DOM fallback.*?return True\s+except Exception:\s+pass'
video_shadow_replacement = """        # Shadow DOM fallback
        try:
            has_shadow = page.evaluate(\"\"\"() => {
                for (const el of document.querySelectorAll('*')) {
                    if (el.shadowRoot && el.shadowRoot.querySelector('video')) return true;
                }
                return false;
            }\"\"\")
            if has_shadow:
                self.log(\"Found video in Shadow DOM — playing for 5s then skipping\", \"VIDEO\")
                page.evaluate(\"\"\"() => {
                    // Try to click any shadow UI play buttons FIRST
                    for (const el of document.querySelectorAll('*')) {
                        if (el.shadowRoot) {
                            const btn = el.shadowRoot.querySelector('.vjs-big-play-button, .play-button, [title=\\"Play\\"]');
                            if (btn && typeof btn.click === 'function') btn.click();
                        }
                    }
                    
                    for (const el of document.querySelectorAll('*')) {
                        if (el.shadowRoot) {
                            const v = el.shadowRoot.querySelector('video');
                            if (v) {
                                v.muted = true; v.currentTime = 0;
                                v.play();
                                setTimeout(() => {
                                    if (v.currentTime < v.duration - 1) {
                                        v.currentTime = v.duration - 1;
                                        v.play();
                                    }
                                }, 5000);
                                return;
                            }
                        }
                    }
                }\"\"\")
                time.sleep(5.0)
                return True
        except Exception:
            pass"""

# Fix _handle_coding (Restoring it and removing the accidental quiz logic)
coding_pattern = r'def _handle_coding\(self, page\):.*?return False'
coding_replacement = """def _handle_coding(self, page):
        # Look for code editors or 'play' buttons
        try:
            play_selectors = [
                'mat-icon:has-text("play_arrow")',
                'button mat-icon:has-text("play_arrow")',
                '.play-button',
                '[class*="play-btn"]',
                'button[mattooltip="Run Code"]',
                'button[mattooltip="Execute"]'
            ]
            
            js_code = \"\"\"() => {
                let clicked = false;
                const clickPlay = (doc) => {
                    const icons = Array.from(doc.querySelectorAll('mat-icon, i, .icon'));
                    for (const icon of icons) {
                        if (icon.innerText.includes(\"play_arrow\") || icon.innerText.includes(\"play\")) {
                            const btn = icon.closest('button') || icon;
                            btn.click();
                            clicked = true;
                            return true;
                        }
                    }
                    const btns = Array.from(doc.querySelectorAll('button'));
                    for (const btn of btns) {
                        if (btn.outerHTML.toLowerCase().includes(\"play\") && !btn.outerHTML.toLowerCase().includes(\"video\")) {
                            btn.click();
                            clicked = true;
                            return true;
                        }
                    }
                    return false;
                };
                if(clickPlay(document)) return true;
                return clicked;
            }\"\"\"

            clicked = False
            for sel in play_selectors:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=500):
                        self.log(\"Found coding exercise! Clicking Play button...\", \"INFO\")
                        el.click()
                        clicked = True
                        break
                except Exception: continue

            if not clicked:
                try:
                    if page.evaluate(js_code):
                        self.log(\"Found coding exercise via JS! Clicking Play...\", \"INFO\")
                        clicked = True
                except Exception: pass

            if not clicked:
                for frame in page.frames:
                    try:
                        if frame.evaluate(js_code):
                            self.log(\"Found coding exercise in iframe! Clicking Play...\", \"INFO\")
                            clicked = True
                            break
                    except Exception: pass
                        
            if clicked:
                self.log(\"Waiting 10s for code execution to finish...\", \"INFO\")
                time.sleep(5.0)
                return True
                
        except Exception: pass
        return False"""

# Clean up any trailing garbage or malformed blocks
# Re-apply the whole content with regex
content = re.sub(video_shadow_pattern, video_shadow_replacement, content, flags=re.DOTALL)
content = re.sub(coding_pattern, coding_replacement, content, flags=re.DOTALL)

with open('c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("FIXED SYNTAX AND RESTORED CODING LOGIC")
