# OB-010：substitution 的 PPar / ty_par —— 非单射重命名下并行组合的"资源重划"（最后一个 case）

- 编号：OB-010
- 首次记录：2026-09-02；**重大更新：2026-09-02 晚（via-renaming 路线，subst_ren_general 7/8 Qed）**
- 所在文件/定理：coq/theories/ALL/Layer2.v
  - 新主引理 `subst_ren_general`（源任意，同构 Layer1.ren_typed）：**8 个 case 已 Qed 7 个，只剩 ty_par 一个 admit（约 line1056），整体暂 Admitted（line1073）**
  - 旧 `substitution_general`：7/8 手证 case 保留作交叉验证，PPar admit（line1824），待 subst_ren_general 证通后由它一行导出
- 阻碍本质：**纯技术（线性类型 strengthening），但牵涉一个存在论语义判断（主动丢弃"不用的明性"是否合法——主人已明确"明性可不保持"，倾向合法）**

---

## 一、路线转变：substitution 本质是"非单射重命名"（已落定，编译验证）

旧路线想让 PPar 直接在 `insert_at k T Gamma` 形状的源上做 split 交换，卡在"子块 Ga/Gb 不具 insert_at 形状（交叉时是重定向不是相等）"。

新路线（S04 自行数学决断，DS#13 给方向、S04 改写落地）：
- `subst_var m k P = ren (subst_name m k) P`（引理 subst_var_eq_ren，对 P 归纳，已 Qed）。
- 令 rho:=subst_name m k。rho **非全局单射**：唯一碰撞对是 {k,c}（m<k 时 c=m；m≥k 时 c=m+1），rho k = rho c = m；其余位置单射（已 Qed rho_inj_except_m）。
- 资源保持 subst_rho_pts（已 Qed）。
- 主引理改为**源 D 任意**（不写死 insert_at）：
  ```coq
  Lemma subst_ren_general : forall (D:ctx)(Q:proc), typed D Q ->
    forall (m k:nat)(G:ctx),
    (forall n T', get D n=Some(Some T')->get G(subst_name m k n)=Some(Some T')) ->
    no_use_at_subst Q m k=true -> typed G (ren (subst_name m k) Q).
  ```
  对 typed D Q 归纳，逐行同构 Layer1.ren_typed（line246-413）。
- 最终导出 substitution_general：取 D=insert_at k T Gamma，资源前提供给 subst_rho_pts，rewrite subst_var_eq_ren 即得。

## 二、7/8 case 已 Qed（commit 链 7d082e2→aa29e3d→4ea864d→8e19649，均已 push）

| case | 状态 | 关键手法 |
|---|---|---|
| ty_zero | ✅ | ty_zero（任意 G） |
| ty_var | ✅ | 资源前提 Hpts |
| ty_tau | ✅ | IH + no_use |
| ty_rep | ✅ | IH 作用到 []，空上下文资源前提 discriminate |
| ty_res | ✅ | 进绑定器 rho→upren rho=subst_name(Sm)(Sk)，新引理 subst_name_succ |
| ty_in | ✅ | 通道经 rho；局部单射由 rho_inj_except_m + no_use 通道分量推出 |
| ty_out | ✅ | 两通道，全局 Hinj 的三处用途全部换成 rho_inj_except_m + no_use 两段 |
| **ty_par** | ⏳ admit | **唯一卡点，见第三节** |

配套地基引理（全部 Qed）：upren_subst_name_pt、ren_ext、subst_var_eq_ren、subst_name_succ、subst_rho_pts、rho_inj_except_m。

## 三、ty_par 的精确数学卡点（本次彻底定位）

照 ren_typed ty_par（Layer1 line356-391）：`destruct (split_proj Gamma1 rho G)` 得 split + Hp1 + Hp2；IHP 作用于 proj1（split_get_l + Hp1，顺通）；**IHQ 作用于 proj2 时，要对每个 get Gamma2 n=Some T 的 n 证明 ~img1 Gamma1 rho(rho n)（Hp2 前提）**。

