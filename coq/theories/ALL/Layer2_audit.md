<!-- Author: workbuddy -->
# Layer2 静态审计报告（WorkBuddy 审计，2026-08-27）

对象：`coq/theories/ALL/Layer2.v`（用户提供，DeepSeek 盲写、未编译第一刀）
方法：无 coqc 环境，逐行对照 `Layer1.v` 做静态审计（核对每一个 L1 引用、arity、签名、bullet 结构与证明义务）。
结论：**4 处确定编译错误 + 1 处 Layer1 根基缺口（ren_typed 是 Admitted）**。
修正版见同目录 `Layer2_fix.v`（未经 coqc 验证，需在用户真机编译确认）。

---

## 〇、最紧要：Layer1 的 `ren_typed` 是 `Admitted`（未证明）

`Layer1.v` 第 234–240 行：

```coq
Theorem ren_typed : forall Γ P, typed Γ P -> forall Δ ξ, ... -> typed Δ (ren ξ P).
Proof.
  (* TODO: Coq 9.0 compatibility - induction as clause conflicts with conclusion variables *)
  Admitted.
```

- 这与项目里"ren_typed 已证明（line 239, 0 Admitted）"的说法**直接矛盾**。文件里 ren_typed 是 `Admitted`（占位公理），**并未证明**。
- `Admitted` 在 Coq 里生成一个"无证明的常量"，所以 `apply ren_typed` 能过类型检查——但整条 Layer1 主定理是悬空的。
- **影响范围**：
  - `Layer2.msubst_typed`（替换引理）依赖 `ren_typed`，因此它本身也是"在 ren_typed 公理下成立"，不是真证明。
  - `subject_reduction` 与 `progress` **不**依赖 `ren_typed`（它们只用 Layer1 已证的小引理 `split_proj / set_none_* / get_Some_lt / split_get_l/r` + Layer2 自证的 `split_contra / agree_typed / split_nones_r`）。所以验收标准这两条在修复 B/C/D/E 后**可以真正证出来**，不必等 ren_typed。
- **行动项（L1，最高优先级）**：真正证明 `ren_typed`。报错提示是 "induction as clause conflicts with conclusion variables"（Coq 9.0 改动：对含结论变量 Γ/P 的 `induction H` 报错）。标准绕法：`induction H` 前先 `revert Γ P` 把结论变量推出去，或把定理改写成 `forall Γ P (H : typed Γ P) Δ ξ, ...` 后用 `induction H` 再 `intros`。此修复属于 Layer1，用户/豆包来落。

---

## 一、Layer2 的 4 处确定编译错误

### Bug B —— `progress` 的 `ty_par` 分支（Hv1 / P2' 情形）
位置：`progress` 定理，`destruct IH2` 的第二子情形。

原稿（错）：
```coq
      * right. exists (PPar P P2'). apply (s_par_l P P1' Q Hs1).
```
问题：
1. `P1'` 在此分支**不在作用域**（它是 `destruct IH1` 另一支的绑定），编译报 `No such variable P1'`。
2. 语义也错：本情形是 Q 可约（Q → P2'，证据 `Hs2 : step Q P2'`），应构造 `PPar P P2'` 并用 `s_par_r`；原稿却用 `s_par_l P P1' Q Hs1`。

修正（已写入 `Layer2_fix.v`）：
```coq
      * right. exists (PPar P P2'). apply (s_par_r P Q P2' Hs2).
```

### Bug C —— `subject_reduction` 的 bullet 结构错位
位置：`subject_reduction` 定理，`induction H as [...] ; intros P' Hs; inversion Hs; subst.` 之后。

原稿有 7 个顶层 bullet（ty_zero / ty_tau / ty_out / ty_in / ty_par / ty_res / ty_rep），但：
- `step` 的构造子中，LHS 为 `PZero / POut / PIn` 的规则**不存在**；故 `inversion Hs` 对 `ty_zero / ty_out / ty_in` 三个目标**直接闭合（0 子目标）**。
- 存活目标只剩 4 个顶层：ty_tau(1) / ty_par(3 子) / ty_res(1) / ty_rep(1)。
- 原稿第一个 bullet `- (* ty_zero *)` **没有 tactic**，且 bullet 数与实际目标数（4）不符 → 编译报 "goal 未解 / bullet 无 tactic"。

