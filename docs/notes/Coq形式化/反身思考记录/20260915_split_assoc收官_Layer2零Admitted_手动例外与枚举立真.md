# 2026-09-15 反身思考：split_assoc 收官，Layer2 零 Admitted——手动例外、枚举立真、以及我为什么过去总在浪费

> 分站：S04（明序）｜分支：s04-coq｜commit：edc2333（证明）、d284f34（固化）｜方式：用户特许手动（DS 主谋分工的唯一例外）

## 一、这轮到底成了什么（事实，非口号）

- Layer2 最后一个 Admitted `split_assoc`（资源分划结合律）完整 Qed，整层 `coqc -Q . ALL Layer2.v` **exit=0**；Layer1/Layer2/Layer3 真正的 `Admitted.` tactic 总数为 0。
- 路径可复核：先在独立范本 `TEST_split.v` 做到 exit=0，再用 CRLF 安全的 Python 脚本并入正式 Layer2.v（替换原 Admitted 块，新增 256 行证明链），并入后又修一处真实问题（gc_blank 复用 Layer1 split_get_l/r 时按名绑定要用 Gamma/Gamma1/Gamma2 而非 TEST 里的 G/A/B），重编 exit=0。
- Layer3 仍 exit=1，但唯一原因是 line580 引用 Layer2 尚未证的 `subject_reduction`——这是**下一个目标**，不是 split_assoc 引入的回归。

## 二、为什么 DeepSeek 九轮没成，而这轮成了（照见自己过去的妄）

1. **DS（以及过去的我）一直在和"想象中的目标"搏斗。** 在主上下文 `destruct (merge_cell ..) eqn:Em` 后，Coq 把目标里**埋在 build_g23 递归体中、尚未展开的同名 merge_cell 一并替换成构造子**；之后 `rewrite Em` 当然失配——项已经不在了。九轮里反复调 `cbn` 的展开粒度（全 cbn / cbn[f] / beta iota delta），都是在一个错误的心智模型上加大力气。**这轮的转折动作极其便宜：插一句 `idtac` 把真实目标打印出来。** 打印两次，翻盘两次：一次发现"区间外分支结论本来就是 None、根本不含 build 项"，于是删掉一整套多余的越界引理；一次发现 destruct 的隐藏替换。明性 F3 在此不是玄思，是"照见自己正要 rewrite 的那个项此刻真实的样子"。
2. **真假方向没先锁定就烧额度。** DS 一度判定 split_assoc 为假。这轮我先用 Python 对 option(option ty) 三态做有限穷尽：merge_cell/cell_step 各 32 组合 0 失败、build_g23 递归 2383 个可达实例 0 失败、两类交错反例搜索 0。枚举不是证明，但它是最便宜的真假方向探测器——0 反例把问题从"命题是不是假的"重新定位为"证明路线/引理强度不对"，于是不再在判假分支上浪费。这正是结晶022。
3. **正确的数学结构：中间块 G23 不是现成实体，是逐位重新聚拢。** merge_cell 定一位怎么并（四规则），build_g23 从分界 k 起、遇 None 截断地把 G2/G3 聚起来，build_correct 做区间归纳（区间内步长引理化归到 S k 层、区间外结论本就是 None），主定理再按 n<K / n≥K 分情况。危险交错不是被某个聪明引理消灭的，是被 split 定义自身（一位只能归属一侧）逐位排除的。过去 choose/fuel 路线的失败，本质是想用"现成选择"回避"重新聚拢"这个构造动作。

## 三、策略为什么这样调整（可复用，已进结晶库）

- 结晶021：依赖某等式化归的步骤，**抽成带假设 H、不 destruct 的独立小引理**（step_head/step_some/step_none），主归纳只 apply；配合 Opaque 保护待 rewrite 的常数、归纳前 revert 递增下标、合取用 destruct as、Nat.sub_0_r、apply 多前提显式 with。
- 结晶022：DS 三轮不收敛且开始质疑真假 → 停派单，花十分钟写宿主语言枚举把小论域跑满，用"0 反例/第 k 个反例"这个事实决定方向，而不是用更强的 prompt 再赌一轮。
- 工艺层：Layer2.v 是 CRLF，Edit 工具按 LF 匹配必失败，统一用 Python io.open 读入、写回时还原 CRLF；独立范本先证、再并入、再整层编译，杜绝直接在正式大文件上盲改。

## 四、哲学判断点（留给 S01，不自行拍板）

- 中间聚合块 G23"无自性、逐位聚拢而成"，与生命论"多者并行的中间综合不是现成存在者、是在归属规则下被聚拢"是否同构？有限枚举之明（在感层对具体格位的清点）上升到 coqc 普遍真（感应层对任意长度的成立），这条认识论阶梯请 S01 背书。
- 明性 F3 的用法严格限定为"反身照见自身操作"（idtac 照见真实目标、枚举照见真假方向），没有把它泛化成"生命向外照亮对象"的生命之光（F1/F2），遵守概念纪律。

## 五、这轮哪里做得比过去好、哪里仍要改（不画饼）

- 做得好：① 先独立范本后并入，全程有 exit code 为证，没有用活动量冒充进展；② 真假方向先用枚举锁定，再投入证明；③ 每一步都 commit 并 push，成果不会因对话压缩或算力重置丢失（edc2333、d284f34 已在远程）；④ 固化与证明分离成两个 commit，历史清楚。
- 仍要改：① 工作区残留一批一次性脚手架（_apply_split.py/_split_block.v/_crystal_append.md/_append_canal.py/_o.txt/_t.txt/.bak_split），应建立"临时文件统一放 scratch/、提交前自动清"的机制，而不是靠每次记得；② run_current.py 的 system prompt 是否已自动带上结晶021/022 还没核实——"让 DS 下次自动获得这些教训"必须落到代码，不能只写进 md（下一步第一件事）；③ Layer3 文件中文注释存在 GBK/UTF-8 错配乱码，触碰前要先定编码，避免重蹈覆辙。

## 六、下一步（按依赖顺序）

1. 把结晶021/022 与"派 DS 前先枚举立真、化归抽小引理"写进 run_current.py 的 system prompt / s04_context，确保 DS 自动获得（代码强制，不靠记性）。
2. 在 Layer2 证 `subject_reduction`（主题归约保持类型）：派 DS 前先按结晶022 对最小进程做枚举/预检，按结晶021 切小引理；证出后重编 Layer3，应转绿。
3. 清理一次性脚手架，建立 scratch 约定。
