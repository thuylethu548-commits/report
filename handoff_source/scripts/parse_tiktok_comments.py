import json
import re
import glob
import os

files = glob.glob(r'C:\Users\Administrator\.gemini\antigravity\brain\2743d13b-891b-483c-89fd-2ffb20910483\.system_generated\steps\*\content.md')
print(f"Found {len(files)} content.md files")

for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for ld+json
        json_matches = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
        for jm in json_matches:
            try:
                data = json.loads(jm)
                if isinstance(data, dict) and "comment" in data:
                    print(f"\n==========================================")
                    print(f"FILE: {fpath}")
                    print(f"VIDEO TITLE: {data.get('name')}")
                    print(f"VIDEO DESC: {data.get('description')}")
                    print(f"TOTAL COMMENTS IN JSON: {len(data['comment'])}")
                    print(f"==========================================")
                    for idx, c in enumerate(data["comment"]):
                        author = c.get("author", {}).get("name", "Unknown")
                        text = c.get("text", "")
                        likes = c.get("interactionStatistic", {}).get("userInteractionCount", 0) if isinstance(c.get("interactionStatistic"), dict) else 0
                        print(f"[{idx+1}] {author} (❤️ {likes}): {text}\n")
            except Exception as e:
                pass
                
        # Also look for __UNIVERSAL_DATA_FOR_REHYDRATION__ or comments in script tags
        script_matches = re.findall(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', content, re.DOTALL)
        for sm in script_matches:
            print("Found __UNIVERSAL_DATA_FOR_REHYDRATION__")
    except Exception as ex:
        print(f"Error reading {fpath}: {ex}")
