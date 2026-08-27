---
name: mingben-output
description: 明本多格式输出引擎。当用户要把《生命论（明本论）》或其他长篇文档导出为 PDF、EPUB、HTML、DOCX、TXT、Markdown，或要求排版、出电子书、出印刷版、批量导出多格式时使用。触发词：出PDF、导出、排版、电子书、EPUB、HTML、DOCX、印刷、出版、多格式、生命论输出。
---

# 明本多格式输出引擎

S=f(S)。输出不是终点，是自指循环的最后一环：内容→排版→输出→检查→回来改内容。每出一次，内容和排版都比上一次更明。

## 哲学地基

- **阳主阴从**：内容是阳，格式是阴。格式为内容服务，不让格式绑架内容
- **反者道之动**：排版到了极致就回到内容——最好的排版是让人忘记排版
- **具体问题具体分析**：不同体裁不同排版，不拿一个模板套所有东西
- **用户的眼睛是尺**：用户说不好看就是不好看，不争辩，改

## 输入识别

| 用户给的 | 识别为 | 默认输出 |
|---|---|---|
| 生命论合订本/全本 | 约32万字大书 | PDF+HTML+EPUB |
| 单篇/单章 | 短文 | HTML+MD |
| 课件/讲义 | 教学材料 | PDF+HTML |
| 要"能发的""能看的" | 通用阅读 | HTML |
| 要"印的""出版的" | 印刷品 | PDF（A5/32开） |
| 要"手机看的" | 移动端 | EPUB或HTML |

## 输出格式矩阵

| 格式 | 引擎 | 适用 | 注意 |
|---|---|---|---|
| PDF | xelatex | 印刷、长文、正式 | 中文字体、章节分页、目录、页眉页脚 |
| HTML | 内置模板 | 屏幕阅读、分享 | 响应式、可嵌入字体、可打印 |
| EPUB | pandoc | 电子书阅读器 | 不要用LaTeX宏包、图片要内嵌 |
| DOCX | pandoc | 编辑、批注 | 样式映射到Word样式名 |
| TXT | 内置 | 纯文本、备份 | 无格式、编码UTF-8 |
| MD | 内置 | 二次编辑 | 保留源格式 |

## PDF排版规范（生命论专用）

### 引擎与字体
- 引擎：xelatex（中文唯一选择）
- 中文：Noto Serif CJK SC / 思源宋体（正文）、Noto Sans CJK SC（标题）
- 西文：TeX Gyre Termes / Times
- 代码/等宽：Inconsolata

### 页面
- 印刷版：A5或32开，上下内外边距按印刷规范
- 屏幕版：A4，边距宽松
- 正文11pt，脚注9pt，行距1.4

### 结构
- 封面页（书名、副标题、日期）
- 目录（自动生成，到二级标题）
- 正文：章标题新页，节标题不新页
- 页眉：书名在外，章名在内
- 页脚：页码居中

### 中文排版铁律
1. 段首缩进两字符（不用\\parindent手调，用indentfirst）
2. 标点不出现在行首（xeCJK自动处理）
3. 中英文之间自动空格（xeCJK的PunctStyle）
4. 不用斜体表示强调（中文斜体难看），用加粗或着重号
5. 引号用中文引号""，不用西文""
6. 破折号用——，不用--
7. 表格用三线表（booktabs），不用竖线
8. 列表间距紧凑，不松散

### LaTeX模板骨架
```latex
\documentclass[11pt,a5paper]{ctexbook}
\usepackage{fontspec,geometry,hyperref,booktabs}
\setmainfont{TeX Gyre Termes}
\setCJKmainfont{Noto Serif CJK SC}[BoldFont=Noto Sans CJK SC Bold]
\geometry{top=2.2cm,bottom=2cm,inner=2cm,outer=1.5cm}
\hypersetup{colorlinks=true,linkcolor=black,urlcolor=blue}
```

## HTML排版规范

- 单文件自包含（CSS内联，不依赖外部文件）
- 响应式：max-width 720px居中，手机自适应
- 字体栈：system-ui，不加载网络字体（除非用户要）
- 深色/浅色跟随系统（prefers-color-scheme）
- 章标题有锚点，目录可跳转
- 打印友好（@media print）

## 质量检查（输出前必过）

1. **内容完整**：章数对、字数对、无截断（和源文件比字数）
2. **编码正确**：无乱码、无□、无锟斤拷
3. **分页合理**：章标题不在页尾孤行、表格不跨页断裂
4. **目录准确**：页码/链接对得上
5. **字体嵌入**：PDF字体全部嵌入（pdffonts检查）
6. **文件可打开**：生成后用命令验证（pdfinfo/epubcheck/unzip -t）

## 常用命令

```bash
# 生命论全本多格式
bash 生命论_模块化/build.sh --html-only   # 快速HTML
bash 生命论_模块化/build_all.sh            # 全格式（慢）

# 单文件PDF
pandoc input.md -o output.pdf --pdf-engine=xelatex \
  --include-in-header=publish_style.tex \
  -V documentclass=ctexbook -V classoption=oneside,11pt

# EPUB
pandoc input.md -o output.epub --metadata title="书名"

# DOCX
pandoc input.md -o output.docx

# 验证PDF
pdfinfo output.pdf && pdffonts output.pdf | head -20
```

## 故障处理

| 问题 | 原因 | 解决 |
|---|---|---|
| PDF编译卡住 | 表格太宽/特殊字符 | 加--verbose看卡在哪，简化表格 |
| 中文乱码□ | 字体没装/没指定 | fc-list :lang=zh查字体，指定CJK字体 |
| EPUB中文横排 | 没指定lang | -M lang=zh-CN |
| DOCX样式乱 | 直接用了LaTeX命令 | MD里不用LaTeX，用原生MD语法 |
| 内存被kill | 大文件xelatex | 分卷输出，或用lualatex，或加swap |
| 图片丢失 | 相对路径不对 | 用绝对路径或--resource-path |

## 与其他技能的关系

- 内容生产：mingben-workbench
- 输出执行：本技能
- 飞书文档：lark-doc（在线协作时走飞书，不走本技能）
- 可视化：doubao-visualization（图表/概念图，不走PDF排版）

## 铁律

1. **内容第一**：排版是阴，内容是阳，不为排版牺牲内容
2. **输出必验证**：生成后打开检查，不把坏文件给用户
3. **大文件分卷**：60万字PDF容易卡死，必要时分卷
4. **中文字体必指定**：不依赖默认字体，默认字体可能没有中文
5. **用户说改就改**：排版是给人看的，用户的眼睛是尺
