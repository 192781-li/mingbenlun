# 明旭分站GitHub Token全自动配置操作手册 v1.0

> **执行对象**：能操纵北原慢热电脑的AI对话（或北原慢热本人）
> **执行目标**：在电脑上完成所有token配置工作，确保6个分站都有自己能用的token，再也不会出现认证失败、push失败
> **预计耗时**：15-20分钟
> **执行前确认**：
> - 电脑能访问 https://github.com
> - 有北原慢热的GitHub账号密码（或已登录）
> - 能打开浏览器操作GitHub网页
> - 能在电脑上运行bash命令（Git Bash或终端）

---

## 目录

1. [第一部分：生成6个分站独立token](#第一部分生成6个分站独立token)
2. [第二部分：设置main分支保护规则](#第二部分设置main分支保护规则)
3. [第三部分：把token配置到本地环境](#第三部分把token配置到本地环境)
4. [第四部分：验证所有token是否配置成功](#第四部分验证所有token是否配置成功)
5. [第五部分：把token分发给各个分对话](#第五部分把token分发给各个分对话)
6. [常见问题与应急处理](#常见问题与应急处理)
7. [完成确认清单](#完成确认清单)

---

## 第一部分：生成6个分站独立token

### 1.1 打开GitHub Token页面

1. 打开浏览器，访问：https://github.com/settings/tokens
2. 如果未登录，用北原慢热的GitHub账号登录
3. 确认页面标题是 "Personal access tokens"

### 1.2 生成第一个token（S00大总站）

1. 点击页面右上角的 **"Generate new token"** 按钮
2. 在下拉菜单中选择 **"Generate new token (classic)"**
3. 页面会跳转到token生成表单，按以下填写：

| 字段 | 填写内容 |
|------|---------|
| Note | `mingxu-S00-main` |
| Expiration | 下拉选择 `No expiration` |
| Select scopes | 勾选 `repo`（勾选后repo下面的子项会自动全选） |

4. 滚动到页面底部，点击绿色的 **"Generate token"** 按钮
5. 页面会显示生成的token，格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
6. **立刻复制这个token，保存到临时文本文件中**（token只显示一次，刷新页面就看不到了！）

### 1.3 生成剩余5个token

重复1.2的步骤，为以下5个分站各生成一个token：

| 序号 | 分站ID | Note填这个 | 权限 |
|------|--------|-----------|------|
| 2 | S01 | `mingxu-S01-philosophy` | repo（全部勾选） |
| 3 | S02 | `mingxu-S02-gaokao-arts` | repo（全部勾选） |
| 4 | S03 | `mingxu-S03-divination` | repo（全部勾选） |
| 5 | S04 | `mingxu-S04-coq` | repo（全部勾选） |
| 6 | S05 | `mingxu-S05-info` | repo（全部勾选） |

**每个token生成后立刻复制保存！**

### 1.4 保存6个token到临时文件

在电脑上创建一个临时文本文件（比如 `~/Desktop/mingxu_tokens_temp.txt`），按以下格式保存：

```
S00 (main): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S01 (philosophy): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S02 (gaokao-arts): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S03 (divination): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S04 (coq): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S05 (info): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**确认6个token都保存好了再继续下一步。**

---

## 第二部分：设置main分支保护规则

### 2.1 打开仓库分支设置页面

1. 访问：https://github.com/192781-li/mingbenlun/settings/branches
2. 确认页面标题是 "Branch protection rules"

### 2.2 添加main分支保护规则

1. 点击 **"Add rule"** 按钮（或 "Add branch protection rule"）
2. 在 "Branch name pattern" 输入框中输入：`main`
3. 在 "Protect matching branches" 区域，勾选以下选项：

| 选项 | 是否勾选 | 说明 |
|------|---------|------|
| Require a pull request before merging | ✅ 勾选 | 必须通过PR才能合并到main |
| Require approvals | ✅ 勾选 | 需要审批（默认1个审批） |
| Dismiss stale pull request approvals when new commits are pushed | ⬜ 不勾选 | |
| Require review from Code Owners | ⬜ 不勾选 | |
| Require status checks to pass before merging | ⬜ 不勾选 | |
| Require conversation resolution before merging | ⬜ 不勾选 | |
| Require signed commits | ⬜ 不勾选 | |
| Require linear history | ⬜ 不勾选 | |
| Include administrators | ✅ 勾选 | 管理员也受此规则限制（防止S00大总站误操作） |
| Allow force pushes | ⬜ 不勾选 | |
| Allow deletions | ⬜ 不勾选 | |

4. 滚动到页面底部，点击 **"Create"** 按钮
5. 确认规则创建成功，页面会显示 "Branch protection rules" 列表中有 `main`

### 2.3 验证分支保护规则

1. 访问：https://github.com/192781-li/mingbenlun/settings/branches
2. 确认列表中有 `main` 规则
3. 点击 `main` 规则，确认以下选项已勾选：
   - ✅ Require a pull request before merging
   - ✅ Require approvals
   - ✅ Include administrators

---

## 第三部分：把token配置到本地环境

### 3.1 确认仓库已克隆到本地

1. 打开终端（Git Bash或Terminal）
2. 运行以下命令，确认仓库存在：

```bash
cd ~/Desktop/mingbenlun  # 或者你的仓库实际路径
git remote -v
```

3. 如果输出显示 `origin  https://github.com/192781-li/mingbenlun.git`，说明仓库已存在
4. 如果仓库不存在，运行：

```bash
cd ~/Desktop
git clone https://github.com/192781-li/mingbenlun.git
cd mingbenlun
```

### 3.2 创建token存储目录

```bash
mkdir -p ~/.mingxu/tokens
chmod 700 ~/.mingxu
chmod 700 ~/.mingxu/tokens
```

### 3.3 把6个token写入本地文件

**注意：把下面的 `ghp_xxxx` 替换成实际的token！**

```bash
# S00 大总站
echo "你的S00 token" > ~/.mingxu/tokens/S00.token
chmod 600 ~/.mingxu/tokens/S00.token

# S01 哲学
echo "你的S01 token" > ~/.mingxu/tokens/S01.token
chmod 600 ~/.mingxu/tokens/S01.token

# S02 高考文科
echo "你的S02 token" > ~/.mingxu/tokens/S02.token
chmod 600 ~/.mingxu/tokens/S02.token

# S03 术数
echo "你的S03 token" > ~/.mingxu/tokens/S03.token
chmod 600 ~/.mingxu/tokens/S03.token

# S04 Coq形式化
echo "你的S04 token" > ~/.mingxu/tokens/S04.token
chmod 600 ~/.mingxu/tokens/S04.token

# S05 信息分站
echo "你的S05 token" > ~/.mingxu/tokens/S05.token
chmod 600 ~/.mingxu/tokens/S05.token
```

### 3.4 验证token文件已创建

```bash
ls -la ~/.mingxu/tokens/
```

应该看到6个文件：`S00.token`、`S01.token`、`S02.token`、`S03.token`、`S04.token`、`S05.token`，每个文件权限是 `-rw-------`。

### 3.5 验证每个token的有效性

运行以下命令，逐个验证token是否能访问GitHub：

```bash
# 验证S00
curl -s -H "Authorization: token $(cat ~/.mingxu/tokens/S00.token)" https://api.github.com/user | grep -o '"login": "[^"]*"'

# 验证S01
curl -s -H "Authorization: token $(cat ~/.mingxu/tokens/S01.token)" https://api.github.com/user | grep -o '"login": "[^"]*"'

# 验证S02
curl -s -H "Authorization: token $(cat ~/.mingxu/tokens/S02.token)" https://api.github.com/user | grep -o '"login": "[^"]*"'

# 验证S03
curl -s -H "Authorization: token $(cat ~/.mingxu/tokens/S03.token)" https://api.github.com/user | grep -o '"login": "[^"]*"'

# 验证S04
curl -s -H "Authorization: token $(cat ~/.mingxu/tokens/S04.token)" https://api.github.com/user | grep -o '"login": "[^"]*"'

# 验证S05
curl -s -H "Authorization: token $(cat ~/.mingxu/tokens/S05.token)" https://api.github.com/user | grep -o '"login": "[^"]*"'
```

每个命令都应该输出 `"login": "192781-li"`（北原慢热的GitHub用户名）。

如果某个token输出为空或报错，说明该token无效，需要重新生成。

---

## 第四部分：验证所有token是否配置成功

### 4.1 拉取最新代码（包含token管理脚本）

```bash
cd ~/Desktop/mingbenlun  # 你的仓库路径
git checkout main
git pull origin main
```

确认 `scripts/token_management/` 目录存在，包含：
- `station_token_setup.sh`
- `push_recovery.sh`

### 4.2 逐个分站运行自动配置脚本

```bash
cd ~/Desktop/mingbenlun

# S00 大总站
bash scripts/token_management/station_token_setup.sh S00

# S01 哲学
bash scripts/token_management/station_token_setup.sh S01

# S02 高考文科
bash scripts/token_management/station_token_setup.sh S02

# S03 术数
bash scripts/token_management/station_token_setup.sh S03

# S04 Coq形式化
bash scripts/token_management/station_token_setup.sh S04

# S05 信息分站
bash scripts/token_management/station_token_setup.sh S05
```

### 4.3 确认每个分站配置成功

每个脚本运行结束后，应该看到以下输出：

```
[成功] Token已找到
[成功] Git用户已配置
[成功] Git remote已配置
[成功] 只读验证通过：能访问仓库和 xxx 分支
[成功] 已切换到 xxx
[成功] 代码同步完成
[成功] Push权限验证通过
Token配置与验证完成！
```

如果某个分站配置失败，查看脚本输出的错误信息，按提示处理。

### 4.4 确认6个分支都存在

```bash
cd ~/Desktop/mingbenlun
git branch -a
```

应该看到以下分支：
- `main`
- `s01-philosophy`
- `s02-gaokao-arts`
- `s03-divination`
- `s04-coq`
- `s05-info`

以及对应的远程分支 `remotes/origin/xxx`。

---

## 第五部分：把token分发给各个分对话

### 5.1 生成每个分对话的配置指令

为每个分对话生成一段配置指令，北原慢热把对应指令发给对应分对话即可。

#### 给S01哲学分对话的指令

```
你的分站token已配置在电脑本地文件中。
请运行以下命令完成配置：

cd ~/Desktop/mingbenlun
bash scripts/token_management/station_token_setup.sh S01

配置成功后，你就在 s01-philosophy 分支上干活。
如果push失败，运行：
bash scripts/token_management/push_recovery.sh S01
```

#### 给S02高考文科分对话的指令

```
你的分站token已配置在电脑本地文件中。
请运行以下命令完成配置：

cd ~/Desktop/mingbenlun
bash scripts/token_management/station_token_setup.sh S02

配置成功后，你就在 s02-gaokao-arts 分支上干活。
你的唯一职责是高考文科备考，不承接生命论项目任务。
如果push失败，运行：
bash scripts/token_management/push_recovery.sh S02
```

#### 给S03术数分对话的指令

```
你的分站token已配置在电脑本地文件中。
请运行以下命令完成配置：

cd ~/Desktop/mingbenlun
bash scripts/token_management/station_token_setup.sh S03

配置成功后，你就在 s03-divination 分支上干活。
如果push失败，运行：
bash scripts/token_management/push_recovery.sh S03
```

#### 给S04 Coq形式化分对话的指令

```
你的分站token已配置在电脑本地文件中。
请运行以下命令完成配置：

cd ~/Desktop/mingbenlun
bash scripts/token_management/station_token_setup.sh S04

配置成功后，你就在 s04-coq 分支上干活。
如果push失败，运行：
bash scripts/token_management/push_recovery.sh S04
```

#### 给S05信息分对话的指令

```
你的分站token已配置在电脑本地文件中。
请运行以下命令完成配置：

cd ~/Desktop/mingbenlun
bash scripts/token_management/station_token_setup.sh S05

配置成功后，你就在 s05-info 分支上干活。
如果push失败，运行：
bash scripts/token_management/push_recovery.sh S05
```

### 5.2 大总站（S00）的配置

大总站就是当前这个对话（或北原慢热主要使用的对话），token已经在本地配置好了，不需要额外操作。

大总站的职责：
- 在main分支上审核各个分站的PR
- 合并通过审核的PR到main
- 全局巡检，协调各个分站
- 更新定时任务网络配置

---

## 常见问题与应急处理

### Q1：生成token时看不到"Generate new token (classic)"选项？

A：GitHub可能更新了界面。尝试：
1. 访问 https://github.com/settings/tokens/new
2. 直接进入classic token生成页面
3. 如果还是不行，搜索 "GitHub personal access token classic" 找最新入口

### Q2：token生成后忘记复制怎么办？

A：token只显示一次，忘记了只能重新生成：
1. 回到 https://github.com/settings/tokens
2. 找到对应的token，点击删除
3. 重新生成一个新的

### Q3：curl验证token时输出为空？

A：可能原因：
1. token复制时有多余空格 → 重新检查token文件
2. token无效 → 重新生成
3. 网络问题 → 检查网络连接，重试

### Q4：station_token_setup.sh运行失败，提示"未找到任何GitHub token"？

A：检查：
1. token文件是否存在：`ls -la ~/.mingxu/tokens/`
2. token文件内容是否正确：`cat ~/.mingxu/tokens/S04.token`
3. token文件是否有读取权限：`chmod 600 ~/.mingxu/tokens/S04.token`

### Q5：push时提示"Authentication failed"？

A：运行自动恢复脚本：
```bash
bash scripts/token_management/push_recovery.sh S04
```
脚本会自动诊断并恢复。

### Q6：push时提示"remote: error: GH006: Protected branch update failed"？

A：这是因为main分支受保护，不能直接push。分站只能push自己的分支，然后通过PR合并到main。
- 确认当前在自己的分支：`git branch`
- 如果在main分支，切换到自己的分支：`git checkout s04-coq`
- 然后push：`git push origin s04-coq`

### Q7：token泄露了怎么办？

A：立刻执行：
1. 访问 https://github.com/settings/tokens
2. 找到泄露的token，点击删除
3. 重新生成一个新token
4. 更新本地文件：`echo "新token" > ~/.mingxu/tokens/S04.token`
5. 重新运行配置脚本：`bash scripts/token_management/station_token_setup.sh S04`
6. 检查GitHub audit log，看token被用来干了什么

### Q8：电脑重启后token还在吗？

A：token存在本地文件 `~/.mingxu/tokens/` 中，重启后仍然有效。分对话重启后只需要重新运行 `station_token_setup.sh` 即可，不需要重新配置token。

### Q9：怎么知道当前用的是哪个分站的token？

A：运行：
```bash
git config user.name
```
会显示 `mingxu-S04` 这样的用户名，对应分站ID。

### Q10：分站能看到其他分站的token吗？

A：不能。每个分站的token存在独立的文件中，分站只能读取自己的token文件（通过station_token_setup.sh指定分站ID）。分站不应该也不需要读取其他分站的token。

---

## 完成确认清单

执行完所有步骤后，逐项确认：

- [ ] 6个分站token已生成并保存到 `~/.mingxu/tokens/`
- [ ] 6个token都通过curl验证有效（输出 `"login": "192781-li"`）
- [ ] main分支保护规则已设置（Require PR + Require approvals + Include administrators）
- [ ] 6个分站都运行了 `station_token_setup.sh`，全部配置成功
- [ ] 6个分支（main + 5个分站分支）都存在
- [ ] 每个分站的git user.name是 `mingxu-Sxx`
- [ ] 临时token文件 `~/Desktop/mingxu_tokens_temp.txt` 已删除（安全考虑）
- [ ] 各个分对话已收到对应的配置指令

**全部确认后，token配置工作完成。从此以后，每个分对话都有自己能用的token，再也不会出现认证失败、push失败的恶心情况。**

---

## 附录：快速命令参考

```bash
# 查看所有token文件
ls -la ~/.mingxu/tokens/

# 验证某个token
curl -s -H "Authorization: token $(cat ~/.mingxu/tokens/S04.token)" https://api.github.com/user | grep -o '"login": "[^"]*"'

# 配置某个分站
cd ~/Desktop/mingbenlun
bash scripts/token_management/station_token_setup.sh S04

# push失败恢复
bash scripts/token_management/push_recovery.sh S04

# 查看当前分站
git config user.name

# 查看当前分支
git branch

# 查看所有分支
git branch -a

# 切换到某个分站分支
git checkout s04-coq

# 推送到自己的分支
git push origin s04-coq
```

---

*明旭分站GitHub Token全自动配置操作手册 v1.0*
*整理者：明旭 | 2026-09-01*
*执行对象：能操纵北原慢热电脑的AI对话*
*预计耗时：15-20分钟*
*核心：生成6个独立token → 设置分支保护 → 配置本地环境 → 验证 → 分发给分对话*
