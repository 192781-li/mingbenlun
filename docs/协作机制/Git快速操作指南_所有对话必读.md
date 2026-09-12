# Git 快速操作指南（所有对话/分站必读）

> 建立：2026-09-11 S00 ｜ 升级 v2.0：2026-09-12（补开工查重 L039、先分支后提交、四项CI轮询、squash、撞车归一、内容红线、回报清单、本地分叉自救）
> 用途：任何新对话/分站读完即能"又快又对"地完成 领任务→查重→干活→一次PR→合入→回报，不卡、不重、不返工。
> 配套：commit/文档头/命名格式见《明旭标准模式与操作惯性手册_v1.0》；分站职责见《库驱动协作机制规范_唯一权威版》；本指南只讲"怎么又快又稳地落库"。

---

## 一、一句话根因

**git 慢不是卡死，是仓库所在文件系统慢。** 不同文件系统速度差 200–2000 倍：

| 文件系统 | 路径 | git status |
|---------|------|-----------|
| **hpvs_fs（快，只用这个）** | `/home/user/mingbenlun` | **约0.9秒** |
| overlay | `/tmp` | 快但易失，不放正式产出 |
| virtiofs（慢，避开） | `/sandboxdata/workspace/file/mingbenlun`、`/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun` | 30秒跑不完 |

只给 5–10 秒 timeout 就会把 virtiofs 的慢误判成"卡死"。

---

## 二、路径铁律

- **日常唯一工作路径：`/home/user/mingbenlun`（hpvs_fs 快盘）。**
- 每次 Bash 后 shell 会重置目录，**每条 git 命令前都先 `cd /home/user/mingbenlun`**。
- 判断当前盘：`df -T .` → 见 virtiofs 立即换快盘；见 hpvs_fs/overlay 可用。
- 快盘不存在时一次性建立：
```bash
git clone --depth 50 https://github.com/192781-li/mingbenlun.git /home/user/mingbenlun
cd /home/user/mingbenlun
git config user.name "192781-li"
git config user.email "192781-li@users.noreply.github.com"
git config core.preloadindex true
git config core.quotepath false     # 中文路径不再显示成八进制转义
```

---

## 三、领任务到合入的全链路（照此顺序，不可跳步）

### 第0步 同步 + 三步查重（L039，防并行重复，必做）
```bash
cd /home/user/mingbenlun
git checkout main && git pull origin main
ls -1 "<目标目录>"                                   # ① 看目录里已有什么
git log --oneline -8 -- "<目标目录>"                  # ② 看最近谁写过同主题
grep -rln "<主题关键词>" docs 生命论_模块化 2>/dev/null # ③ 全库内容查重
```
> main 上若已有同主题"已合入/在途"文档：**禁止另起新文件**，转为给那一份"补增量/校订"（见第六节撞车归一）。

### 第1步 先建分支，再动手（铁律：绝不在本地 main 上直接 commit）
```bash
git checkout -b sXX-主题词-$(date +%Y%m%d)   # XX=站号；一次任务一分支
```
> 在本地 main 直接 commit 而远程又被别的 PR 推进，会造成本地/远程分叉（2026-09-12 已发生一次，见教训 L039/L040）。先建分支可从根上避免。

### 第2步 干活（内容红线见第七节；文档头/命名按标准模式手册）

### 第3步 相关改动攒成一次提交（不过频），推分支、开 PR
```bash
git -c core.quotepath=false add -A
git -c core.quotepath=false commit -m "SXX: 类型+具体内容(关键范畴/数据,一行看懂改了什么和为什么)"
git push -u origin <分支名>
gh pr create --base main --head <分支名> --title "SXX: 标题" --body "改了什么/为什么/涉及文件/查重结果"
```
> commit 标准：谁+做了什么+为什么，禁止 update/fix/test 这类无信息提交（标准模式手册模式一）。

### 第4步 等四项 CI 全过，再 squash 合入
```bash
gh pr checks <PR号>
# 四项：code-check / content-check / quality-check / security-check
# quality-check 通常最后出；有 pending 就隔约10秒再查一次（不要用长 sleep），别在未全过时 merge
gh pr merge <PR号> --squash --delete-branch     # 全库统一用 squash，不用 --merge
git checkout main && git pull origin main
```
**被别的 PR 抢先（head not up to date）时追平：**
```bash
git fetch origin && git rebase origin/main && git push --force-with-lease origin <分支名>
# 解决 rebase 冲突后 git rebase --continue，再重等 CI
```

---

## 四、timeout 规范

- 快盘 git 命令 **30 秒**；push/pull/PR 等走网络的 **60 秒**。
- 慢盘 status 类需 60 秒以上——但正解是换盘，不是干等。
- 速度基准（快盘）：status 0.9s / add 0.16s / commit 0.3s / push 2.5s / pull 1–3s。比这慢很多先查是不是跑错盘。

---

## 五、排查"git 卡住 / 本地分叉"的顺序

**疑似卡住：**
1. `df -T .`：virtiofs 就换快盘，问题直接消失
2. `ls .git/*.lock`：有锁＝上次 git 被强杀；删 lock 前先 `ps aux|grep git` 确认无 git 进程
3. `git rev-parse HEAD`：秒回＝git 没坏，慢在文件扫描
4. `git status --untracked-files=no`：还慢即 tracked 文件 stat 慢＝文件系统问题

