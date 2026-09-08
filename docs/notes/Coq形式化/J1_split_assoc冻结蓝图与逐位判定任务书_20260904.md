# J1 任务书：split_assoc 逐位判定流水线（蓝图已由 J0 用 coqc 冻结）

日期 2026-09-04　工序 J1（看板）　DeepSeek 主谋，S04 只 coqc 终裁/git/哲学桥梁。
**本路线取代旧的"主定理内裸 destruct 9 格 + 整段重写"打法（那套 68 trace 0 收敛）。**

## 0. 目标与验收（唯一度量=coqc Qed 净增长）

- 消掉 Layer2.v 唯一 Admitted：`split_assoc`。
- 验收硬门：`coqc -R .. ALL Layer2.v` exit=0；`split_assoc` 与本轮新增的全部辅助引理 **0 Admitted / 0 Abort**；preflight 报 L2 Admitted 1→0。
- API success 不算收敛，只有整文件 coqc exit 0 才算。

## 1. 存在论命题（为什么为真，别再误判为假）

`split G A B` = 把场域 G 的每一位"分划"给 A 或 B（持值方=该位 get 等于 G，另一方为空：越界 None 或在位空 Some None）。
`split_assoc` 说：先按 (G12 | G3) 分、再把 G12 按 (G1 | G2) 分，必能重排出一个中间块 G23，使 (G1 | G23) 与 (G23 | G2 | G3) 两种分划都成立——**结合的顺序不改变逐位归属，中间块逐位重新聚拢即可，空位形态可选可收摄（结晶012：明性可不保持）**。已由证伪双门裁定为真，任何"为假/反例"必须先过证伪双门三步，否则禁止输出。

## 2. J0 已 coqc 类型验证的冻结蓝图（直接用，不要再改见证）

`split`（Layer1）逐位定义：
```coq
split G A B := forall n,
  (get A n = get G n /\ (get B n = None \/ get B n = Some None))
  \/ (get B n = get G n /\ (get A n = None \/ get A n = Some None)).
```

单 n 抽象（J0 已 Check 通过）：
```coq
Definition cell_split (g a b : option (option ty)) : Prop :=
  (a = g /\ (b = None \/ b = Some None))
  \/ (b = g /\ (a = None \/ a = Some None)).
```

逐位结合引理（J1-a，纯有限命题，变量全是 option(option ty)，取值有限）：
```coq
Lemma split_assoc_cell : forall (g g12 g3 g1 g2 : option (option ty)),
  cell_split g g12 g3 -> cell_split g12 g1 g2 ->
  exists g23 : option (option ty), cell_split g g1 g23 /\ cell_split g23 g2 g3.
```

主定理见证（J0 已验证类型；f 与已 Qed 的 H23_val 逐字一致）：
```coq
G23 := setby f (repeat (None:option ty) (Nat.max (length G2) (length G3))) 0
f n _ := match get G2 n with
         | Some (Some a) => Some a                       (* G2 真实发用，优先持之 *)
         | _ => match get G3 n with Some v => v | None => None end  (* 否则 G3 兜底 *)
         end
```
已 Qed 的 `H23_val`（Layer2，直接用）给出：当 n<max_len，
`get G23 n = match get G2 n with Some(Some a)=>Some(Some a) | _=> match get G3 n with Some v=>Some v | None=>Some None end end`。

## 3. 精确战术路线（小引理流水线，从简到繁，结晶001/004）

### J1-a：先独立证 split_assoc_cell（本轮真正的主战场，规模约 9 行 case）
1. `intros g g12 g3 g1 g2 H1 H2.`
2. 先用前提析取收缩：`destruct H1 as [(-> & [->|->]) | (-> & [->|->])]; destruct H2 as [(-> & [->|->]) | (-> & [->|->])].`
   —— 前提直接把 g12/g3/g1/g2 之间的大量等式钉死，绝大多数组合在此被归并/矛盾消去，**不要先裸 destruct g2/g3 造 9 格再硬填**（那正是旧空转根因）。
3. 剩余有限分支里，`exists` 一个 g23（选择规则与 H23_val 同向：g2 是 Some(Some x) 就取它，否则取 g3；两边皆空取 None/Some None 使两个 cell_split 同时成立），然后 `left/right` 选析取 + `auto/discriminate/injection` 收尾；`Some(Some x)=Some None` 这类用 `injection`/`congruence`，`None=Some _` 用 `discriminate`。
4. 若个别分支用 `tauto` 能收就用，但**不许留 Admitted**。

### J1-b：split 与 cell_split 的逐位等价（unfold 即得，可选）
`split G A B` 定义本就是 `forall n, cell_split (get G n)(get A n)(get B n)`，主证明里直接 `unfold split` 即可，不必单独立引理；若立则一行 `intros; unfold split, cell_split; auto` 类。

### J1-c：主定理变薄（不再有嵌套 bullet）
```
intros G G12 G3 G1 G2 H12 H3.
exists (setby f (repeat None (Nat.max (length G2)(length G3))) 0).
unfold split; split; intros n.
- (* split G G1 G23：specialize (H12 n)(H3 n)，经 split_assoc_cell 取左合取，位值等式用 H23_val（n<max_len）；n>=max_len 时 G2/G3 越界皆 None、G23 越界 None，cell_split 自动成立 *)
- (* split G23 G2 G3：对称，取 split_assoc_cell 右合取，同样 H23_val + 越界分支 *)
```
越界位（n≥length）统一事实：`get _ n=None`，`cell_split None None None` 走右析取 `None=None` 成立。需要的长度事实（n<length↔get≠None、repeat/setby 长度）若材料没有，按 @prove 立小引理当轮证掉。

## 4. option 双层铁表（本项目最易错，每个 match 前先定位层）

- 元素层 `option ty`：None=空 | Some T 持值；setby 的 f 入参/返回都在这一层。
- get 层 `option(option ty)` 三态：**None=越界之寂 | Some None=在位之寂 | Some(Some T)=真实发用**；destruct 用 `as [[T|]|]` 三分支。
- 元素层空是 None，绝不是 Some None；两层错配的反例必被证伪双门驳回。

## 5. 外部引理政策（四分类，大胆用已证）

- Stdlib/List/PeanoNat/Lia 已机器证明者大胆 Require 直接用（@stdlib L1），别重证轮子；
- 材料 Layer1/2 已 Qed 的直接用（H23_val、get_repeat_None_lt、get_setby_*、length 类等，先 grep 确认名字存在）；
- 教材结论只作思路须本库重证（@cite）；查无实据的名字禁止（幻觉拦截）；
- 加强归纳/更强引理是自由证明技术，需要就用，不算 Axiom。

## 6. 明令禁止

- 禁止一次吐上万字符、在主定理嵌套 bullet 里"修一处冒一处"；先证 J1-a 小引理再装主定理。
- 禁止 5 轮打满从 r1 重来时丢掉已证子引理——每轮把上一轮已 Qed 的辅助引理保留。
- 禁止未过证伪双门三步就宣布全称命题为假。
- 禁止 Abort 草稿、只留名字不给证明、把假设当已证。
