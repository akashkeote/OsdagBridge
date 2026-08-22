import os
import re

dir_path = r'C:\Users\AkashK\.gemini\antigravity\scratch\OsdagBridge\src\osdagbridge\core\reports'
pattern = re.compile(
    r'(\\begin\{longtable\}\{[^\}]+\})\s*'
    r'(\\caption\{[^\}]+\}\s*\\\\?)?\s*'
    r'\\hline\s*'
    r'([^\\]+\\\\\s*)'
    r'\\hline', 
    re.DOTALL
)

for root, _, files in os.walk(dir_path):
    for f in files:
        if f.endswith('.py') and f.startswith('chap'):
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8') as file:
                content = file.read()
            
            def repl(m):
                lt_def = m.group(1)
                caption = (m.group(2) or "").strip()
                # If there's a \\ at the end of caption, keep it, else add it
                if caption and not caption.endswith('\\\\'):
                    caption += ' \\\\'
                
                header_row = m.group(3).strip()
                
                cont_cap = caption.replace('}', ' (Continued)}') if caption else ""
                
                res = f"{lt_def}\n"
                if caption: res += f"{caption}\n"
                res += f"\\hline\n{header_row}\n\\hline\n\\endfirsthead\n"
                
                if cont_cap: res += f"{cont_cap}\n"
                res += f"\\hline\n{header_row}\n\\hline\n\\endhead"
                
                return res

            
            new_content = pattern.sub(repl, content)
            if new_content != content:
                with open(fp, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f'Updated {f}')