- ren_typed 靠**全局单射** Hinj：img1（存在 m'，has Gamma1 m' /\ rho m'=rho n）⇒ m'=n，再用 split 互斥矛盾。
- rho 非单射，rho m'=rho n 有两种：
  - (i) m'=n：同样被 split 互斥排除 ✅
  - (ii) m'≠n：{m',n} 必是碰撞对 {k,c}，rho m'=rho n=**m**。**无法仅用 split 互斥排除**：因为 typed 允许 weakening，Gamma1 可在 k 位携带 P 并不使用的冗余资源、Gamma2 可在 c 位携带 Q 并不使用的冗余资源；于是 img1 成立，proj2 在 m 位被划成 None，而 IHQ 的资源前提要求 get(proj2) m=Some T，失败。
- no_use_at_subst 是**进程语法**谓词（进程不用映到 m 的通道 k,c），不能直接说明**上下文** Gamma1/Gamma2 在 k,c 位无资源（weakening 允许冗余）。这就是缺口。

### 解法（已确定方向）：strengthening（紧缩）
先把子进程上下文紧缩到它实际使用的最小上下文，清掉碰撞位上的冗余资源，则情形(ii)两边碰撞位皆空、img1 不成立，~img1 得证，后续完全同 ren_typed。

**正确的紧缩引理陈述（S04 纠正 DS#14 后）**：
```coq
(* 进程 P 不使用通道 u（自由变量层面），则把 C 的 u 位清空后 P 仍可类型化——
   不需要"C 在 u 位本就空"这个前提（DS#14 加了它，使紧缩退化为恒等，是错的） *)
Lemma typed_strengthen_unused : forall (C:ctx)(P:proc)(u:nat),
  typed C P -> not_free_in u P = true -> typed (set_none C u) P.
```
- 对 typed C P 归纳（结构递归，ty_par 时 u 落在哪侧就对该侧 IH，split 同步；不会自指）。
- 需要一个进程自由变量谓词 not_free_in / free_in（no_use_at_subst 是 subst 特化，不能直接当一般"不用 u"用，需另定义或证 no_use 到 free_in 的桥接）。
- ty_par 里对碰撞位 k、c 分别在对应侧 strengthen，再 split_proj。

### DS#14 的对与错（留档 s01_temp_docs/deepseek_v14_typar.md）
- ✅ 对：确认"必须 strengthening、唯一正确路径"；确认紧缩引理对 typed 归纳不会在 ty_par 自指；否定了"改 split_proj 变体/弱化 IH 前提"（会波及其余 7 case）。
- ❌ 错1：紧缩引理加了 `forall T, get C u <> Some T`（u 位本空）前提，使紧缩恒等、无的放矢。正确是"进程不用 u 即可清空，无论原来有没有"。
- ❌ 错2：说最终导出时"选 m 为不在 Gamma 中的新名字"。实际 substitution_general 里 **m 是承载被代入资源 T 的源位置，get Gamma m=Some(Some T)（Hget），m 在 Gamma 中有资源**，不是新名字。不采纳。

## 四、涉及的哲学问题（请 S01 研判）
1. **strengthening = 主动丢弃"未被使用的明性"**：子进程上下文里它不使用的资源位，是否可以在形式化中清空而不改变存在论语义？主人已口头明确"为什么一定保持明性？当然可以不保持明性"——请 S01 把这句上升为正式研判：紧缩引理在 ALL 体系是否与"明性可不保持、籍才须保持"一致，命名用什么（紧缩/去冗余/明性收摄？）。
2. 碰撞对 {k,c} 的存在论解读：代换把两个名字收到同一个 m，这是"两条操作权流汇为一条"，strengthening 清掉的是"没有操作权流经的空壳位置"，请确认这一解读与路线乙（同型异位、insert_at 是假设不是复制）相容。

## 五、解决状态：**open，但已到最后一步（7/8，解法与引理陈述已定）**
下一步（按序）：
1. 定义进程自由变量谓词 not_free_in（或证 no_use_at_subst→碰撞位 not_free_in 的桥接）。
2. 证 typed_strengthen_unused（对 typed 归纳）。
3. subst_ren_general 的 ty_par：对 k,c 紧缩后照 ren_typed line356-391 完成，整体改 Qed。
4. 用 subst_ren_general 一行导出 substitution_general，去掉 line1824 admit，旧 7 手证 case 保留交叉验证。
5. 复跑 Layer1→2→3 顺序编译，内部 admit 清零（仅剩独立的 congruence_preserves_typing）。
