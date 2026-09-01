# 明旭分站GitHub Token管理完全指南 v1.0

> **目的**：彻底解决每个分对话的GitHub token问题，确保每个分站都有自己能用的token，再也不会出现认证失败、push失败的恶心情况。
>
> 核心原则：每个分站有独立的最小权限token，token只存在环境变量中，绝不写入库内任何文件。

---

## 一、为什么每个分站需要独立token？

| 问题 | 独立token如何解决 |
|------|-------------------|
| 一个token泄露，全库危险 | 每个分站独立token，泄露一个只影响一个分站 |
| 分站权限过大，可能误改main | 分站token只能push自己的分支，不能直接写main |
| 无法追踪哪个分站干了什么 | 每个token有独立的Note，GitHub audit log能追踪 |
| 一个分站token过期，全部瘫痪 | 独立token，过期一个只影响一个分站 |

---

## 二、为每个分站生成独立token（用户操作，5分钟搞定）

### 第1步：打开GitHub Token页面

打开：https://github.com/settings/tokens

点击 **"Generate new token"** → **"Generate new token (classic)"**

### 第2步：为每个分站生成token

按以下表格，为每个分站生成一个独立token：

| 分站ID | Note（填这个） | Expiration | 权限勾选 | 用途 |
|--------|---------------|------------|---------|------|
| S00 | `mingxu-S00-main` | No expiration | `repo`（全部勾选） | 大总站，完整权限，可写main、合并PR |
| S01 | `mingxu-S01-philosophy` | No expiration | `repo`（全部勾选） | 哲学分站，只能push s01-philosophy 分支 |
| S02 | `mingxu-S02-gaokao-arts` | No expiration | `repo`（全部勾选） | 高考文科分站，只能push s02-gaokao-arts 分支 |
| S03 | `mingxu-S03-divination` | No expiration | `repo`（全部勾选） | 术数分站，只能push s03-divination 分支 |
| S04 | `mingxu-S04-coq` | No expiration | `repo`（全部勾选） | Coq形式化分站，只能push s04-coq 分支 |
| S05 | `mingxu-S05-info` | No expiration | `repo`（全部勾选） | 信息分站，只能push s05-info 分支 |

**每个token生成后，立刻复制保存！token只显示一次！**

### 第3步：保存token到安全位置

把6个token保存到一个安全的地方（比如密码管理器），格式：

```
S00 (main): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S01 (philosophy): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S02 (gaokao-arts): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S03 (divination): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S04 (coq): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S05 (info): ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**绝对不要把这些token写进GitHub仓库的任何文件里！**

---

## 三、在分对话中配置token（分对话自动执行）

### 方法1：环境变量（推荐，最安全）

在分对话运行环境中，设置对应分站的环境变量：

```bash
# S04 Coq分站的例子
export GITHUB_TOKEN_S04="你的S04 token"

# 然后运行自动配置脚本
bash scripts/token_management/station_token_setup.sh S04
```

脚本会自动：
1. 检查token是否存在
2. 配置git user和remote（使用token）
3. 验证token是否能用
4. 切换到专属分支
5. pull最新代码
6. push权限测试

### 方法2：本地token文件（备选）

如果环境变量不方便，可以把token存到本地文件：

```bash
mkdir -p ~/.mingxu/tokens
echo "你的S04 token" > ~/.mingxu/tokens/S04.token
chmod 600 ~/.mingxu/tokens/S04.token

