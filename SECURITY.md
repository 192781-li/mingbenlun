# 安全政策

## 支持的版本

| 版本 | 支持状态 |
|---|---|
| v1.1.x | ✅ 当前版本 |
| v1.0.x | ⚠️ 仅安全修复 |
| < v1.0 | ❌ 不再支持 |

## 报告安全漏洞

如果你发现了安全漏洞（包括但不限于）：

- Token / 密钥泄露
- 恶意代码注入
- 依赖库漏洞
- CI/CD 配置缺陷

请**不要**公开创建Issue，而是通过以下方式联系：

1. 在GitHub上创建[Security Advisory](https://github.com/192781-li/mingbenlun/security/advisories)
2. 或直接联系仓库所有者

## 我们的承诺

- 收到报告后24小时内确认
- 48小时内开始调查
- 修复后公开致谢（如报告者同意）

## Token安全

- 所有分站token存储在本地 `~/.mingxu/tokens/`，**绝不写入库内**
- CI通过GitHub Secrets获取token，不硬编码
- 如发现token泄露，立即轮换：GitHub → Settings → Developer settings → Personal access tokens

## 依赖安全

- Python依赖通过`requirements.txt`管理
- Dependabot自动监控依赖更新
- 关键依赖变更需人工审核
