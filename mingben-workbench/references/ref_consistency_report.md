# 引用一致性检查报告

扫描目录: `C:\Users\lison\Desktop\mingbenlun_fresh\mingben-workbench\references`

注册表: `C:\Users\lison\Desktop\mingbenlun_fresh\mingben-workbench\references\theorem_registry.json`

生成时间: 2026-08-26

## 统计概览

| 类别 | 数量 |
|------|------|
| 注册表中定理ID | 18 |
| 永久ID引用(T001格式) | 11 |
| 无效ID引用 | 1 |
| 旧格式引用(定理X) | 1660 |
| **发现问题** | **1661** |

## 严重程度分布

- 错误 (error): 1
- 警告 (warning): 0
- 信息 (info): 1660

## 定理状态分布

- conjecture: 1
- paper_proof: 17

## 新颖性分布

- new_application: 4
- new_interpretation: 5
- new_proof: 2
- new_theorem: 7

## Coq验证状态

- 已Coq验证: 0/18
- 未验证: 18

## 文献核查状态

- 已查文献: 6/18
- 未核查: 12

## 错误（必须修复）

### E001 [invalid_id] 版本号规范化体系.md:53

**问题**: 引用了不存在的定理ID "T999"。请检查拼写或在注册表中添加。

**上下文**: `- **范围**: T001-T999（足够用）`


## 信息（建议改进，共1660条）

旧格式引用（定理X/公理X等）建议逐步改为永久ID（T001格式）。

1. [old_ref] enactics_v0.1.md:89 — 使用可变编号 "定义2.1"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
2. [old_ref] enactics_v0.1.md:108 — 使用可变编号 "定义2.2"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
3. [old_ref] enactics_v0.1.md:114 — 使用可变编号 "定理2.1"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
4. [old_ref] enactics_v0.1.md:122 — 使用可变编号 "定义2.3"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
5. [old_ref] enactics_v0.1.md:126 — 使用可变编号 "定理2.2"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
6. [old_ref] enactics_v0.1.md:136 — 使用可变编号 "定义2.4"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
7. [old_ref] enactics_v0.1.md:145 — 使用可变编号 "定理2.3"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
8. [old_ref] enactics_v0.1.md:157 — 使用可变编号 "定义3.1"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
9. [old_ref] enactics_v0.1.md:172 — 使用可变编号 "定义3.2"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
10. [old_ref] enactics_v0.1.md:176 — 使用可变编号 "定理3.1"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
11. [old_ref] enactics_v0.1.md:178 — 使用可变编号 "定义3.1"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
12. [old_ref] enactics_v0.1.md:196 — 使用可变编号 "定义4.1"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
13. [old_ref] enactics_v0.1.md:198 — 使用可变编号 "定义4.2"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
14. [old_ref] enactics_v0.1.md:206 — 使用可变编号 "定理4.1"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
15. [old_ref] enactics_v0.1.md:214 — 使用可变编号 "定义4.3"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
16. [old_ref] enactics_v0.1.md:220 — 使用可变编号 "定理4.2"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
17. [old_ref] enactics_v0.1.md:224 — 使用可变编号 "定义4.3"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
18. [old_ref] enactics_v0.1.md:226 — 使用可变编号 "定理4.3"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
19. [old_ref] enactics_v0.1.md:234 — 使用可变编号 "定义4.4"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。
20. [old_ref] enactics_v0.1.md:238 — 使用可变编号 "定理4.4"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。

... 还有 1640 条，详见完整报告。

## 总结

⚠️  发现 1 个错误，0 个警告，1660 条建议。


**核心原则**: 所有定理引用使用永久ID（T001格式），一旦确定永不改变。
旧格式引用（定理X/公理X）会随版本变化而失效，必须逐步迁移到永久ID。
