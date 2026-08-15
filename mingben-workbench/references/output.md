# 多格式输出

## 生命论构建系统

### 快速HTML（秒级）
```bash
bash 生命论_模块化/build.sh --html-only
```
输出：`生命论（明本论）合订本.html`

### 全格式构建
```bash
bash 生命论_模块化/build_all.sh          # 全部格式
bash 生命论_模块化/build_all.sh pdf epub  # 指定格式
```
输出到`生命论_输出/`，支持：pdf / html / epub / docx / txt / md

### PDF单独构建（5-10分钟，后台跑）
```bash
bash 生命论_模块化/build.sh --pdf-only
```
用xelatex + Noto Serif CJK SC，167页，八卦符号正常显示。

### 新章节合并
```bash
python3 生命论_模块化/auto_merge.py <新文件>   # 自动编号合并
python3 生命论_模块化/auto_merge.py --validate  # 校验编号
python3 生命论_模块化/auto_merge.py --index     # 列章节
```

### 替换模块
```bash
bash 生命论_模块化/replace.sh <关键词> <新文件>
```

## 样式文件

- `publish_style.tex`：LaTeX样式（Noto Serif CJK SC、1.5倍行距、首行缩进、页眉页脚）
- `html_style.css` + `html_header.html`：HTML样式（衬线字体、可点击目录、手机适配、封面）

## 其他内容输出

### 飞书文档
长文、报告、笔记 → lark-doc技能，创建在线文档，手机电脑都能看。

### 可视化
概念图、关系图、流程图 → ECharts HTML（参考`生命论_概念图谱_升级版.html`，110节点）。

### 画板
Mermaid图 → lark-whiteboard技能。

### 网页应用
交互式工具 → app_builder_agent（读app.md）。

## 备份与版本管理

- 本地git：`生命论_模块化/`已有仓库
- 远程备份：推GitHub/Gitee私有仓库（读下方）
- 全量打包：`zip -r 生命论_备份_$(date +%Y%m%d).zip 生命论_模块化/ .user_skills/ 生命论合订本_最新.md`

### 远程推送（需先配置SSH key）
```bash
cd 生命论_模块化
git remote add origin git@github.com:<用户名>/shengminglun.git
git push -u origin main
```
