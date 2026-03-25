import re

with open('c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Faster Reading Scroll
text = text.replace('step = vh * 0.6  # Overlap scrolls', 'step = vh * 0.9  # Faster scrolls')
text = text.replace('time.sleep(2)', 'time.sleep(0.8)') # Replace all 2s stops with 0.8s
text = text.replace('time.sleep(3)', 'time.sleep(1.5)') # Reduce 3s waits
text = text.replace('time.sleep(4)', 'time.sleep(2.0)') # Reduce 4s waits
text = text.replace('time.sleep(10)', 'time.sleep(5.0)') # Reduce 10s waits

# 2. Add UI Play Button Clicks to Video Handler
new_video_start = """self.log("Scanning for video elements...", "VIDEO")

        # Press UI Play buttons FIRST to bypass browser Autoplay policies
        play_selectors = ['.vjs-big-play-button', 'button.vjs-play-control', '.play-button', '[title="Play"]', 'button:has-text("Play")', 'mat-icon:has-text("play_arrow")']
        try:
            for s in play_selectors:
                if page.locator(s).first.is_visible(timeout=500):
                    page.locator(s).first.click(force=True)
                    time.sleep(0.5)
            for frame in page.frames:
                for s in play_selectors:
                    try:
                        if frame.locator(s).first.is_visible(timeout=500):
                            frame.locator(s).first.click(force=True)
                            time.sleep(0.5)
                    except: pass
        except: pass

        for i, frame in enumerate(page.frames):"""

text = text.replace('self.log("Scanning for video elements...", "VIDEO")\n\n        for i, frame in enumerate(page.frames):', new_video_start)

# 3. Add same click logic inside shadow DOM block
shadow_play_injection = """if has_shadow:
                self.log("Found video in Shadow DOM — playing for 5s then skipping", "VIDEO")
                page.evaluate('''() => {
                    // Try to click any shadow UI play buttons FIRST
                    for (const el of document.querySelectorAll('*')) {
                        if (el.shadowRoot) {
                            const btn = el.shadowRoot.querySelector('.vjs-big-play-button, .play-button');
                            if (btn && typeof btn.click === 'function') btn.click();
                        }
                    }
                    
                    for (const el of document.querySelectorAll('*')) {''')"""

text = text.replace('if has_shadow:\n                self.log("Found video in Shadow DOM — playing for 5s then skipping", "VIDEO")\n                page.evaluate("""() => {\n                    for (const el of document.querySelectorAll(\'*\')) {', shadow_play_injection)

with open('c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('SUCCESSFULLY PATCHED')
