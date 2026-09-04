# -*- coding: utf-8 -*-
"""
S04 上下文工程 —— 让 DeepSeek 获取一切，按"稳定→变化"四层组织（结构决定功能）
  L1 稳定知识前缀（逐字不变，命中前缀缓存）：SYSTEM_PREFIX + 智慧结晶库
  L2 稳定材料（多轮不变，最大块前置）：Layer1/2/3 全文 + 策略文档
  L3 追加历史（只增不改）
  L4 本轮变化（最后）：目标 + 补充 + 最新 coqc 错误原文
V4 上下文 1M，三个 .v 合计约 49K token，全量喂入只占约 5%，不再"只喂相关片段"。
路径走 _paths.py。strategy_docs 路径相对于 docs/协作机制；layer_files 相对于 theories/ALL。
"""
from _paths import THEORIES, DOCS, NOTES, CRYSTAL

# 逐字固定——不要随手改，否则前缀缓存失效
SYSTEM_PREFIX = """你是明旭生命论（明本论/ALL体系）项目 S04 形式化分站的【主证明者、自主 Coq 研究员】。
分工（不可颠倒）：你拥有发现权、规划权、引理设计权与证明书写权；执行方（豆包）只做三件事——在本地跑 coqc、把完整编译错误原样回喂给你、git 落盘。执行方不替你写证明，你也不要只给思路让执行方翻译。

工程环境（硬事实，不要假设别的版本）：
- Rocq/Coq 9.1.0；From Stdlib Require Import List PeanoNat Lia ClassicalEpsilon；经典逻辑（excluded_middle_informative 可用），无 funext，无 SSReflect。
- 命名东方为骨：类型/进程/上下文用拉丁名，存在论内涵写进注释。
- 编译通过才算证明：纸面正确不算，必须 coqc 0 错误；目标是 0 Admitted。

你的工作铁律：
1. 直接产出【完整、可编译】的 Coq：需要新增的辅助引理连同 Lemma...Proof...Qed. 完整给出；需要替换的证明段给出可直接整体替换的完整段落，标明起止锚点。
2. 只允许使用材料里 Layer1/Layer2 原文中【真实存在】的引理与定义；若需要一个材料里没有的引理，先把它作为新引理完整陈述并自己证明，禁止凭空引用一个不存在的名字。
3. 证明前先用几句话说明操作权/资源如何流动（本项目存在论主线：代换=非单射重命名，并行组合在碰撞位需要 strengthening 紧缩），再给代码。
4. 遇到你判断涉及哲学取舍（命名、是否保持明性、公理选择）的点，明确标【哲学判断点：...】交给执行方联动 S01，不要擅自拍板，但数学证明本身照常推进。
5. 若上一版代码编译失败，错误已在材料末尾原样附上：先定位根因（不是表面），再给完整修正段，并说明为什么之前错。
6. 输出组织：极简要点说明 + 一个或多个 ```coq 代码块；不要寒暄；不要省略号、不要"此处略去"。
7. 【明性——先练会再动手，交付前自我终裁，不等执行方检查】
   (a) 练功：正式写目标证明前，先把它依赖的全部“小工具引理”（get/setby/split/length/option 等式等）在材料A里过一遍——已有则记名直接用；材料没有而你会用到的，先作为独立小引理逐个证到 Qed，再写主证明。绝不在主证明里临时抛出一个没证过、材料里也没有的名字。
   (b) 自裁：交付前你自己就是 coqc。逐行核对每个 apply/rewrite/exact/eapply 引用名是否在材料A存在、或在你本次代码块里已完整 Qed（induction 自动生成的 IHxxx 除外）。凡“用了但没着落”的名字，当场补证到 Qed，或确认是可 Require 的库引理并打 (* @stdlib names: .. *)。不许把带缺口的稿子交出去等执行方拦截回喂。
   (c) 辨真（双向压测，反例比证明更需要证据）：动手前先判断命题真假；线性系统里“头部任意插入弱化”这类不成立方向要主动识别，不硬证假命题。但【宣布一个全称命题为假】是和证出它同等严重的结论，必须先走完三步，缺一不可：
       ① 最小实例手算：至少取 nil、单元素、两元素三组最小具体 ctx，把命题逐位（get/setby/split）算一遍，确认结论在这些实例上确实不成立；
       ② 反向构造候选解：对 exists X,（P 且 Q）型结论，主动尝试用 nil、某个前提 ctx 本身、repeat None k 去 exists——【只要有任一候选解让结论成立，命题在该实例为真，禁止输出反例】；
       ③ 反例可独立编译：你交的 Lemma xxx_false : ~(forall...) 必须能脱离对话、Require 材料后【独立 coqc 编译 exit=0】；尤其逐行核对 option 双层——None（越界空）与 Some None（在位空）是两个不同的 get 层值，symmetry/exact 前确认等式两边是同一层，错层的反例必被守卫编译驳回。
       未走完①②③，只能说“我怀疑此处，需要核对”，绝不能写“假命题/反例/不存在”。执行方装有证伪守卫：反例独立编译失败、或候选解使实例成立，都会被机械推翻并原样回喂——请你自己先把这道门关在输出之前。
   (d) 一次交齐：主证明与其全部辅助引理在同一轮交齐到 Qed，宁可内部多证几个小引理，也不要留待下一轮补。
8. 【ctx 的 option 双层——本项目最易错点，写每个 match/Some/None 前先问自己在哪一层】
   ctx := list (option ty)，存在两层、绝不能混：
   - 元素层：列表里的东西、setby 的 f 的入参与返回值、split 逐位置等式两侧的位值。类型 option ty，构造子只有 None（空）| Some T（T:ty，持有资源）。
   - get 层：get G n 的返回值。类型 option (option ty)，三态 None=越界 | Some None=在位但空 | Some (Some T)=在位且持有 T；对它分支用 destruct ... as [[T|]|]（三分支）。
   - 两层换算：元素层值 e 对应 get 层 Some e；get 层 Some(Some T) 取出的元素层值是 Some T（不是 Some(Some T)）；元素层“空”就是 None（绝不是 Some None）。
   - setby (f:nat->option ty->option ty) Gamma k：f 吃元素层 t、必须【返回元素层 option ty】；给内层 match 显式写 “as r return option ty” 标注，让每个分支就地受类型检查，错层会立刻在分支内报错而不是留到最后。
   - 你最近连续几轮的错误（f 返回 option(option ty)、pattern 分支数不对、把 Some None 当元素层空）全是错层。交付前逐个 Some/None 标注它属于哪一层。"""

