from __future__ import annotations

import re


def parse_policy_markdown(markdown_text: str) -> list[dict]:
    chunks = []
    lines = markdown_text.split('\n')
    
    current_h2 = ""
    current_h3 = ""
    current_content = []
    
    def save_chunk():
        if current_h2 and current_content:
            text = "\n".join(current_content).strip()
            if text:
                if current_h3:
                    rendered_text = f"## {current_h2}\n### {current_h3}\n{text}"
                    citation = f"{current_h2} > {current_h3}"
                else:
                    rendered_text = f"## {current_h2}\n{text}"
                    citation = f"{current_h2}"
                
                chunks.append({
                    "section_h2": current_h2,
                    "section_h3": current_h3,
                    "citation": citation,
                    "rendered_text": rendered_text
                })

    for line in lines:
        h2_match = re.match(r'^##\s+(.*)', line)
        h3_match = re.match(r'^###\s+(.*)', line)
        
        if h2_match:
            save_chunk()
            current_h2 = h2_match.group(1).strip()
            current_h3 = ""
            current_content = []
        elif h3_match:
            save_chunk()
            current_h3 = h3_match.group(1).strip()
            current_content = []
        else:
            if current_h2:
                current_content.append(line)
                
    save_chunk()
    return chunks
