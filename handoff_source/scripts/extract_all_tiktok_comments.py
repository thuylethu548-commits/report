import json
import re

def extract():
    results = []
    
    # 1. Step 15808 (Video 1: 23 tuổi mới ra trường)
    fpath1 = r'C:\Users\Administrator\.gemini\antigravity\brain\2743d13b-891b-483c-89fd-2ffb20910483\.system_generated\steps\15808\content.md'
    with open(fpath1, 'r', encoding='utf-8') as f:
        c1 = f.read()
    
    vo1 = re.search(r'<script type="application/ld\+json" id="VideoObject">(.*?)</script>', c1, re.DOTALL)
    if vo1:
        data1 = json.loads(vo1.group(1))
        results.append({
            "title": data1.get("name"),
            "url": data1.get("url"),
            "caption": data1.get("embeddedTextCaption"),
            "comments": data1.get("comment", [])
        })

    # 2. Step 15812 (Video 2: Bao nhiêu % người thành công)
    fpath2 = r'C:\Users\Administrator\.gemini\antigravity\brain\2743d13b-891b-483c-89fd-2ffb20910483\.system_generated\steps\15812\content.md'
    with open(fpath2, 'r', encoding='utf-8') as f:
        c2 = f.read()
    
    vo2 = re.search(r'<script type="application/ld\+json" id="VideoObject">(.*?)</script>', c2, re.DOTALL)
    if vo2:
        data2 = json.loads(vo2.group(1))
        results.append({
            "title": data2.get("name"),
            "url": data2.get("url"),
            "caption": data2.get("embeddedTextCaption"),
            "comments": data2.get("comment", [])
        })

    # 3. Step 15820 (Video 4: Câu chuyện kiên trì từ cháy tài khoản đến mua xe)
    fpath3 = r'C:\Users\Administrator\.gemini\antigravity\brain\2743d13b-891b-483c-89fd-2ffb20910483\.system_generated\steps\15820\content.md'
    with open(fpath3, 'r', encoding='utf-8') as f:
        c3 = f.read()
    
    vo3 = re.search(r'<script type="application/ld\+json" id="VideoObject">(.*?)</script>', c3, re.DOTALL)
    if vo3:
        data3 = json.loads(vo3.group(1))
        results.append({
            "title": data3.get("name"),
            "url": data3.get("url"),
            "caption": data3.get("embeddedTextCaption"),
            "comments": data3.get("comment", [])
        })

    out = "# TOÀN BỘ BÌNH LUẬN & LỜI KHUYÊN TỪ CÁC VIDEO CỦA @HOAI.XIM\n\n"
    for v in results:
        out += f"## 🎬 Video: {v['title']}\n"
        out += f"- **Link:** {v['url']}\n"
        out += f"- **Nội dung trên video:**\n```\n{v['caption']}\n```\n\n"
        out += f"### 💬 Danh sách {len(v['comments'])} bình luận tiêu biểu được cộng đồng tương tác mạnh:\n\n"
        for i, c in enumerate(v['comments']):
            author = c.get("author", {}).get("name", "Ẩn danh")
            handle = c.get("author", {}).get("alternateName", "")
            text = c.get("text", "")
            likes = 0
            if "interactionStatistic" in c:
                likes = c["interactionStatistic"].get("userInteractionCount", 0)
            out += f"**{i+1}. {author} (@{handle})** — ❤️ {likes} likes\n"
            out += f"> \"{text}\"\n\n"
        out += "\n---\n\n"

    with open(r'c:\sunMy\trading_bot\tiktok_comments_digest.md', 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"Successfully generated tiktok_comments_digest.md with {len(results)} videos!")

if __name__ == '__main__':
    extract()