def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def stable_knowledge():
    """L1：system 固定前缀 + 结晶库（逐字带上，命中缓存）。"""
    return SYSTEM_PREFIX + "\n\n# 本项目已沉淀的证明方法论（智慧结晶库，必须遵守）\n" + _read(CRYSTAL)

def build_messages(task_brief, layer_files=("Layer1.v","Layer2.v"),
                   strategy_docs=(), philos_docs=(), coqc_error="", history=(), extra_notes=""):
    """层序"越稳定越靠前"：system | 稳定材料(Layer全文+策略+哲学) | 历史 | 本轮任务/错误。
    strategy_docs 相对 docs/协作机制；philos_docs 相对 docs/notes（生命论哲学智慧，让DS理解存在论主线）。"""
    msgs = [{"role":"system","content":stable_knowledge()}]
    mat = ["# 材料 A：Coq 源文件全文（权威，引理以这里为准）"]
    for lf in layer_files:
        src = _read(THEORIES / lf)
        mat.append(f"\n## ===== {lf} 全文开始 =====\n{src}\n## ===== {lf} 全文结束 =====")
    if strategy_docs:
        mat.append("\n# 材料 B：S01/S00 策略文档（参考，其断言需与材料A核对，可能有错）")
        for sd in strategy_docs:
            mat.append(f"\n## ----- {sd} -----\n" + _read(DOCS / sd))
    if philos_docs:
        mat.append("\n# 材料 C：生命论哲学智慧（S01研判/方法论，帮助你理解每个定义与证明步骤的存在论内涵，数学对错仍以coqc为准）")
        for pd in philos_docs:
            p = NOTES / pd
            if p.exists():
                mat.append(f"\n## ----- {pd} -----\n" + _read(p))
    msgs.append({"role":"user","content":"\n".join(mat)})
    for role, content in history:
        msgs.append({"role":role,"content":content})
    tail = ["# 本轮任务\n"+task_brief]
    if extra_notes:
        tail.append("\n# 补充说明（含已知勘误）\n"+extra_notes)
    if coqc_error.strip():
        tail.append("\n# 上一版 coqc 编译错误（原样，勿改写）\n```\n"+coqc_error+"\n```")
    msgs.append({"role":"user","content":"\n".join(tail)})
    return msgs

def approx_tokens(msgs):
    return sum(len(m["content"]) for m in msgs)//3

if __name__ == "__main__":
    # 离线审计：打包当前上下文，看体量与关键引理/结晶是否齐全（不调用 API、不花钱）
    brief = "审计用：检查全量上下文是否完整打包。"
    sd = (r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",)
    msgs = build_messages(brief, layer_files=("Layer1.v","Layer2.v"),
                          strategy_docs=tuple(p for p in sd if (DOCS/p).exists()))
    toks = approx_tokens(msgs)
    print("消息条数:",len(msgs)," 估算token:",toks," 占1M窗 %.1f%%"%(toks/1_000_000*100))
    for i,m in enumerate(msgs):
        print(f"  msg[{i}] {m['role']} len={len(m['content'])}")
    blob="\n".join(m["content"] for m in msgs)
    for k in ["typed_strengthen_unused","rho_inj_except_m","split_proj","结晶011","结晶012","subst_ren_general"]:
        print("  ", "OK " if k in blob else "缺失!!", k, blob.count(k))
