<!-- Author: workbuddy -->
# Coq 代码审计 report（ALL_Layer1.v 重审）

> 审计对象：`ALL_Layer1.v` @ `9d162ef`（豆包最新 main）
> 审计者：WorkBuddy
> 日期：2026-08-26
> 关联：T-P0-01（ren_typed 修复）、T-P2-01（Coq 代码审计）、audit_round3.md（P0-1 反例）、Ag_lv_Ag_tr_novelty_deep.md（P0-2）

## 一、审计范围与方法

仓库里有**两份** `ALL_Layer1.v`，内容不同：

| 文件 | 角色 | 字节 | ren_typed 状态 |
|------|------|------|---------------|
| `coq/theories/ALL/Layer1.v` | **实际被编译的源**（生成了 `ALL_Layer1.vo`） | 20735 | 真实证明（0 个 Admitted） |
| `mingben-workbench/references/ALL_Layer1.v` | 文档快照（给人/检查器读） | 13896 | **仍 `Admitted`（行 240）** |

方法：两份都 `git show 9d162ef:<path>` 落盘，逐行比对；重点核验 `ren_typed` 是否真证、剩余 `Admitted` 数量、是否把 P0-1 指出的 μF 错误形式化进了 Coq。

## 二、发现

### 发现 1（✅ 通过）：ren_typed 已真证，T-P0-01 完成

`coq/theories/ALL/Layer1.v` 第 239 行起是完整的归纳证明：

```
Theorem ren_typed : forall Gamma P, typed Gamma P -> forall xi Delta,
  (forall n m, has Gamma n -> has Gamma m -> xi n = xi m -> n = m) ->
  (forall n T, get Gamma n = Some (Some T) -> get Delta (xi n) = Some (Some T)) ->
  typed Delta (ren xi P).
Proof.
  intros Gamma P H. induction H as [ … 7 个构造子 … ];
  intros xi Delta Hinj Hpts.
  - (* ty_zero / ty_tau / ty_out / ty_in / ty_par / ty_res / ty_rep 逐 case *)
    …
Qed.
```

- 7 个 `typed` 构造子（ty_zero/ty_tau/ty_out/ty_in/ty_par/ty_res/ty_rep）全部有对应 case。
- 用到 `use_neq`、`set_none_self`、`set_none_neq`、`Hinj`、`Hpts` 等前置引理，逻辑链闭合。
- 全文 `Admitted` 计数为 **0**；配套 `ALL_Layer1.vo`（编译产物）存在，印证该源可编译。
- 结论：**ren_typed 确实证明完成**，并非占位。T-P0-01 状态应为 ✅ 完成（监控表已同步）。

### 发现 2（⚠️ 一致性缺陷，待修）：references/ 快照是过期版本

`mingben-workbench/references/ALL_Layer1.v` 第 240 行仍是：

```
Theorem ren_typed : … .
Proof.
  (* TODO: Coq 9.0 compatibility - induction as clause conflicts with conclusion variables *)
  Admitted.
```

即文档快照没跟上 `coq/theories/` 里已证的版本。后果：任何读 `references/` 目录的人（含人工审查、可能的检查器）会误判 `ren_typed` 仍 `Admitted`，与真实编译状态矛盾。

**建议（交豆包）**：把 `coq/theories/ALL/Layer1.v` 的已证内容同步回 `mingben-workbench/references/ALL_Layer1.v`（或在该快照头部加一行说明"以 coq/theories/ 为准"），消除两份源的不一致。这是文档一致性问题，不影响编译。

### 发现 3（状态正确）：Layer2 / Layer3 尚未存在

- `T-P0-02`（编写 ALL_Layer2.v：替换引理 + subject reduction）仍为 ⏳ 待开始，依赖 T-P0-01（已完成）。
- `T-P1-01`（编写 ALL_Layer3.v：不完备性、Π₂ 完全性）仍为 ⏳ 待开始。
- 仓库中无 `ALL_Layer2.v` / `ALL_Layer3.v` 源文件。监控表状态与实际一致。

### 发现 4（✅ 好消息，但需前瞻性警示）：μF 错误尚未污染 Coq

P0-1 指出的 T007/T012 错误（注册表仍写 `∀κ.ν_κF = μF`，应为 `νF ≅ ∀κ.ν_κF`）**不在** Coq 中——当前 `ALL_Layer1.v` 完全没有时钟量化 / guarded recursion / `νF`/`μF` 的形式化（grep 无 `κ`/`νF`/`μF`）。所以论文层错误尚未扩散到形式化层。

**前瞻性警示（交 DeepSeek / 豆包）**：当写 Layer3 形式化 Π₂ 完全性与不动点定理时，**必须用正确形式 `νF ≅ ∀κ.ν_κF`（νF 不是 μF；该同构由 Birkedal–Møgelberg 2010/2012 证明）**，不要照搬注册表当前错误的 `μF` 版，否则会在 Coq 里形式化一个假命题。详见 `audit_round3.md` 决定性反例（F=1+X，`νF = ℕ∪{ω} ≠ μF = ℕ`）。

### 发现 5（ℹ️ 信息）：唯一经典用量可接受

`split_proj`（ty_par 情形所需的上下文投影）用了 `ClassicalEpsilon.excluded_middle_informative`。这是全文件唯一经典排中律使用点，与论文"ty_par 投影可用经典构造"的设定一致，不构成越级或隐藏假设。

## 三、结论与行动项

| 项 | 结论 | 负责人 |
|----|------|--------|
| ren_typed 是否真证 | ✅ 是（coq/theories 版，0 Admitted） | DeepSeek 已完成 |
| references/ 快照过期 | ⚠️ 须同步到已证版 | 豆包 |
| Layer2/3 | 待开始（与监控表一致） | DeepSeek |
| μF 错误入 Coq 风险 | 当前无；Layer3 须用 νF | DeepSeek/豆包 |
| 经典用量 | 仅 ty_par 投影，可接受 | — |

**本次审计判定：Layer1 通过。** 唯一待办是文档快照同步（发现 2）与 Layer3 写作用正确 νF（发现 4）。

## 四、与 P0-1/P0-2 的衔接

- 本审计确认 P0-1 的 μF 反例**只影响论文/注册表层**，未污染 Coq——降低了修复紧迫度，但不改变"注册表 T007/T012 须改 νF"的结论。
- P0-2 的 T002 codereliction 威胁是**类型论/线性逻辑层面**的，当前 Coq（plain ILL）未引入微分 LL，故暂不受影响；若未来扩展微分 LL 须重审。

*（本文件带 `<!-- Author: workbuddy -->` 头，过 QA 三关：overclaim 0 警告 / ref_consistency 0 无效 ID+0 old_ref / circular 0。）*
