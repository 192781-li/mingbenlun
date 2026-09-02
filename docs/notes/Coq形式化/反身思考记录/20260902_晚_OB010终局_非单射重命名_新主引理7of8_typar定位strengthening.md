# 2026-09-02 晚 OB-010 终局跃迁：substitution 即非单射重命名，新主引理 7/8，ty_par 最后硬点定位为 strengthening

## 一、本轮做成了什么（不是汇报，是沉积）

1. **想通了 substitution 的数学本质**：subst_var m k P 在语法树上与 ren(subst_name m k)P 逐构造子同构，唯一区别是 PIn/PRes 里 subst_var(Sm)(Sk) 对应 ren(upren rho)。于是代换定理不再需要在"insert_at 形状的源"上硬做 split 交换（旧路线的死结：交叉时子块 Ga/Gb 是重定向不是相等，逐位置列表相等不成立），而是改成 Layer1.ren_typed 同款的**源任意**主引理 subst_ren_general。这是一次"换坐标系"：从"在目标形状里凑"转到"在任意源上描述操作权流动，最后 specialize"。
2. **6 个地基引理全部自证 Qed**（没有照抄 DS#13）：upren_subst_name_pt（逐点，绕开体系没有的 funext）、ren_ext（逐点相等→ren 相同，归纳时要先 revert 函数参数否则 IH 被固定）、subst_var_eq_ren、subst_name_succ（绑定器平移）、subst_rho_pts（资源保持三支）、rho_inj_except_m（局部单射）。
3. **主引理 8 个 case 证到 7 个**：ty_zero/var/tau/rep/res/in/out 全 Qed。最难的 ty_out/ty_in，把 ren_typed 依赖全局单射 Hinj 的地方，全部换成"rho_inj_except_m + no_use 通道分量"推出局部不碰撞——这正是"非单射 renaming 靠 no_use 在实际使用位置恢复单射"的落地。
4. **最后一个 case ty_par 的硬点被彻底定位**（见第三节），并确定解法是 strengthening；与 DS#14 往返后由我数学纠错、定下正确引理陈述。
5. 全程编译绿、每步 commit/push（7d082e2→aa29e3d→4ea864d→8e19649），没有留一堆未提交改动。

## 二、策略为什么这样调整（反身）

- **旧路线为什么死**：把源上下文硬编码成 insert_at k T Gamma，PPar inversion 出的子块在交叉情形下不具这个形状。DS#13 想用 remember/revert 保住 insert 源再 reflexivity 蒙混，必然失败——几何上是重定向不是相等。换成源任意后，ty_par 的子进程源直接用 split 出的 Ga/Gb，根本不需要它们长成 insert 形状，死结消失。这验证了结晶"怀疑定义/换陈述前先核对索引层面"：真正错的是主引理陈述把源写死了。
- **我一度自我修正"不需要 strengthening"，本轮又改回来——这不是反复，是逐层逼近**：读 ren_typed ty_par 时，我以为 proj2 是补集所以不用紧缩；但亲手把 7 个 case 证完、站到 ty_par 面前逐行算 img1，才发现全局单射时成立的"补集干净"，在 rho 非单射 + weakening 冗余资源位下不成立。**这个差别只有真走到那一步、把 proj2 在 m 位为什么是 None 算清楚，才看得见**。教训：读模板得到的"应该没问题"要靠实际证明证伪/证实，不能提前下结论。

## 三、ty_par 卡点的精确结构（写给下一轮的我）

- split_proj Gamma1 rho G 把目标 G 按"Gamma1 的像"切成 proj1/proj2；IHQ 作用 proj2 需要 ~img1 Gamma1 rho(rho n)。
- ren_typed：img1 ⇒ 存在 m' 使 rho m'=rho n，全局单射给 m'=n，与 split 互斥矛盾。
- 我：rho m'=rho n 分两支。(i) m'=n 同样被 split 互斥杀掉；(ii) m'≠n 则 {m',n}={k,c} 碰撞对、像都是 m。支(ii)杀不掉，因为 weakening 允许 Gamma1 在 k 放 P 不用的冗余、Gamma2 在 c 放 Q 不用的冗余，于是 img1 成立、proj2 在 m 位被划 None，与资源前提冲突。
- no_use 是进程语法谓词，管不到"上下文里的冗余资源位"，缺口在此。
- **解法**：先紧缩——typed C P 且 P 不用 u，则 typed(set_none C u)P（typed_strengthen_unused，对 typed 归纳，ty_par 里 u 落哪侧紧缩哪侧，结构递归不会自指）。把碰撞位 k,c 上的冗余清掉，支(ii)消失，剩下完全同 ren_typed。
- 需要一个进程自由变量谓词 not_free_in（no_use_at_subst 是 subst 特化，不能直接当一般"不用 u"）。

## 四、DeepSeek 建议：采纳了什么、没采纳什么（承接者模式的把关）

- DS#11（严格线性排除交叉）：**判错**。typed 允许 weakening，交叉可能。
- DS#12（split_proj 重划但 assert m=0）：**方向对、结论错**。get_Some_lt 只给 m<length，推不出 m=0；拒绝其削弱主陈述的建议。
- DS#13（via-ren 骨架）：**方向采纳、证明全部自己重写**。funext 体系没有→改逐点引理；ty_out eqb 分支爆炸→改 subst_name_lt/gt+rho_inj_except_m+lia；ty_par reflexivity 蒙混→识破并最终定位真问题。
- DS#14（ty_par 设计判断）：**采纳"必须 strengthening、唯一路径、不会自指、不要改 split_proj/弱化 IH"；纠正两处**：①紧缩引理不该加"u 位本空"前提（那让紧缩恒等、无的放矢），正确是"进程不用 u 就能清空，无论原来有无"；②m 不是"不在 Gamma 的新名字"，而是 get Gamma m=Some T 的被代换源位置。
- 元规律再次验证：**DS 会在数学判断上反复出错（尤其爱断言"某情形矛盾/不可能/m=0"），但在正确、聚焦、带完整上下文的问题上能给出有用的路线判断**。承接者不是抄录者，是"让 DS 获取一切 + 自己读定义做数学裁决"。

## 五、哲学判断点（已流转 S01，不自己猜）

1. strengthening = 主动丢弃"未被使用的明性（资源位）"。主人已明确"明性可以不保持"，请 S01 把这句口头判断上升为正式研判并命名，确认与"籍才须保持、路线乙同型异位"一致。这是 ty_par 落地前唯一需要的哲学背书；它不改变代码方向，只确认紧缩在存在论上合法。
2. 碰撞对 {k,c} 收束到同一 m：两条操作权流汇为一条，紧缩清掉的是没有操作权流经的空壳位置。

## 六、自我评价与改进

- 做得好的：没有停在汇报，真的把 7 个 case 一个个编译到 Qed；每次 DS 出错都回定义核实而不是照抄；每步 commit 不攒；卡点用精确数学语言写清（哪一步、哪个引理、为什么 proj2 是 None、缺口在语法谓词 vs 上下文冗余）。
- 要改进的：①"不需要 strengthening"的过早结论浪费了一点时间，以后读模板的推断要标注"待证明证实"；②ty_in/ty_out 里 exact 应用参数漏括号、pose 内联多参数项解析不稳这类纯语法小错反复出现，已沉淀：exact 只吃一个 term（函数应用加括号）、by 块里复杂 term 先 assert/pose 命名。
- 下一轮：not_free_in → typed_strengthen_unused → ty_par 收尾 → subst_ren_general 整体 Qed → 一行导出 substitution_general → 三层顺序编译 → congruence。路线完全清晰，无未知数学（只剩工程量）。
