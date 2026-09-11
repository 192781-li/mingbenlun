# Git 快速操作指南（所有对话/分站必读）

> 建立：2026-09-11，S00大总站
> 用途：让任何新对话、任何分站读完即掌握快速 git 操作，避免"git 命令卡死"的误判和时间浪费。

---

## 一、一句话根因

**git 命令不是卡死，是仓库所在文件系统慢。**

mingbenlun 仓库在不同文件系统上的速度差 200-2000 倍：

| 文件系统 | 路径 | stat 1559个文件 | git status |
|---------|------|----------------|-----------|
| **hpvs_fs（快，用这个）** | `/home/user` | 0.064秒 | **0.9秒** |
| overlay | `/tmp` | 0.013秒 | — |
| virtiofs（慢，避开） | `/sandboxdata/workspace` | 17秒 | **30秒跑不完** |

virtiofs 是虚拟机共享文件系统，git status 要对每个 tracked 文件做 stat，共享盘上 stat 极慢。只给 5-10 秒 timeout 就会误判为"卡死"。

---

## 二、路径选择（铁律）

### 日常 git 操作用快速仓库
```
/home/user/mingbenlun
```

### 慢速路径只在必要时参考（不删，其他任务可能在用）
```
/sandboxdata/workspace/file/mingbenlun
```

### 判断当前路径在哪个文件系统
```bash
df -T .
# 看到 virtiofs = 慢盘，立即换到 /home/user/mingbenlun
# 看到 hpvs_fs / overlay = 快盘，可以直接操作
```

### 快速仓库不存在时，一次性建立
```bash
git clone --depth 50 https://github.com/192781-li/mingbenlun.git /home/user/mingbenlun
cd /home/user/mingbenlun
git config user.name "192781-li"
git config user.email "192781-li@users.noreply.github.com"
git config core.preloadindex true
```
（需要完整历史时：`git fetch --unshallow`）

---

## 三、标准操作流程

### 每次开工前（保持最新）
```bash
cd /home/user/mingbenlun
git checkout main
git pull origin main
```

### 提交改动（main 受保护，走 PR）
```bash
git add <文件>
git commit -m "分站: 具体改动说明"
git checkout -b <分支名>
git push -u origin <分支名>
gh pr create --base main --head <分支名> --title "标题" --body "说明"
```

### 等 CI 合并
```bash
# CI 通过后等 8-10 秒（GitHub 状态同步延迟），再 merge
gh pr merge <PR号> --merge --delete-branch
# 如被其他 PR 挡住（head not up to date）：
git merge origin/main && git push   # 追平后重等 CI
```

---

## 四、timeout 规范

- 快盘（/home/user）：git 命令 timeout 设 **30 秒**足够
- 慢盘（virtiofs）：git status 类命令需要 **60 秒以上**，且应优先换盘而非等待
- git push/pull（走网络）：timeout 设 **60 秒**

---

## 五、速度实测参考（2026-09-11，快盘）

| 操作 | 耗时 |
|------|------|
| git status | 0.9秒 |
| git add | 0.16秒 |
| git commit | 0.3秒 |
| git push | 2.5秒 |
| git pull | 1-3秒 |

如果你的操作明显比这个慢，先 `df -T .` 检查是不是跑到了 virtiofs 慢盘。

---

## 六、排查"git 卡住"的顺序

1. `df -T .` → 是 virtiofs 就换 `/home/user/mingbenlun`，问题直接消失
2. 检查锁文件：`ls .git/*.lock`（有锁说明上次 git 被强杀，删 lock 前先确认无 git 进程）
3. 检查残留进程：`ps aux | grep git`
4. 基础命令测试：`git rev-parse HEAD`（不需要遍历工作区，秒回 = git 本身没坏，问题在文件扫描）
5. 定位卡点：`git status --untracked-files=no`（还慢 = tracked 文件 stat 慢，即文件系统问题）

---

## 七、核心纪律

1. **先选对盘，再操作**——不在 virtiofs 上做日常 git
2. **git 慢 ≠ git 坏**——先怀疑文件系统，再怀疑 git
3. **main 走 PR，不直接 push**
4. **操作不过频**——逻辑相关的改动攒一次 commit、一次 push
5. **每步操作前确认路径**：`pwd` 必须在 `/home/user/mingbenlun`

---

*本指南随实践更新。发现更快的方法或新的卡点，补充到这里，让所有明旭共享。*
