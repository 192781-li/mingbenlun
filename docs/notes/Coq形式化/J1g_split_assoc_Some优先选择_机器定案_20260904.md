# J1g：split_assoc 正确路线（四轮 guard 机器定案，勿再怀疑主命题）

> 给 DeepSeek。**split_assoc 已被独立 guard 反复证实为真，禁止再宣布它为假、禁止交 `~exists...`/`_counterexample`。** 之前所有卡住源于一个错误的逐位选择函数 choose。本轮按 Some 优先重写选择层。

## 0. 机器铁证（独立 guard，coqc 均 exit=0，结论不可翻案）
- `_guard_assoc_false.v`：你上一轮交的 choose_suffix 反例实例（G=[Some TUnit;Some TUnit], G12=[Some TUnit;None], G3=[None;Some TUnit], G1=G12, G2=nil），两个 split 前提确实成立（cf_split1/2），**但存在 G23=[None;Some TUnit] 满足结论**（choose_counterexample_does_not_kill_assoc）。
- 结论：**假的是 `choose`（"左-左格一律取 g2"）这条选择规则，不是 split_assoc。** choose_suffix 在 choose 下为假是正常的，不要再证它、也不要据此判主命题假。
- `cf_real_problem_only`：只有真问题格 `cell_split None (Some None) x -> x=None`（g 越界且 g1 在位空）才被迫取越界 None；其余格（含 g 在位的左-左格）都有在位候选 Some None 或 Some(Some T)。

## 1. 错误根因（一句话）
左-左格在 g 在位时，choose 机械取越界的 g2=None，于是选择序列出现 `[None(位0); 在位(位1)]` 的非前缀交错，列表无法实现；但该格本可取**在位空 Some None** 承续，取它就恢复前缀连续。

## 2. 正确选择规则：Some 优先
给定逐位 g=get G n, g12=get G12 n, g3=get G3 n, g1=get G1 n, g2=get G2 n，以及 H1:cell_split g g12 g3, H2:cell_split g12 g1 g2。
在所有"同时满足 cell_split g g1 z 且 cell_split z g2 g3"的候选 z 里：
- **优先取在位值**（z=Some _，即 Some(Some T) 或 Some None）；
- 只有当所有候选都只能是越界 None 时（等价于真问题格：g=None 且 g1=Some None，此时 cf_real_problem_only 强制 z=None），才取 None。
实现可用 ClassicalEpsilon/排中，或直接对五个 option(option ty) 三态 destruct、配合 H1/H2 穷举，每格显式选一个 Some 优先的 z（材料是经典逻辑，ClassicalEpsilon 已可用）。

## 3. 本轮只交以下（INSERT-BEFORE Lemma split_assoc，全部 Qed、0 Admitted）
(A) `Definition pick_prefix ... : option(option ty)`：Some 优先逐位选择（替换错误的 choose；choose/choose_correct/is_empty_get 已 Qed 的先保留不删，避免动别处，新引理并列新增即可）。
(B) `Lemma pick_prefix_correct : forall ..., cell_split g g12 g3 -> cell_split g12 g1 g2 -> cell_split g g1 (pick_prefix ...) /\ cell_split (pick_prefix ...) g2 g3.`（逐位三态穷举，纯枚举）
(C) `Lemma pick_prefix_none_suffix : forall G G12 G3 G1 G2 n m, n <= m -> split G G12 G3 -> split G12 G1 G2 -> pick_prefix (get G n)(get G12 n)(get G3 n)(get G1 n)(get G2 n) = None -> pick_prefix (get G m)(get G12 m)(get G3 m)(get G1 m)(get G2 m) = None.`（pick 取 None 的位向后闭 ⇔ 非 None 位是前缀。**注意：不要证"n<max长度⇒pick非None"，那是假的**——真问题格 g 越界、g1 在位空可出现在 n<max 区间，此时 cf_real_problem_only 强制 pick=None；但它必落在后缀，不破坏构造。）
本轮**不碰主定理、不构造 G23 列表**，把 (A)(B)(C) 三个 Qed 交干净即可。下一轮据 (C) 定 G23 长度=第一个 pick=None 的位置（全非 None 则取 max 长度），逐位读出 pick 剥层值。

## 4. 硬纪律
- 只交 (A)(B)(C) 及其直接依赖的 get 长度小引理，全部 Qed；不 iff、不另造第二套选择、不重交已 Qed 件、不判主命题假。
- option 三态 destruct `as [[T|]|]`；两种寂分清 None=越界 / Some None=在位空；不要把 Some None 当实资源冲突。
- 直接给 ```coq 代码，别写长段自然语言论证。
