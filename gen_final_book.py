#!/usr/bin/env python3
import re
import os

moddir = "生命论_模块化"

# 读取manifest，按卷分组
manifest = []
with open(os.path.join(moddir, "manifest.txt"), "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("10_参考资料") and not line.startswith("09_练习"):
            manifest.append(line)

# 按卷分组
volumes = {}
vol_order = []
for mf in manifest:
    parts = mf.split("/")
    vol_dir = parts[0]
    if vol_dir not in volumes:
        volumes[vol_dir] = []
        vol_order.append(vol_dir)
    volumes[vol_dir].append(mf)

# 读取卷标题
vol_titles = {}
for vol_dir in vol_order:
    title_file = os.path.join(moddir, vol_dir, "00_卷标题.md")
    if os.path.exists(title_file):
        with open(title_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    vol_titles[vol_dir] = line.strip().lstrip("# ").strip()
                    break

# 读取所有篇文件，提取篇标题和章标题
all_content = []
toc_data = []

for vol_dir in vol_order:
    vol_title = vol_titles.get(vol_dir, vol_dir)
    vol_pians = []
    
    # 卷标题文件内容
    title_file = os.path.join(moddir, vol_dir, "00_卷标题.md")
    if os.path.exists(title_file):
        with open(title_file, "r", encoding="utf-8") as f:
            all_content.append(f.read())
            all_content.append("\n\n")
    
    for mf in volumes[vol_dir]:
        if "00_卷标题" in mf:
            continue
        filepath = os.path.join(moddir, mf)
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        all_content.append(content)
        all_content.append("\n\n")
        
        # 提取篇标题
        pian_title = None
        zhangs = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## 第") and "篇" in line and not pian_title:
                pian_title = line.lstrip("# ").strip()
            elif line.startswith("### 第") and "章" in line and pian_title:
                zhangs.append(line.lstrip("# ").strip())
        
        if pian_title:
            vol_pians.append({"title": pian_title, "zhangs": zhangs})
    
    toc_data.append({"vol": vol_title, "pians": vol_pians})

# 统计
total_vol = len(toc_data)
total_pian = sum(len(v["pians"]) for v in toc_data)
total_zhang = sum(len(p["zhangs"]) for v in toc_data for p in v["pians"])
full_text = "\n".join(all_content)
hanzi = len(re.findall(r'[\u4e00-\u9fff]', full_text))

print(f"卷: {total_vol}, 篇: {total_pian}, 章: {total_zhang}, 汉字: {hanzi:,}")

# 生成目录（纯文本，不用markdown列表）
toc = []
toc.append("# 目录")
toc.append("")
toc.append(f"**全本结构：{total_vol}卷 {total_pian}篇 {total_zhang}章**")
toc.append(f"**当前字数：约 {hanzi//10000} 万字（汉字）**")
toc.append("")
toc.append("> **说明：** 此为体系骨架版。核心命题与推导链条已完整建立，但各卷的经验材料、历史案例、与前人的逐条对话、文献考证等血肉尚未充分展开。按资本论（230万字仅覆盖生产关系一个领域）的密度估算，本体系九卷充分展开后，总规模可达 **1500-2500万字**。当前版本供了解体系框架与核心命题之用。")
toc.append("")
toc.append("---")
toc.append("")

for v in toc_data:
    toc.append(f"## {v['vol']}")
    toc.append("")
    for p in v["pians"]:
        toc.append(f"**{p['title']}**")
        for z in p["zhangs"]:
            toc.append(f"　　{z}")
        toc.append("")

toc_text = "\n".join(toc)

# 封面
cover = """# 生命论（明本论）

### 从操作出发的存在论革命与旧哲学总清算

---

**全本·骨架版**

**2026年8月**

---

"""

# 正文从总序开始
正文_start = full_text.find("# 总序")
if 正文_start == -1:
    正文_start = 0
正文 = full_text[正文_start:]

final = cover + toc_text + "\n---\n\n" + 正文

with open("/tmp/final_book_v2.md", "w", encoding="utf-8") as f:
    f.write(final)

print(f"最终文件生成: /tmp/final_book_v2.md")
