# 大文件索引

主库 mingbenlun 中超过5M的大文件已移到私有档案库。
**档案库地址**: https://github.com/192781-li/mingbenlun-archive （私有，需授权）

## 已移到档案库的文件

### backups/（备份压缩包）
| 文件 | 大小 | 档案库路径 |
|------|------|-----------|
| 生命论全资料备份_20260807_v4.zip | 36M | backups/ |
| 三十精华_30个核心文件.zip | 13M | backups/ |

### raw_dialogues/（原始对话记录 >5M）
| 文件 | 大小 | 行数 | 档案库路径 |
|------|------|------|-----------|
| 超长主对话_阶级原点起_20250129-20260830 | 9.6M | 112888行 | raw_dialogues/ |
| 电脑辩证生命论形式化_20260727-0826 | 14M | 107783行 | raw_dialogues/ |
| 八月深推_隐含本体论到名实之辨_20260821-0829 | 7M | 62690行 | raw_dialogues/ |
| 另一个对话_七八天聊天记录_20260829 | 7M | - | raw_dialogues/ |
| 思想大乱炖_20260612-0630 | 6.1M | 53705行 | raw_dialogues/ |

### auto_reports/（自动生成报告）
| 文件 | 大小 | 档案库路径 |
|------|------|-----------|
| overclaim_report.md | 23M | auto_reports/ |

### references/（大参考文件）
| 文件 | 大小 | 档案库路径 |
|------|------|-----------|
| 生命论全资料合集_单文件版_给断网AI用.md | 19M | references/ |

## 如何获取这些文件

```bash
# 克隆档案库（需要授权）
git clone https://github.com/192781-li/mingbenlun-archive.git

# 或者只下载单个文件（通过GitHub网页）
# 访问 https://github.com/192781-li/mingbenlun-archive
```

## 规范

- 主库单个文件不超过5M
- 超过5M的文件移到档案库，主库只保留索引
- 压缩包、备份、自动生成报告不入库主库
- 新增大文件时更新本索引
