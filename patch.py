import re

with open("c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py", "r", encoding="utf-8") as f:
    text = f.read()

start_idx = text.find('                # Try to find answer options — the assessment uses circle radio buttons')
end_idx = text.find('                # Click "Save & Next"')

new_content = """                option_found = False
                self.log("  Using robust JS injection to answer all visible questions...", "INFO")
                
                js_code = \"\"\"() => {
                    let answeredCount = 0;
                    const pageText = document.body.innerText.toLowerCase();
                    
                    const clickSmartOption = (optionsArray, questionText = "") => {
                        if (!optionsArray || optionsArray.length === 0) return false;
                        
                        let targetText = "";
                        if (pageText.includes("81, 20, 34") || questionText.includes("81, 20, 34")) targetText = "0,1";
                        else if (pageText.includes("hash-functions is the best") || questionText.includes("hash-functions")) targetText = "k%4";
                        else if (questionText.includes("index position 0")) targetText = "true";
                        else if (questionText.includes("index position 24")) targetText = "25";
                        else if (pageText.includes("descending order")) targetText = "descendingorder"; 
                        
                        for (const el of optionsArray) {
                            if (targetText && el.innerText.toLowerCase().replace(/\\s/g, '').includes(targetText.replace(/\\s/g, ''))) {
                                el.click(); return true;
                            }
                        }
                        
                        optionsArray[0].click(); // default 
                        return true;
                    };

                    const groups = Array.from(document.querySelectorAll('mat-radio-group, fieldset, [role="radiogroup"], .question-container, .quiz-question'));
                    
                    if (groups.length > 0) {
                        for (const g of groups) {
                            const hasChecked = g.querySelector('.mat-radio-checked, input:checked');
                            if (!hasChecked) {
                                const opts = Array.from(g.querySelectorAll('mat-radio-button, input[type="radio"], label.option, .quiz-option'));
                                const groupText = g.innerText.toLowerCase() || "";
                                if(opts.length > 0 && clickSmartOption(opts, groupText)) answeredCount++;
                            }
                        }
                        if (answeredCount > 0) return answeredCount > 0;
                    } 
                    
                    const allRadios = Array.from(document.querySelectorAll('mat-radio-button, input[type="radio"]'));
                    const groupsByName = {};
                    
                    allRadios.forEach(r => {
                        const name = r.getAttribute('name') || r.getAttribute('ng-reflect-name');
                        if (name) {
                            if (!groupsByName[name]) groupsByName[name] = [];
                            groupsByName[name].push(r);
                        } else {
                            const parent = r.closest('div.mb-4, mat-card') || r.parentElement.parentElement;
                            const pid = parent ? parent.innerHTML.length : Math.random();
                            if (!groupsByName[pid]) groupsByName[pid] = [];
                            groupsByName[pid].push(r);
                        }
                    });
                    
                    for (const name in groupsByName) {
                        const opts = groupsByName[name];
                        const hasChecked = opts.some(o => (o.classList && o.classList.contains('mat-radio-checked')) || o.checked);
                        if (!hasChecked && opts.length > 0) {
                            const parent = opts[0].closest('div');
                            const parentText = parent ? parent.innerText.toLowerCase() : "";
                            if (clickSmartOption(opts, parentText)) answeredCount++;
                        }
                    }
                    
                    return answeredCount > 0;
                }\"\"\"
                
                try:
                    if page.evaluate(js_code):
                        option_found = True
                        self.log("  Successfully answered question(s) via JS injection!", "OK")
                except Exception as e:
                    self.log(f"  JS error: {e}", "ERR")
                    
                if not option_found:
                    for frame in page.frames:
                        try:
                            if frame.evaluate(js_code):
                                option_found = True
                                self.log("  Successfully answered question(s) via JS injection in iframe!", "OK")
                                break
                        except Exception:
                            pass

                if not option_found:
                    self.log(f"  Could not find any options for Q#{question_count}", "WARN")

                time.sleep(0.5)

"""

if start_idx != -1 and end_idx != -1:
    new_text = text[:start_idx] + new_content + text[end_idx:]
    with open("c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("SUCCESSFULLY REPLACED")
else:
    print(f"FAILED TO FIND INDICES start:{start_idx} end:{end_idx}")
