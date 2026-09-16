# 当前证明链 · subject_reduction（给 DeepSeek 的最简施工链）

> 性质：这是**唯一面向当前目标的施工文件**。DeepSeek 每轮先读它，再读 Layer 全文。
> 它只回答三件事：要证什么、零件哪些已 Qed（直接用、别重证）、按什么顺序、哪条是死路。
> 更新：2026-09-15。目标一旦完成，本文件归档，换下一张"当前证明链"。
> 数学对错仍以 coqc 为准；本卡是路线不是证明本身。

---

## 0. 一句话现状

Layer1/Layer2 自有定理 **0 Admitted、整层 coqc exit=0**。Layer3 两处（`subject_reduction_self` line580、`subject_reduction_alien` line592）`eapply subject_reduction` 等一个**当前 Layer2 尚不存在**的定理。
注意：Layer2 line2621 旧 SUMMARY 注释写"Subject Reduction FULLY PROVED"是**过时注释，不属实**——顶层定义表里没有 subject_reduction 本体，以本卡为准（注释≠代码）。

## 1. 目标与最简依赖 DAG

```
J1  congruence_preserves_typing        ← 唯一真正缺口（11 构造子，难点只在 cong_sym）
        │  被 J2 的 red_cong 分支调用
        ▼
J2  subject_reduction                  ← 6 构造子；旧备份有现成骨架，零件全在岗
        │  补入 Layer2 后
        ▼
J3  Layer3 line580/592 自动转绿（eapply 即得），再整层 coqc
```

**只做 J1→J2→J3，不节外生枝、不新造更大抽象（结晶：拼装优先戒节外生枝）。**

### 精确陈述（建议签名，与 Layer3 的 eapply 对齐：先 typed 后 reduce）
```coq
Lemma congruence_preserves_typing : forall Gamma P P',
  congruence P P' -> typed Gamma P -> typed Gamma P'.

Theorem subject_reduction : forall Gamma P P',
  typed Gamma P -> reduce P P' -> typed Gamma P'.
```

---

## 2. J1 · congruence_preserves_typing 逐构造子施工表

congruence 共 11 构造子（Layer2 line180-193）。**唯一硬点是 cong_sym 方向反转**：对 congruence 直接归纳时，cong_sym 的 IH 方向是反的。标准解法二选一（推荐 A）：

- **方案 A（加强成对归纳，推荐）**：证
  `Lemma cpt : forall Gamma P P', congruence P P' -> (typed Gamma P -> typed Gamma P') /\ (typed Gamma P' -> typed Gamma P).`
  对 `congruence P P'` 归纳，每个构造子正反两方向一起构造，最后取合取分量即得 congruence_preserves_typing 与其反向。cong_trans 用两段函数复合；cong_sym 直接交换合取两项。
- 方案 B：mutual fix 同时声明正反两方向。

| 构造子 | 怎么证（用哪个已 Qed 零件，禁止重证） |
|---|---|
| cong_refl | 恒等，intros;exact |
| cong_sym | 成对版本里交换两个合取项（方案A），无需额外引理 |
| cong_trans | 正向=先到 Q 再到 R，两段 IH 复合；反向同理倒着复合 |
| cong_par_comm | `par_elim`(436) 拆出 split/typed P/typed Q，交换后 `ty_par` 重组；split 两侧对调用 `split_sym`(418) |
| cong_par_assoc | 两层 `par_elim` 拆，`ty_par` 重组；中间分划重合用 `split_assoc`(2531，已 Qed) |
| cong_par_zero | 正向 par_elim 拆，PZero 支对应空分划，留 typed P；反向用空 split + `ty_zero`/ty_par 补 PZero |
| cong_res_par | **直接调已 Qed 的 `typed_res_par_l`(2815)**；其反向（成对版本需要）调 `typed_res_par_r`(3058)，前提 `~ fv_at Q 0` 构造子已自带 |
| cong_rep_unfold | ty_rep 与 (ty_par + ty_rep) 互推；需要时用最小的 rep 拆/装小引理（@prove 当轮证掉） |
| cong_par_cong | par_elim 拆两侧，分别用两个 IH，再 ty_par 重组 |
| cong_res_cong | `res_elim`(457) 拆出 `typed (Some T::Gamma) P`，IH 后 `ty_res` 装回 |
| cong_tau_cong | inversion typed 取内部 typed，IH 后用 ty_tau 装回 |

