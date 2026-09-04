# J1d：split_assoc 主定理的正确路线（弃 fcell/pick，复用已 Qed 的 split_assoc_cell 见证）

> 给 DeepSeek 的任务书。S04 已用独立 coqc guard 机器查清"哪条路真、哪条路假"，你按本文件出完整可编译代码，不要再走被证伪的 fcell 路线，也不要再怀疑主命题。

## 一、两条铁的事实（已被 coqc 机器证实，禁止翻案）

1. **主命题 split_assoc 为真**，不容再宣布为假：
   `split G G12 G3 -> split G12 G1 G2 -> exists G23, split G G1 G23 /\ split G23 G2 G3.`
   证据：逐位版 `Lemma split_assoc_cell`（exists g23）**已在 Layer2 Qed**；J0 阶段见证类型也已 coqc 检查通过。

2. **你前几轮自造的 `fcell` 固定选择 + `split_assoc_cell_pick` 引理为假**，S04 用独立文件 coqc exit=0 机器证实反例：
   - 反例格：`g=None, g12=None, g1=Some None, g2=None, g3=Some None`
   - 三前提全真：`cell_split None None (Some None)`✓、`cell_split None (Some None) None`✓、`g2<>None \/ g3<>None`（由 `Some None<>None`）✓
   - 但 `fcell None (Some None) = Some None`，于是结论第一合取 `cell_split None (Some None) (Some None)` 为假（两支都要求 `Some None = None`，被 discriminate 推翻）。
   - **根因**：fcell 按"g2 是 Some(Some a) 就取 g2，否则取 g3，皆空取 Some None"选值；但在"g 越界 None、g1 在位空 Some None、g2 越界 None、g3 在位空 Some None"这一格，正确值应是 **g=None**（让第二支 b=g 成立），fcell 却错取了 g3=Some None。
   - 教训：你前几轮的"判假直觉"摸到了 pick 这个**你自造的辅助引理**确实有洞，但你错误地把它上升成"主命题 split_assoc 假"。主命题真、你的固定选择函数假，是两回事。

## 二、正确的逐位选择规则（直接抄自已 Qed 的 split_assoc_cell 四格证明）

split_assoc_cell 的 Qed 证明已对每个析取格显式给出见证 g23：

| H1=cell_split g g12 g3 | H2=cell_split g12 g1 g2 | 正确见证 g23 |
| --- | --- | --- |
| 左：g12=g，g3 空 | 左：g1=g12，g2 空 | **g2** |
| 左：g12=g，g3 空 | 右：g2=g12，g1 空 | **g** |
| 右：g3=g，g12 空 | 左：g1=g12，g2 空 | **g** |
| 右：g3=g，g12 空 | 右：g2=g12，g1 空 | **g** |

即"只有『左-左』格取 g2，其余三格都取 g"。这个选择在反例格（左-右）取 g=None，恰好修正 fcell 的错误。

## 三、要你做的事（小步，分步交）

Layer1 事实：ctx=list(option ty)；get 越界返回 None；setby f L k 逐位作用且不改变 length；split 是 forall n 的逐位 cell_split；`H23_val` 已 Qed（逐位读出 setby 见证值）。ty 是有限归纳，option(option ty) 可判定相等（需要时用 decide equality / Nat 之外的 Sumbool）。

**第一步（先只交这些 INSERT-BEFORE，coqc 过了再交主定理）**：
- 按第二节四格定义正确的逐位选择函数 `choose (g g12 g3 g1 g2 : option(option ty)) : option(option ty)`（纯函数，用 match/相等判定实现"左-左取 g2、否则取 g"；若纯函数难以表达析取条件，可改证一个带前提的显式见证引理，形式自定，但必须可编译、为真）。
- 证 choose 的正确性引理（替代假的 pick）：
  `cell_split g g12 g3 -> cell_split g12 g1 g2 -> cell_split g g1 (choose ...) /\ cell_split (choose ...) g2 g3.`
  直接按 split_assoc_cell 的四格 destruct 走，每格 choose 的取值与该 Qed 证明的 exists 见证一致，因此必真、应很短。0 Admitted。

**第二步（第一步 coqc 通过后，再 REPLACE 主引理）**：
- 用 choose 逐位构造 G23（如 `setby (fun n _ => choose (get G n)(get G12 n)(get G3 n)(get G1 n)(get G2 n)) (repeat None max_len) 0`，max_len 取足够覆盖 G/G1/G2/G3/G12 长度），exists 之；
- unfold split、intros n，在位位用 choose 正确性引理 + H23_val（读出 G23 第 n 位 = choose ...）；越界位各 get 皆 None，直接证 cell_split（左支自反）。
- 主引理 split_assoc 从 Lemma 到 Qed 完整给，0 Admitted。

## 四、硬性禁止
- 禁止重新提交 cell_split / split_assoc_cell（已在文件 Qed）。
- 禁止再用 fcell、split_assoc_cell_pick，或任何"g2 优先否则 g3 兜底"的固定选择。
- 禁止宣布 split_assoc 或 choose 正确性引理为假、禁止交反例（主命题真已机器证实）。
- 每步交齐依赖的小引理到 Qed；优先 @stdlib（List/PeanoNat）已机器证明者，不重复造轮子；需要新小引理（如 option(option ty) 判定、长度覆盖）自己证到 Qed。
- 一次只做本步，不要把主定理和第一步揉成一个巨型输出。