**本地 main 与 origin/main 分叉（pull 报 divergent）：**
```bash
git fetch origin
git log --oneline origin/main..main      # 本地独有提交
git log --oneline main..origin/main      # 远程独有提交
git diff origin/main..main               # 逐字比对内容差异
```
- 若本地独有提交的内容已被远程 PR 等价覆盖（diff 为空）：`git checkout main && git reset --hard origin/main` 对齐权威，零损失。
- 若本地确有远程没有的增量：把增量在**新分支**上重提为 PR，不在 main 上硬合。拿不准就停下报告，不强行 push、不覆盖别人内容。

---

## 六、撞车归一（发现并行重复怎么办）

以"**先合入 main 且更完整**"者为唯一权威：把你这版独有的增量并进它 → 删除你新建的重复件 → 同一个 PR 完成"并增量+去重" → 按《教训库》L039 格式记一条（若属新教训）。**绝不让两份近义文件长期共存，也不许静默删改他人内容。**

---

## 七、内容质量红线（生命论项目特有，违反即返工）

1. **引用库内范畴前先读原文**：阴阳、沉积/发用、νF/!-模态、操作权、反自指、阳主阴从、结晶等，必须先 Grep/Read 库内正文按原意用；**禁止用外部哲学家/社会学术语做类比替代**（曾因把"沉积"类比 habitus 被重批）。
2. **用户原话原样收录**，不软化、不润色，包括口语重复、语气词、粗口。
3. **数字必有出处**；官方口径与学者估计（如 Maddison/伍晓鹰）分列，不混、不编；查不到标"待核实"。
4. **绝对不说"完美"。**
5. 标注"留待明旭亲手雕琢"的论证夹缝，只摆问题与候选，**不替用户定调**。
6. **不越界**：只动本任务范围；Coq `.v` 归 S04、哲学研判正文归 S01；不删文件、不改他站内容。
7. 信息走库不走口头：给分站派活/纠偏＝更新其运行指令文件或发 PR 评论，不靠对话转述（库驱动规范）。

---

## 八、完成后回报清单（固定格式，别多别少）

- 任务结论（1–3 句）
- 查重结果：目标目录已有什么、是否撞车、如何处理
- 合入信息：PR 号 + squash 后 commit 短 hash + main 最终 HEAD
- 新增/修改文件的仓库相对路径
- 留待明旭定调的点（无则写"无"）
- 失败项与原因（不得静默略过）

---

## 九、核心纪律（浓缩）

1. 先选对盘再操作，每条命令前确认在 `/home/user/mingbenlun`
2. git 慢≠git 坏，先怀疑文件系统
3. **先建分支再 commit，绝不在本地 main 直接提交；main 只走 PR**
4. 开工先三步查重，撞车只并增量不另起文件
5. 四项 CI 全过才 squash 合入，逻辑相关改动攒一次 PR、不过频
6. 内容守第七节红线：范畴读原文、原话不软化、数字有出处、不替明旭定调

---

## 附录：最强开工包（可整段复制给任何新对话/分站）

```text
【任务】你是明旭生命论项目分站。在 mingbenlun 完成我交给你的任务并规范落库，照下面做，不反问、不另找文档。
【路径】只用快盘 /home/user/mingbenlun（hpvs_fs）；每条git命令前先cd这里；慢盘virtiofs绝不用，怀疑卡先 df -T .。远程 https://github.com/192781-li/mingbenlun，main受保护只走PR。
【0 同步+查重】git checkout main && git pull origin main；然后 ls 目标目录 + git log --oneline -8 -- 目标目录 + grep -rln 主题词 docs 生命论_模块化；已有同主题就只补增量、不另起文件。
【1 先建分支】git checkout -b sXX-主题-$(date +%Y%m%d)，绝不在main上直接commit。
【2 内容红线】①用生命论范畴前先Grep/Read库内原文，禁外部哲学类比；②我原话原样收录含口语粗口；③数字必有出处、官方与学者估计分列、查不到标待核实；④不说"完美"；⑤"留待明旭雕琢"处只摆候选不代定调；⑥不碰S04的.v与S01哲学正文，不删文件。新文档带标准元数据头。
【3 一次提交】git -c core.quotepath=false add -A；commit -m "SXX: 谁+做了什么+为什么"；push -u origin 分支；gh pr create --base main --head 分支 --title --body(含查重结果)。相关改动攒一次，不过频。
【4 CI合入】gh pr checks 编号，code/content/quality/security四项全过(quality最后,pending隔10秒再查,别长sleep)→ gh pr merge 编号 --squash --delete-branch → git checkout main && git pull。被挡就 git fetch && git rebase origin/main 后 force-with-lease 重推。
【超时】快盘30s、网络60s；status应秒级，变慢先查盘。
【撞车】以先合入main且更完整版为唯一权威，把你独有增量并进去、删重复件，同一PR完成并记教训库L039。
【完成回报】结论1-3句；查重/撞车处理；PR号+squash hash+main HEAD；文件路径；留我定调点(无则写无)；失败项原因。权威细节见仓库 docs/协作机制/Git快速操作指南_所有对话必读.md。
```

*本指南随实践更新；发现更快方法或新卡点，补到这里让所有明旭共享。*
