# S00 大总站 · 夜间巡检 SOP

> 本文件是 S00 夜间巡检定时任务（每天 23:00）的执行标准。
> 任务触发后：先 `git checkout main && git pull origin main`，再读本文件，按步骤执行。
> 修改巡检流程只改本文件，无需改 cron prompt。

## 0. 身份与边界

- 你是 S00 大总站（明旭本体），管总协调、跨分站文档、定时任务注册、冲突裁决。
- **不碰** Coq `.v` 证明代码（S04 管）、不碰哲学研判正文（S01 管）。
- 库是唯一权威，旧记忆与库冲突以库为准。
- 绝对不说"完美"。

## 1. 记忆恢复

```bash
cd /home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun
git checkout main
git pull origin main
```

读以下文件恢复上下文（按需，不必全读）：
- `docs/协作机制/分站/S00_大总站_身份档案.md`
- `docs/协作机制/明旭的记忆/定时任务网络配置.json`
- `docs/协作机制/明旭的记忆/明旭_运行状态机.md`

## 2. 一键巡检（核心，用 s00_patrol.py）

```bash
python3 scripts/s00_patrol.py all
```

这一条命令完成：
- **report**：生成结构化巡检报告到 `docs/协作机制/巡检报告/YYYYMMDD_HHMM_巡检报告.md`
  - 分站分支领先/落后
  - 结晶库编号连续 + 跨分支同号异义
  - 定时任务注册表内部一致
  - 分站档案完整性
  - 未合并 PR / 最近 CI 运行
  - 工作区未提交改动
  - 关键目录文件数
- **sync**：列出各分支 main 缺失的共享文档（白名单：智慧河流/分站通道/S01给S04/哲学研究/高考数学）

## 3. 定时任务平台对账（防 L037 复发——快照是唯一权威）

夜间巡检是唯一能接触 cron 平台的时机，必须导出最新快照覆盖旧快照：

1. 用 `list_cron_jobs`（enable=true/false 各一次）取平台真实 10 个任务
2. 直接覆盖写入 `docs/协作机制/明旭的记忆/平台快照_latest.json`（这是库内定时任务状态的唯一权威，注册表 v3.0 不再存 cron_jobs/stopped_jobs 副本）
3. 跑校验：
   ```bash
   python3 scripts/network_reconcile.py --only registry
   ```
4. 如果新导出的快照与旧快照有差异（任务增删/状态变更），在巡检报告里记录差异

发现漂移（幽灵 ID/状态不符/漏登）时：
- 以平台为唯一权威，快照即真相，无需再回写注册表
- 记录到 `docs/协作机制/教训库.md`（如果是新类型的漂移）

## 4. 共享文档同步（只增不删不改）

如果 `s00_patrol.py sync` 列出了 main 缺失的共享文档：

```bash
python3 scripts/s00_patrol.py sync --apply
```

- 只添加白名单内 main 没有的文件
- **不删除、不覆盖、不自动合并** append-only 文件（河流/结晶的合并走 `river_sync.sh pull`）
- 同步后 review 内容，确认无误再 commit

## 5. 分站分支积压自动同步（防堆积——s00_sync_branches.py）

```bash
python3 scripts/s00_sync_branches.py --apply --auto-merge
```

自动检测各分站分支领先 main 的独有产出并同步：
- **四层过滤**：白名单目录自动同步（智慧河流/分站通道/哲学研究/高考数学/文科学习/术数研究/巡检报告）/ 排除目录（`mingben-workbench/`、`site/`、`archive/` 等分站工作目录和 CI 产物）/ 排除模式（`.v`/`.vo` 等 Coq 代码）/ 基础配置默认排除（需 `--include-config` 才同步）
- **只增不覆盖**：只同步 main 上没有的新增文件，不覆盖已有文件
- `--apply` 实际同步并开 PR，`--auto-merge` CI 通过后自动合并（带时序重试和分支落后自动追平，最多追平 2 次）
- 同步的文件清单会在巡检报告里列出
- 如遇 merge 冲突或 auto-merge 失败，不强行 push，记录到巡检报告待用户处理

## 6. 结晶与分支深度对账（可选，有异常时跑）

```bash
python3 scripts/network_reconcile.py --fetch
```

- 结晶跨分支同号异义：已裁决的标"待同步"，未裁决的必须处理（分支改用临时号，合 main 由 S00 发正式号）
- 分支领先超过 10：评估是否有共享文档需要集成

## 7. 任务队列清理

- 检查 `定时任务网络配置.json` 的 `task_queue`
- 已完成的任务标 `completed`（加 `completed_at` 和 `resolution`）
- 长期 pending 的任务评估是否仍有效
- **不擅自启动/停止分站定时任务**（S04 看板、S06 任务的恢复需用户或对应分站决定）

## 7.5 统一提交智慧对账（防 L037 复发——对账的对账）

按 `docs/协作机制/统一提交处理智慧_v1.0.md` 第四层，检查各站今日提交总结质量：

1. 各分站 `S0X_signal.json` 的 `last_update` 是否是今天？不是=该站今天没跑或没回写，记录到巡检报告。
2. 各站 signal 的 `self_review` 是否非空？是空的=闭环短路嫌疑，标注。
3. 各站 `needs_other` 是否有未被响应的跨站需求？有则在巡检报告里提醒对应分站。
4. 河流主干今天是否有各站的 append？没有=该站今天没沉积。

发现系统性问题（连续 2 天以上某站不回写/不沉积）→ 记录到教训库，评估是否需要调整该站定时任务或运行指令。

## 8. 产出与提交

1. 巡检报告已由 `s00_patrol.py report` 生成在 `docs/协作机制/巡检报告/`
2. 如有对账修正、同步文档、任务队列更新，全部 commit：
   ```bash
   git add -A
   git commit -m "S00夜间巡检 YYYYMMDD：巡检报告+对账修正+共享文档同步"
   ```
3. **main 受保护，必须走 PR**：
   ```bash
   git checkout -b s00-nightly-YYYYMMDD
   git push -u origin s00-nightly-YYYYMMDD
   gh pr create --base main --head s00-nightly-YYYYMMDD --title "S00夜间巡检 YYYYMMDD"
   # 等 CI 通过后 gh pr merge --merge --delete-branch
   ```
4. 无改动时跳过 commit，直接结束。

## 9. 异常处理

- **git 冲突**：不强行 push，记录冲突待用户处理
- **CI 失败**：看失败日志，是本次改动导致的就修，是既有问题就记录到教训库
- **平台对账发现大漂移**（超过 3 处）：不要批量自动改，先记录，等用户确认
- **结晶同号异义未裁决**：不自动合并，在巡检报告里标注，等 S00/用户裁决

## 10. 结束前自检

- [ ] 巡检报告已生成
- [ ] 平台对账已做（如有漂移已回写注册表）
- [ ] 共享文档缺失已同步（或确认无缺失）
- [ ] 分站分支积压已自动同步（或确认无积压）
- [ ] 任务队列已清理
- [ ] 改动已 commit 并走 PR（或确认无改动）
- [ ] 未碰 Coq `.v`、未碰哲学研判正文
