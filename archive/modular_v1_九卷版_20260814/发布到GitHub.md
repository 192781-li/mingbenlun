# 发布到 GitHub（一键路径）

本目录已是**本地 git 仓库**，已 `init` 并完成首次提交。由于当前环境 `gh` CLI
未安装、且 GitHub 未鉴权，请按以下步骤把仓库推到云端（你只需做一次）。

## 方式一：用 gh（推荐）
1. 安装 gh：https://cli.github.com/ （Windows 可 `winget install GitHub.cli`）
2. 登录（按提示选 GitHub.com / HTTPS / 浏览器授权）：
   ```
   gh auth login
   ```
3. 在本目录执行（私有仓库）：
   ```
   gh repo create mingbenlun-modular --private --source=. --remote=origin --push
   ```
   公开请改 `--private` 为 `--public`。

## 方式二：用个人访问令牌（PAT）
1. GitHub → Settings → Developer settings → Personal access tokens → 勾选 `repo`
2. 复制令牌后执行：
   ```
   git remote add origin https://<用户名>:<令牌>@github.com/<用户名>/mingbenlun-modular.git
   git branch -M main
   git push -u origin main
   ```
   推送前如需改身份：
   ```
   git config user.email "你的GitHub邮箱"
   git config user.name "你的GitHub用户名"
   ```

## 方式三：飞书云空间（已连接，免鉴权）
若不愿用 GitHub，可将整个 `模块化全本/` 文件夹上传至已连接的**飞书云空间**
做云端共享（保留目录结构与 core/ 代码）。

## 已纳入版本控制的内容
- 九卷模块化文本 + 前辅 + 附录（目录绝对清晰）
- `core/` 高级代码包（**已通过全部 doctest**）
- `00_总纲与用法/`（创作总纲、超越核心总纲、超越对照表、全面洗涤报告）
- `知识库/`（可检索 HTML 浏览器）
- `verify_iron_rule.py`（术语铁律校验器）

## 日常更新
```
git add -A
git commit -m "升华：卷二认识论超越康德框架"
git push
```
