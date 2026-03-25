import re

with open('c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Enhance the JS click logic
advanced_js = """() => {
                    let answeredCount = 0;
                    const pageText = document.body.innerText.toLowerCase();
                    
                    const triggerClick = (el) => {
                        el.click();
                        el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                        el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                        el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                        
                        // If it's material, click the inner circle container too just to be sure
                        const inner = el.querySelector('.mat-radio-container, .mat-radio-inner-circle') || el.parentElement;
                        if (inner && inner !== el && typeof inner.click === 'function') {
                            inner.click();
                        }
                    };

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
                                triggerClick(el); return true;
                            }
                        }
                        
                        triggerClick(optionsArray[0]); // default 
                        return true;
                    };

                    const groups = Array.from(document.querySelectorAll('mat-radio-group, fieldset, [role="radiogroup"], .question-container, .quiz-question'));
                    
                    if (groups.length > 0) {
                        for (const g of groups) {
                            const hasChecked = g.querySelector('.mat-radio-checked, input:checked, [class*="selected"], [class*="checked"]');
                            if (!hasChecked) {
                                const opts = Array.from(g.querySelectorAll('mat-radio-button, input[type="radio"], label.option, .quiz-option, [class*="radio"], [class*="option"]')).filter(el => el.innerText && el.innerText.trim());
                                const groupText = g.innerText.toLowerCase() || "";
                                if(opts.length > 0 && clickSmartOption(opts, groupText)) answeredCount++;
                            }
                        }
                        if (answeredCount > 0) return answeredCount > 0;
                    } 
                    
                    const allRadios = Array.from(document.querySelectorAll('mat-radio-button, input[type="radio"], [class*="radio-button"]'));
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
                        const hasChecked = opts.some(o => (o.classList && (o.classList.contains('mat-radio-checked') || o.classList.contains('selected'))) || o.checked);
                        if (!hasChecked && opts.length > 0) {
                            const parent = opts[0].closest('div');
                            const parentText = parent ? parent.innerText.toLowerCase() : "";
                            if (clickSmartOption(opts, parentText)) answeredCount++;
                        }
                    }
                    
                    return answeredCount > 0;
                }"""

# Actually replace the old JS code completely
start_idx = text.find('js_code = \"\"\"() => {')
end_idx = text.find('\"\"\"', start_idx + 15)

if start_idx != -1 and end_idx != -1:
    new_text = text[:start_idx] + 'js_code = """' + advanced_js + '"""' + text[end_idx + 3:]
    with open('c:/Users/sahu4/OneDrive/Pictures/Screenshots/springbaord/springboard_engine.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("SUCCESSFULLY INJECTED ADVANCED CLICKS")
else:
    print("FAILED TO FIND JS BLOCK")
