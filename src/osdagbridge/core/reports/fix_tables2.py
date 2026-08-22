import os

dir_path = r'C:\Users\AkashK\.gemini\antigravity\scratch\OsdagBridge\src\osdagbridge\core\reports'

for root, _, files in os.walk(dir_path):
    for f in files:
        if f.endswith('.py') and f.startswith('chap') and f != 'chap3.py':
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8') as file:
                content = file.read()
            
            chunks = content.split(r'\begin{longtable}')
            if len(chunks) == 1:
                continue
                
            new_chunks = [chunks[0]]
            for chunk in chunks[1:]:
                # find first \hline
                idx1 = chunk.find(r'\hline')
                if idx1 == -1:
                    new_chunks.append(r'\begin{longtable}' + chunk)
                    continue
                # find second \hline
                idx2 = chunk.find(r'\hline', idx1 + 6)
                if idx2 == -1:
                    new_chunks.append(r'\begin{longtable}' + chunk)
                    continue
                
                # The header block is from idx1 to idx2 + 6
                header_block = chunk[idx1:idx2+6]
                
                # Create the replacement
                replacement = header_block + "\n\\endfirsthead\n" + header_block + "\n\\endhead"
                
                new_chunk = chunk[:idx1] + replacement + chunk[idx2+6:]
                new_chunks.append(new_chunk)
                
            new_content = r'\begin{longtable}'.join(new_chunks)
            if new_content != content:
                with open(fp, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f'Updated {f}')