修正：删去 ty_zero/ty_out/ty_in 的空 bullet，仅保留 4 个顶层 bullet，顺序 ty_tau → ty_par → ty_res → ty_rep（见 `Layer2_fix.v`）。

### Bug D —— `subject_reduction` 的 `s_par_l` / `s_par_r` 缺 `step` 前提
位置：`subject_reduction` 的 ty_par 第 2、3 子 bullet。

原稿（错）：
```coq
    + eapply ty_par. exact Hs0. eapply IH1. eassumption. exact H2.
    + eapply ty_par. exact Hs0. exact H1. eapply IH2. eassumption.
```
`IH1 : typed G1 P -> step P P' -> typed G1 P'`。`eapply IH1` 留下的两个前提依次是 `typed G1 P`（由 `eassumption` 解）与 `step P P'`。原稿把 `exact H2`（`typed G2 Q`）填到了 `step P P'` 的坑上 → 不匹配，编译失败。

修正：补上归约证据（`s_par_l` 子目标里 `inversion Hs` 给出 `Hs1 : step P P'`；`s_par_r` 给出 `Hs2 : step Q Q'`）：
```coq
    + eapply ty_par. exact Hs0. eapply IH1. eassumption. exact Hs1. exact H2.
    + eapply ty_par. exact Hs0. exact H1. eapply IH2. eassumption. exact Hs2.
```

### Bug E —— `subject_reduction` 的 `ty_res` 缺 `step` 前提
位置：`subject_reduction` 的 ty_res bullet。

原稿（错）：`eapply ty_res. eapply IH. eassumption.`
`IH : typed (Some T :: G) P -> step P P' -> typed (Some T :: G) P'`。`eapply IH` 留下 `typed (Some T::G) P`（eassumption 解）与 `step P P'`，但原稿到此结束，缺 `step P P'` 的填充 → 编译失败。

修正：`eapply ty_res. eapply IH. eassumption. exact Hs1.`（`Hs1 : step P P'` 由 `inversion Hs` 在 s_res 子目标给出）。

> 注：ty_rep 情形正确——`s_rep` 不约化内部 P，无需 step 前提，三子 bullet（split_nones_r / agree_typed / ty_rep）齐整。

---

## 二、4 个设计裁决问题（WorkBuddy 作为豆包替身的正式建议）

### Q1：`s_comm` 要不要删？（comm_redex_untypable 让它是"死规则"）
**建议：保留 `s_comm`，不要删。** 它是 π-演算通信公理，是整个演算的心脏。
"死规则"是**症状不是病因**：当前 `Layer1.split` 是"粗暴二分"——同一索引不能两边都有活槽位。通信 redex `POut x ∥ PIn x` 需要 x 在两边都被占用（一边输出能力、一边输入能力），被 `split` 直接禁止，于是 `comm_redex_untypable` 成立、s_comm 对良类型项永不触发。
- 删 s_comm → 演算彻底不能通信，Progress 虽"真空成立"但演算无用。
- 真修复在 **Layer1**：让 `split` 支持"能力感知的通道分裂"——同一索引 x 在 G1 放 `TChan _ _ (o=true)`（只发）、在 G2 放 `TChan _ _ (i=true)`（只收）。这正好用到 Q2 的 TChan 双能力。**已登记为 L1 新设计项（待豆包/用户拍板）。**

### Q2：`TChan i o T` 双能力是特性还是 bug？（DeepSeek 说不动 L1）
**建议：是特性，不是 bug。** `TChan : bool -> bool -> ty -> ty` 把输入/输出能力分别记在类型里，正是线性/会话类型做通道分裂的正确基础（Kobayashi 型思路）。Q1 的死 s_comm 恰恰是因为 `split` 没利用这两个 flag，而不是因为 TChan 多带了它们。**不要在 L2 里动 TChan**；把修复留给 L1 的"能力感知 split"。

