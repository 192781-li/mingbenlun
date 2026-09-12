# 双重监控

明性不仅照自己，也照工作环境。监控是明性的延伸。

## 工作区监控

- 磁盘空间（低于15%告警）
- git未提交变更
- 最近1小时修改的文件
- manifest完整性（所有模块文件存在）
- 合并文件大小（异常小=构建失败）
- 输出目录文件数

脚本：`python3 scripts/monitor.py`

## 后台监控

- xelatex/pandoc/build进程状态
- xelatex卡住检测（运行超过10分钟）
- 临时文件堆积（/tmp下pdf_*、.aux、.log）

脚本：`python3 scripts/monitor.py --background`

## 持续监控

```bash
python3 scripts/monitor.py --background --watch 300  # 每5分钟刷新
```

## 已知风险点

1. **.user_skills目录会被环境重置**：技能文件可能丢失，必须纳入git远程备份
2. **build.sh合并文件偶发异常变大（2MB）**：删除`生命论合订本_最新.md`重新build即可
3. **xelatex编译大文件需5-10分钟**：用后台运行+TaskOutput等待，不要前台阻塞
4. **smart_merge.py的篇/卷合并未充分测试**：使用前先--dry-run