> 交付要求：J1 先在独立 `TEST_cpt.v`（铁模板文件头 + Require ALL.Layer1 Layer2 + Import ListNotations）coqc exit=0，再整体并入 Layer2。辅助小引理一律当轮 `(* @prove *) ... Qed.` 交齐，不许留名字。

## 3. J2 · subject_reduction 六分支施工表（旧骨架可复用）

旧备份 `coq/theories/ALL/backup_9.0.1/Layer2.v` line218-251 有一版完整骨架，其所用零件在当前 Layer2 **全部已 Qed**，可直接迁移并按当前命名校准：

| reduce 构造子 | 证法 | 用到的已 Qed 零件 |
|---|---|---|
| red_tau | inversion typed，内部即目标，assumption | ty_tau |
| **red_comm** | **`exfalso`——线性系统里左端 typed 不可能成立**，不要去做 comm 代换 | `no_parallel_channel_sharing`(463，已证 `~ typed Gamma (PPar (POut x y P)(PIn x Q))`) |
| red_par_l | `par_elim`(436) 拆 split/HP/HQ，对左支用 IH，`ty_par` 重组 | par_elim, ty_par |
| red_par_r | 同上，对右支用 IH | par_elim, ty_par |
| red_res | inversion typed，`ty_res` + IH | res_elim/ty_res |
| red_cong | 先用 J1 把 P 同余推到 P'，IH 归约到 Q'，再用 J1 的**反向**（成对版本的第二分量，或 cong_sym 后再用 J1）推回 | congruence_preserves_typing(J1), cong_sym |

归纳写法照旧骨架：`intros Gamma P P' Ht Hr. revert Gamma Ht. induction Hr; intros Gamma Ht.`（参数顺序注意：当前目标签名是 typed 在前、reduce 在后）。

**关键认知（避免最大弯路）**：red_comm 是**空真分支**，靠 no_parallel_channel_sharing 导出 False，**不需要 substitution_general、不需要在这一支做任何代换**。旧版正是这么证的；不要试图正向构造 `PPar P (comm_subst y Q)` 的 typed。

## 4. 已 Qed 零件清单（直接 apply，禁止重证）

- 分划：`split_sym`(418)、`split_assoc`(2531)、par/out/in/res_elim：`par_elim`(436)、`out_elim`(443)、`in_elim`(450)、`res_elim`(457)
- 线性关键：`no_parallel_channel_sharing`(463)
- 限制-并行交换：`typed_res_par_l`(2815)、`typed_res_par_r`(3058)
- 弱化/紧缩（备用）：`typed_strengthen_unused`(366)、`weaken_none_head`(2645)、`typed_any_ctx`(2728)
- typed 构造子在 Layer1：ty_zero/ty_var/ty_tau/ty_out/ty_in/ty_par/ty_res/ty_rep
- 标准库（@stdlib，已 Require List PeanoNat Lia ClassicalEpsilon）：大胆直接用，不重证

## 5. 死路与禁行（本目标专属）

- 禁正向硬证 red_comm（它是空真，走 exfalso）。
- 禁为 cong_sym 新造选择函数/更大同余抽象；成对加强归纳是标准最短路径。
- 禁绕过 coqc 用自然语言判真假；判假先过证伪双门（本目标两条主命题均为真，旧备份即证据，问题只在工程量）。
- 禁手改 .v：DeepSeek 出完整段，执行方只 coqc 与原样回喂错误。
- CRLF：Layer2.v 是 CRLF，并入由执行方用 CRLF 安全脚本，DS 只输出代码块。

## 6. 工序与验收（每工序独立 coqc + 独立 commit）

1. J1：独立 TEST_cpt.v exit=0 → 并入 Layer2 → 整层 `coqc -Q . ALL Layer2.v` exit=0 且 0 Admitted → commit。
2. J2：独立范本 exit=0 → 并入 → 整层 exit=0 → commit。
3. J3：`coqc -Q . ALL Layer3.v`，line580/592 转绿（Layer3 其余未完成构件不在本卡范围，只确认这两处不再因缺 subject_reduction 报错）。
4. 每工序 DeepSeek 一次交齐主引理+全部辅助引理到 Qed；红则完整错误原样回喂，最多 5 轮，3 轮不收敛换道并记录 OB。