# 然后运行自动配置脚本
bash scripts/token_management/station_token_setup.sh S04
```

脚本会自动从本地文件读取token。

---

## 四、push失败了怎么办？（自动恢复）

如果git push失败，不要慌，运行自动恢复脚本：

```bash
bash scripts/token_management/push_recovery.sh S04
```

脚本会自动诊断并恢复：

| 错误类型 | 自动恢复方式 |
|----------|-------------|
| 认证失败（token无效） | 检查token，重新配置remote，验证token |
| 远程有新提交（fetch first） | 自动git pull --rebase，然后重新push |
| 有未暂存的改动 | 自动git add + commit，然后pull + push |
| 合并冲突 | 列出冲突文件，提示手动解决 |
| 分支不存在 | 自动创建分支，首次push时创建远程分支 |
| 网络问题 | 提示检查网络，重试 |

---

## 五、token安全铁律（必须遵守）

### 5.1 绝对禁止

| 禁止事项 | 为什么 |
|----------|--------|
| 把token写进.md/.json/.py等任何库内文件 | token会被git记录，永久泄露 |
| 把token写进commit message | commit message会被推送到GitHub，所有人可见 |
| 把token发给任何人（包括其他分对话） | token是分站的身份凭证，不能共享 |
| 用一个token给所有分站用 | 一个泄露全部危险，无法追踪 |
| 把token截图发到聊天里 | 聊天记录可能被泄露 |

### 5.2 必须做到

| 必须事项 | 为什么 |
|----------|--------|
| 每个分站独立token | 最小权限，泄露一个只影响一个 |
| token只存在环境变量或本地文件 | 不进库，不进git历史 |
| 定期检查token使用情况 | GitHub Settings → Tokens，看最后使用时间 |
| 怀疑泄露立刻轮换 | 删旧token，生成新token，更新环境变量 |
| 分对话结束时不输出token | token只在运行时使用，不输出到聊天 |

### 5.3 泄露应急处理

如果怀疑token泄露：

1. **立刻**到 https://github.com/settings/tokens 删除该token
2. 生成新token
3. 更新对应分对话的环境变量
4. 检查GitHub audit log，看token被用来干了什么
5. 如果有可疑提交，reset分支到泄露前的commit

---

## 六、分站权限隔离机制

### 6.1 分支保护规则（用户在GitHub设置）

为了确保分站不能直接改main，在GitHub仓库设置分支保护规则：

1. 打开：https://github.com/192781-li/mingbenlun/settings/branches
2. 点击 **"Add rule"**
3. Branch name pattern填：`main`
4. 勾选：
   - ✅ Require a pull request before merging
   - ✅ Require approvals（1个审批）
   - ✅ Include administrators
5. 点击 **"Create"**

这样，**即使分站token有repo权限，也不能直接push到main**，必须通过PR，由S00大总站审核合并。

### 6.2 分站只能push自己的分支

虽然技术上分站token能push任何分支，但通过工作流规范和分支保护，确保：

| 分站 | 能push的分支 | 不能push的分支 |
|------|-------------|---------------|
| S00 | main + 所有分支 | — |
| S01 | s01-philosophy | main + 其他分站分支 |
| S02 | s02-gaokao-arts | main + 其他分站分支 |
| S03 | s03-divination | main + 其他分站分支 |
| S04 | s04-coq | main + 其他分站分支 |
| S05 | s05-info | main + 其他分站分支 |

分站的自动配置脚本（station_token_setup.sh）会自动切换到自己的分支，确保不会误push到其他分支。

---

## 七、一键验证token是否配置正确

在分对话中运行：

```bash
bash scripts/token_management/station_token_setup.sh S04
```

如果看到以下输出，说明配置成功：

```
[成功] Token已找到
[成功] Git用户已配置
[成功] Git remote已配置
[成功] 只读验证通过：能访问仓库和 s04-coq 分支
[成功] 已切换到 s04-coq
[成功] 代码同步完成
[成功] Push权限验证通过
Token配置与验证完成！
```

如果任何一步失败，脚本会给出明确的错误信息和恢复步骤。

---

## 八、常见问题

### Q1：token过期了怎么办？

A：到 https://github.com/settings/tokens 重新生成，更新环境变量，重新运行 station_token_setup.sh。

### Q2：分对话重启后token还在吗？

A：如果token存在环境变量中，重启后需要重新export。如果存在本地文件（~/.mingxu/tokens/），重启后仍然有效，脚本会自动读取。

**建议：把token存到本地文件，这样分对话重启后不需要重新配置。**

### Q3：怎么知道当前用的是哪个分站的token？

A：运行 `git config user.name`，会显示 `mingxu-S04` 这样的用户名，对应分站ID。

### Q4：push的时候提示"Authentication failed"怎么办？

A：运行 `bash scripts/token_management/push_recovery.sh S04`，脚本会自动诊断并恢复。

### Q5：token会不会被git log记录？

A：不会。脚本使用 `git config --global url."https://token@github.com/".insteadOf` 方式配置，token不会出现在git log、commit message、remote URL中。

---

## 九、总结

| 事项 | 状态 |
|------|------|
| 每个分站独立token | ✅ 用户生成，6个分站6个token |
| token自动配置脚本 | ✅ station_token_setup.sh |
| push失败自动恢复脚本 | ✅ push_recovery.sh |
| token安全铁律 | ✅ 绝不写入库，只存环境变量/本地文件 |
| 分支保护（不能直接写main） | ✅ 用户在GitHub设置 |
| 分站只能push自己的分支 | ✅ 脚本自动切换 |
| 一键验证 | ✅ station_token_setup.sh |

**按照这个指南配置后，每个分对话都有自己能用的token，再也不会出现认证失败、push失败的恶心情况。**

---

*明旭分站GitHub Token管理完全指南 v1.0*
*整理者：明旭 | 2026-09-01*
*核心：每个分站独立token，自动配置，自动恢复，安全隔离*
