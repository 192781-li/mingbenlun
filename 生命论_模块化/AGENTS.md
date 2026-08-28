# 生命论（明本论）模块化工程指南

## ⚠️ 开始工作前必读

1. **`docs/collaboration/LESSONS_LEARNED.md`（教训库）**——所有犯过的错误、修正、教训。不读就干活等于闭着眼跳坑。
2. **`NEW_AGENT_ONBOARDING.md`**——项目简介、卷结构、协作机制、待办、工作原则。
3. **`STATUS.md`**——当前谁在干什么、有什么待办。

犯了新错误必须追加到教训库。不记录错误的体系，注定重复同一个错误。

## 目录结构

```
生命论_模块化/
├── 00_修订记与体系总纲.md   # 修订记、纪律铁则、体系总纲
├── 00_总序与导论.md         # 总序+导论
├── 00_推导链总览.md         # 全书推导链
├── manifest.txt             # 各卷篇章文件清单（按合并顺序）
├── build.sh                 # 构建脚本
├── 01_卷一_存在论/
├── 03_卷三_认识论/
├── ...
├── 10_卷十_传统论/
└── 12_附录/
```

## 构建命令

```bash
cd /home/user/.super_doubao/super-doubao-runtime/workspace
bash 生命论_模块化/build.sh              # 构建HTML
bash 生命论_模块化/build.sh --html-only  # 只构建HTML（秒级）
bash 生命论_模块化/build.sh --check      # 只跑质检
```

输出：

- `生命论合订本_最新.md`
- `生命论（明本论）合订本.html`

构建后必须上传飞书：
```bash
lark-cli drive +upload --file "生命论（明本论）合订本.html" \
  --file-token "Cvsib1KDhoasfBxJEe1cc1xen3O" --as user --format json
```

## 新增/修改篇章的铁律

### 第一章 1. 新文件必须加入 manifest.txt

新建任何 `.md` 篇章文件后，**必须**把相对路径加到 `manifest.txt` 的正确位置（按卷序和篇序）。build.sh 按 manifest 顺序合并，不在 manifest 中的文件不会被合入。质检会自动检查遗漏。

### 第二章 2. 章号必须连续

全书章号从第1章连续编号到最后一章（当前266章）。新增章节时：

- 先确认插入位置前后章号：`grep -rn "^### 第" 生命论_模块化/`
- 如果在中间插入，后续所有章号必须顺延（用脚本批量改，不要手改）

- 章号用中文数字（第一百一十二章，不是第112章）
- 质检会检查连续性和重复

### 第三章 3. 章名不得重复

质检会检查重名章节。

### 第四章 4. 不要手改合订本

`生命论合订本_最新.md` 和 HTML 是构建产物，只改模块化文件，然后重新构建。

### 第五章 5. Git 提交与远程仓库

每次修改后推荐 `bash sync.sh "提交信息"`（自动构建验证+提交+推送），或手动 `git add -A && git commit -m "描述" && git push`。

**远程仓库（永久记录）：**

- 远程名：origin
- 地址：https://github.com/192781-li/mingbenlun.git

- 推送命令：`git push -u origin main`（首次）/ `git push`（后续）
- 注意：本地git无远程配置时，必须先 `git remote add origin https://github.com/192781-li/-.git`

- 仓库名：mingbenlun（原名`-`，已改名）

## 质检内容

build.sh 自动检查：

- null字节（稀疏文件问题）
- UTF-8乱码

- 章号连续性和重复
- 章名重复

- manifest完整性（遗漏文件/幽灵文件）
- 已知错字

## 统一CLI入口（mingben.py）

所有工具整合到一个命令：`python3 mingben-workbench/mingben.py <子命令>`

```bash
# 项目总览
python3 mingben-workbench/mingben.py status

# 构建
python3 mingben-workbench/mingben.py build --html-only   # 秒级HTML
python3 mingben-workbench/mingben.py build --check        # 只质检

# 自审（元监督）
python3 mingben-workbench/mingben.py audit                # 顺序自审
python3 mingben-workbench/mingben.py audit --parallel     # 并行自审

# 质量门控
python3 mingben-workbench/mingben.py quality <文件.md>

# 监控
python3 mingben-workbench/mingben.py monitor --background

# 自动合并新章节
python3 mingben-workbench/mingben.py merge <新文件.md> --dry-run

# 答题训练（F1/F2/F3）
python3 mingben-workbench/mingben.py exam analyze <题目.md>    # 三层分析
python3 mingben-workbench/mingben.py exam practice <题目.md>   # 三遍重写
python3 mingben-workbench/mingben.py exam status                # 训练进度
python3 mingben-workbench/mingben.py exam template              # 生成模板

# 构建+提交+推送
python3 mingben-workbench/mingben.py sync "提交信息"
```

## F1/F2/F3 答题训练系统

核心铁律：**F1永远先行，F3永远不阻塞F1。**

- **F1（感）**：题感——先于分析的直接抓取（题型、得分结构、答案骨架）
- **F2（应/操作）**：分析——在结构内填充因果逻辑和具体史实

- **F3（自指/递归）**：元认知——看见题目怎么造的，用它优化答案

哲学思维不是答题的敌人，是答题的外挂——前提是先把F1骨架搭好。

训练文件放在 `09_练习/` 目录，命名格式：`训练NN_主题_日期.md`。

三遍重写法：第一遍纯F1骨架→第二遍F1+F2填充史实→第三遍F1+F2+F3优化满分。

## 共享工具库（mingben_utils.py）

所有脚本共用的工具函数，消除重复代码：

- `cn2int()` / `int2cn()`：中文数字转换
- `parse_chapters()`：章节解析

- `read_text()` / `write_text()`：安全文件读写
- `human_size()`：人类可读大小

- `Timer`：计时器
- `run_parallel()`：并行执行

## 写作纪律（修订记中的铁则）

1. 三层纪律（存在论/社会分析/规范立场不混）
2. 术语单义性
3. 公理化姿态清除
4. 节奏由论证决定
5. 立场不变判断可错
6. 好比喻一个只用一次
7. 输入—炼化—产出—沉淀
8. 理论自己也是活的
9. 引用铁则：一切化用必须溯源（作者、书名、篇章、语境）
10. 颠倒的智慧
11. 立场坚定，刀不落空（不搞自我消解）
12. **退化情形铁律**：任何全称数学陈述（"在任何范畴中""所有模型都""不存在态射"）必须先检查退化情形。教训：T009原陈述"在任何LNL范畴中不存在η:νF→!νF"被终范畴1反驳——终范畴只有一个对象，所有东西同构，η当然存在。哲学对应：谈"生命不可克隆"的前提是系统里还有"生命"这回事可言，退化系统中活过程与静态状态的区分本身就消失了。绝对陈述必须加"非退化/non-degenerate"条件或明确排除退化结构。overclaim_checker.py 会自动检查。

## 作者

北原慢热。《生命论（明本论）》存在论地基完成于2026年6-8月。