### Q3：`value = v_in + v_out`（挂起接收/待发消息当典范形式）
**建议：同意，正确且必要。** Progress 要求"良类型闭项要么是值、要么能迈出一步"。一个 `PIn x Q`（无配对发送方）或 `POut x y P`（无配对接收方）会卡住，必须算值，否则 Progress 对它们证不出。这是标准 π-演算 Progress 处理的惯例（阻塞进程即典范形式）。`v_par`（两边皆值时 PPar 为值）也与 s_comm 死亡自洽。**维持现状。**

### Q4：替换引理取"名字版"（L1 无 ty_var）
**建议：同意，正确。** Layer1 的 `proc` 用 de Bruijn（`PVar n`），定型里没有显式名字变量；"把一个名字 m 替换进绑定变量"在 de Bruijn 下就是带 `upren` 的重命名 `ren`，`msubst` = `ren (sigma0 m)`。`msubst_typed` 是 `ren_typed` 在 `sigma0` 处的实例化，**逻辑正确**（验证见下）。
- 唯一依赖：`ren_typed`。在 ren_typed 真正证出之前，`msubst_typed` 只是"公理下成立"。验收标准的 subject_reduction/progress 不依赖它，故不受影响。

---

## 三、反例 / 攻防清单（验证 Layer2 证明的边界）

| # | 攻击点 | 结论 | 说明 |
|---|---|---|---|
| 1 | `comm_redex_untypable`：能否构造良类型 `PPar (POut x y P) (PIn x Q)`？ | **不可构造**（证明成立） | 需 x 在 G1、G2 同时被占；`split` 禁止 → 矛盾。证明无误。 |
| 2 | `subject_reduction` s_rep：复制体 P 在 `nones(len G)` 下若 P 含 G 中的自由名？ | **无反例** | `ty_rep` 前提是 `typed [] P`（P 闭），故 `nones` 死槽上下文足够；`agree_typed []` 前提 vacuous。 |
| 3 | `progress` 对 `PIn x Q` / `POut x y P`：是否真卡住？ | **是值，无反例** | 对应 Q3；v_in/v_out 覆盖，Progress 成立。 |
| 4 | `progress`/`subject_reduction` 对 `PTau`：s_tau 是否总可归？ | **成立** | `progress` 直接 `exists P, s_tau`；`subject_reduction` ty_tau `exact H`。 |
| 5 | **（最大实质性攻击）死 s_comm 导致演算无通信** | **真实缺陷，非证明错误** | Progress+SR 都成立，但良类型项下 s_comm 永不触发 → 整个类型化演算"不会通信"。这是 Q1/Q2 指向的 L1 类型系统不完整，需能力感知 split 修复。 |
| 6 | `msubst_typed` 对 `sigma0` 的注入性 | **成立（依赖 ren_typed）** | 用 `disjoint` + `get Delta m = Some(Some T)` 推出 n=k；逻辑无误，但挂在 Admitted 的 ren_typed 上。 |

---

## 四、验证状态与待办

- [ ] **未编译**：本环境无 coqc（无包管理器、WSL 被禁），`Layer2.v` / `Layer2_fix.v` 均未经 `coqc` 验证。修正版只做了静态审计级确认。
- [ ] **用户真机动作**：在能跑 coqc 的机器上 `coqc Layer1.v` 再 `coqc Layer2_fix.v`，把完整错误贴回；优先验证 Bug B/C/D/E 修复与 `progress`/`subject_reduction` 是否真的 `Qed`。
- [ ] **L1 最高优先级**：证出 `ren_typed`（见 §零），否则 `msubst_typed` 与未来 L3 仍悬空。
- [ ] **L1 设计项**：能力感知 split（Q1/Q2），让通信 redex 可良类型化，s_comm 不再"死"。
- [ ] **治理**：本审计未直推 main（main 已 `enforce_admins`）；存于 `workbuddy/layer2-v1` 分支并开 PR，由用户手机远程批准。

> 来源文件：`Layer1.v`（ren_typed Admitted，line 240）、`Layer2.v`（原文）、`Layer2_fix.v`（修正）。本次审计未发现 Layer2 对 Layer1 其它已证小引理的误用；所有 L1 引用经核对 arity/签名一致。
