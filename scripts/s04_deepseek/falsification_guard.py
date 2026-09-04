# -*- coding: utf-8 -*-
"""
证伪守卫 falsification_guard —— 用代码彻底消灭"DS 说命题为假就盲信"的事故（2026-09-04 split_assoc 误判）。

事故复盘：DS v8 交了 split_assoc_false : ~(forall ...) 声称 split_assoc 是假命题，
执行方没有让该反例独立过 coqc，也没有反向构造候选解，就盲信并宣布"定理为假"、停用全部任务。
事后 coqc 硬验证：① split_assoc_false 根本编译不过（右支把 None=get G23 0 错当成 Some None=get G23 0）；
② 反例输入下 exists [] 直接使两个结论成立（原命题在该实例为真）。命题没写错，是反例写错了。

两道硬门（机械执行，不靠人眼、不靠自然语言自信）：
  门1【反例必独立编译】DS 交的任何 ~(forall ...) 否定引理，必须剥离后【独立 coqc 编译 exit=0】才算"反例成立"；
        编译失败 = 命题未被证伪 = 回喂 DS 继续证真。
  门2【反向候选解压测】即使门1通过，也自动把 DS 给的具体反例参数代入原命题，用一组候选解（nil、
        反例里出现过的每个具体 ctx、repeat None k）逐个 exists 尝试编译；【任一候选解使结论成立 = 反例被推翻】。
  裁决：
    - "no_claim"        DS 没宣布为假，走正常证明闭环；
    - "refuted_claim"   门1失败 或 门2找到成立解 → DS 的"为假"主张被推翻，回喂让其继续证真（附物证）；
    - "plausibly_false" 门1通过 且 门2所有候选都证不出 → 才允许 halt 闭环、冻结烧钱，带两份物证交 S01/S00/主人裁决，
                        【永不自动改判命题真假、永不自动改定理陈述】。

设计原则（接续结晶015：用可复核的机械校验代替主观侥幸）：
  - 候选解 × tactic 做笛卡尔积，交给 coqc 暴力枚举，不做精巧的语义推理；解析不出就退化为"只跑门1 + 留挑战模板"，绝不静默放行。
  - 全程落 trace/干渠物证。自带 __main__ 离线回归：用本次事故的真实文本当夹具，断言守卫能抓到错误反例。
路径走 _paths.py，不写死机器目录。
"""
import os, re, subprocess, datetime
from _paths import COQBIN, COQLIB, THEORIES, TRACE_DIR

# ---------------------------------------------------------------- 信号检测
# 自然语言层：DS 在"宣布目标命题为假"
_NL_PAT = re.compile(
    r"(假命题|是假的|为假|不成立|无法被?证明|不存在任何?|命题本身(就)?(是)?假|不能证(成|明)|反例)")
# 代码层：否定引理  name : ~ (forall ...)   或   name : not (forall ...)
_NEG_CODE = re.compile(r"(?:Lemma|Theorem|Fact|Corollary)\s+([\w']+)\s*:\s*~?\s*(?:\(\s*)?(?:not\s*)?\(\s*forall\b", re.S)

def detect_falsification(content, target, blocks=None):
    """返回 (是否在宣布target为假, 否定引理名或None, 触发理由)。代码信号优先且更强。"""
    blocks = blocks if blocks is not None else []
    for b in blocks:
        m = _NEG_CODE.search(b)
        if m:
            return True, m.group(1), "code:neg-forall"
    if target and re.search(re.escape(target), content) and _NL_PAT.search(content):
        return True, None, "nl:false-claim"
    if _NL_PAT.search(content) and re.search(r"~\s*\(\s*forall|not\s*\(\s*forall", content):
        return True, None, "nl:neg-forall"
    return False, None, ""

def extract_negation_block(blocks, neg_name=None):
    """取出否定引理所在代码块（含 ~ forall / not (forall 的块）。"""
    cands = []
    for b in blocks:
        if _NEG_CODE.search(b):
            cands.append(b)
    if neg_name:
        for b in cands:
            if re.search(r"(?:Lemma|Theorem)\s+"+re.escape(neg_name)+r"\b", b):
                return b
    return cands[0] if cands else None

# ---------------------------------------------------------------- 独立编译
def _compile_v(theories_dir, fname):
    cmd = ("set PATH=%s;%%PATH%% && set COQLIB=%s && cd /d %s && coqc.exe -R .. ALL %s 2>&1"
           % (COQBIN, COQLIB, theories_dir, fname))
    p = subprocess.run(["cmd", "/c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def _standalone_src(body, layer_files=("Layer1.v", "Layer2.v")):
    head = "From Stdlib Require Import List PeanoNat Lia ClassicalEpsilon.\n"
    for lf in layer_files:
        mod = os.path.splitext(lf)[0]
        head += "Require Import ALL.%s.\n" % mod
    head += "Import ListNotations.\n\n"
    return head + body.strip() + "\n"

def compile_negation_standalone(neg_block, layer_files=("Layer1.v", "Layer2.v"), tag="neg"):
    """门1：把否定引理剥离成独立文件编译。返回 (rc, err, path)。"""
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = "_guard_%s_%s.v" % (tag, ts)
    p = THEORIES / fname
    p.write_text(_standalone_src(neg_block, layer_files), encoding="utf-8")
    rc, err = _compile_v(str(THEORIES), fname)
    return rc, err, p

# -------------------------------------------------- 反例参数解析 & 反向候选解压测
# 抓 destruct (H G G12 G3 G1 G2 Hs1 Hs2) 里跟在 H 后的【具体 ctx 实参】序列
_DESTRUCT = re.compile(r"destruct\s*\(\s*[A-Za-z_][\w']*\s+((?:\[[^\]]*\]|\([^)]*\)|[A-Za-z_][\w']*)\s*(?:(?:\[[^\]]*\]|\([^)]*\)|[A-Za-z_][\w']*)\s*)*)\)", re.S)

def parse_instance_args(content):
    """从 DS 反例证明里抽取它实例化 forall 时用的具体 ctx 列表（字符串列表）。抽不到返回 []。"""
    m = _DESTRUCT.search(content)
    if not m:
        return []
    raw = m.group(1)
    # 以顶层空白切分，保留 [] 结构
    args = re.findall(r"\[[^\]]*\]|\([^)]*\)|[A-Za-z_][\w']*", raw)
    # 只保留看起来像 ctx 的（含 [ ] 或 nil/None），过滤掉假设名 Hs1/Hs2
    return [a for a in args if ("[" in a or "]" in a or a == "nil" or "None" in a)]

# 从否定引理里取 forall 的绑定变量名（按出现序），如 G G12 G3 G1 G2
_FORALL_BIND = re.compile(r"forall\s+(.*?),", re.S)
def _binders(neg_block):
    m = _FORALL_BIND.search(neg_block)
    if not m: return []
    return re.findall(r"[A-Za-z_][\w']*", m.group(1))

# 取 exists X, c1 /\ c2 的结论主体（去掉 forall 头与前提链），返回 (exists_var, concl)
_EXISTS = re.compile(r"exists\s+([A-Za-z_][\w']*)\s*,(.*)$", re.S)
def _split_conclusion(neg_block):
    # 只在命题陈述（第一个 Proof 之前）里提取，避免 exists 之后把证明体也吃进来
    stmt = re.split(r"\.\s*Proof\b", neg_block, maxsplit=1)[0]
    m = _EXISTS.search(stmt)
    if not m: return None, None
    concl = m.group(2).strip().rstrip(".").strip()        # 去陈述结尾句号
    if concl.endswith(")"): concl = concl[:-1].strip()    # 精确去掉与 ~( / (forall 外层配对的一个右括号
    return m.group(1), concl

def _substitute(text, mapping):
    # 用单词边界逐个替换绑定变量为具体实参（长名先替换，避免 G 误伤 G12）
    for name in sorted(mapping, key=len, reverse=True):
        text = re.sub(r"\b"+re.escape(name)+r"\b", mapping[name], text)
    return text

DEFAULT_CANDIDATES = ["[]", "nil", "[None]", "repeat None 0", "repeat None 1", "repeat None 2"]
# 本项目 split 类目标的默认通关 tactic（exists c 之后分别证两个 split）；可被外部 tactic 列表覆盖
DEFAULT_TACTICS = [
    "unfold split; intros [|n]; simpl; auto",
    "split; unfold split; intros [|n]; simpl; auto",
    "simpl; unfold split; intros [|n]; simpl; auto",
    "firstorder",
]

def build_challenges(neg_block, instance_args, candidates=None, tactics=None):
    """门2：把具体反例参数代入原命题，对每个候选解×tactic 生成独立 Example 源串。
    返回 [(candidate, tactic, src)]；若结构解析不出来返回 []（调用方据此退化为只跑门1）。"""
    binders = _binders(neg_block)
    ex_var, concl = _split_conclusion(neg_block)
    if not binders or not ex_var or not concl or not instance_args:
        return []
    # binders 数量可能多于 ctx 实参（前提假设名也在 forall 里）；只按位置对齐前 len(args) 个
    mapping = {}
    for i, arg in enumerate(instance_args):
        if i < len(binders):
            mapping[binders[i]] = arg
    concl_inst = _substitute(concl, mapping)
    candidates = candidates if candidates is not None else list(dict.fromkeys(instance_args + DEFAULT_CANDIDATES))
    tactics = tactics or DEFAULT_TACTICS
    out = []
    for c in candidates:
        for t in tactics:
            body = ("Example _challenge : exists %s, %s.\nProof. exists (%s). %s. Qed.\n"
                    % (ex_var, concl_inst, c, t))
            out.append((c, t, _standalone_src(body)))
    return out

def run_challenges(challenges, tag="challenge"):
    """逐个编译候选对抗，返回 (首个成功的(candidate,tactic) 或 None, 尝试记录列表)。"""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    records, winner = [], None
    for i, (c, t, src) in enumerate(challenges):
        fname = "_guard_%s_%d.v" % (tag, i)
        p = THEORIES / fname
        p.write_text(src, encoding="utf-8")
        rc, err = _compile_v(str(THEORIES), fname)
        records.append({"candidate": c, "tactic": t, "rc": rc, "err_head": err[:300]})
        for suf in (".v", ".vo", ".glob", ".vok", ".vos"):
            try: p.with_suffix(suf).unlink()
            except OSError: pass
        if rc == 0:
            winner = (c, t); break
    return winner, records

# ---------------------------------------------------------------- 总裁决
def adjudicate(content, blocks, target, layer_files=("Layer1.v", "Layer2.v"),
               candidates=None, tactics=None, log=print):
    """完整裁决。返回 dict：verdict ∈ no_claim/refuted_claim/plausibly_false，附物证。"""
    claimed, neg_name, why = detect_falsification(content, target, blocks)
    if not claimed:
        return {"verdict": "no_claim", "why": ""}
    log("[guard] 检测到 DS 宣布 %s 为假（%s, neg=%s），启动证伪守卫双门" % (target, why, neg_name))
    neg_block = extract_negation_block(blocks, neg_name)
    evidence = {"target": target, "why": why, "neg_name": neg_name, "ts": datetime.datetime.now().isoformat()}

    # 门1：反例独立编译
    if neg_block is None:
        # 只有自然语言宣称、没交可编译否定引理 → 主张无物证，直接判不成立
        evidence["gate1"] = "no_negation_block"
        log("[guard] 门1：DS 只在自然语言里宣称假、未交可编译的否定引理 → 主张无物证，refuted_claim")
        evidence["verdict"] = "refuted_claim"
        evidence["feedback"] = ("你声称目标引理 %s 为假，但没有交出可独立编译通过的 ~(forall...) 反例引理。"
                                "在交不出编译通过的反例之前，命题默认仍为真：请继续为它构造证明；若确有反例，"
                                "必须给出 Lemma ... : ~(forall...) 从 Lemma 到 Qed 的完整可编译证明。" % target)
        return evidence
    rc1, err1, path1 = compile_negation_standalone(neg_block, layer_files)
    evidence["gate1_rc"] = rc1
    evidence["gate1_neg_src"] = neg_block[:1200]   # 源串作物证留存
    # 门1临时文件编译后即清理（rc/err 已留证），避免污染 theories/ALL 的后续编译
    for suf in (".v", ".vo", ".glob", ".vok", ".vos"):
        try: path1.with_suffix(suf).unlink()
        except OSError: pass
    if rc1 != 0:
        evidence["gate1_err_head"] = err1[:600]
        log("[guard] 门1：反例否定引理独立编译失败 exit=%d → 命题未被证伪，refuted_claim" % rc1)
        evidence["verdict"] = "refuted_claim"
        evidence["feedback"] = ("你给出的反例否定引理【独立编译失败】（exit=%d），错误：\n%s\n"
                                "也就是说你的反例本身不成立，目标引理并未被证伪。请逐行核对反例证明"
                                "（特别小心 option 双层：None=越界空 与 Some None=在位空 不可混；symmetry/exact 前核对等式两边到底是哪一层的值），"
                                "修正后要么交出编译通过的反例，要么回到证明目标引理为真的轨道。" % (rc1, err1[:800]))
        return evidence
    log("[guard] 门1通过：反例否定引理独立编译 exit=0，进入门2反向候选解压测")

    # 门2：反向候选解
    inst = parse_instance_args(content + "\n" + neg_block)
    evidence["instance_args"] = inst
    challenges = build_challenges(neg_block, inst, candidates=candidates, tactics=tactics)
    if not challenges:
        # 解析不出对抗实例：不静默放行，判疑似为假交人，但标注门2未机械执行
        evidence["gate2"] = "unparsed"
        evidence["verdict"] = "plausibly_false"
        log("[guard] 门2：无法从反例解析实例化参数，未机械执行候选压测 → plausibly_false 交人工，禁止自动改判")
        return evidence
    winner, records = run_challenges(challenges)
    evidence["gate2_attempts"] = len(records)
    evidence["gate2_records_head"] = records[:6]
    if winner is not None:
        c, t = winner
        evidence["gate2_winner"] = {"candidate": c, "tactic": t}
        log("[guard] 门2：候选解 %s 使原命题实例成立（%s）→ 反例被推翻，refuted_claim" % (c, t))
        evidence["verdict"] = "refuted_claim"
        evidence["feedback"] = ("你的反例被推翻：在你给的具体参数下，取 exists (%s) 即可使原命题结论编译成立"
                                "（通关 tactic: %s）。即该实例下命题为真、不存在你声称的矛盾。请回到证明目标引理为真的轨道，"
                                "不要再输出为假结论。" % (c, t))
        return evidence
    log("[guard] 门2：%d 组候选解×tactic 均无法使实例成立，且门1反例编译通过 → plausibly_false，halt 交人工裁决" % len(records))
    evidence["verdict"] = "plausibly_false"
    return evidence

# ================================================================== 离线回归自检
if __name__ == "__main__":
    # —— 夹具1：本次 split_assoc 事故里 DS 交的错误反例（原样，含右支 None/Some None 错误）——
    ds_false_block = '''Lemma split_assoc_false :
  ~ (forall G G12 G3 G1 G2,
       split G G12 G3 -> split G12 G1 G2 ->
       exists G23, split G G1 G23 /\\ split G23 G2 G3).
Proof.
  intros H.
  assert (Hs1 : split [] [None] []).
  { unfold split. intros [|n]; simpl; auto. }
  assert (Hs2 : split [None] [None] [None]).
  { unfold split. intros [|n]; simpl; auto. }
  destruct (H [] [None] [] [None] [None] Hs1 Hs2) as [G23 [HsL HsR]].
  unfold split in HsL, HsR.
  specialize (HsL 0). specialize (HsR 0).
  assert (HG23R : get G23 0 = Some None).
  { destruct HsR as [[Hleft _] | [Hright _]].
    - simpl in Hleft. symmetry. exact Hleft.
    - simpl in Hright. symmetry. exact Hright. }
  admit.
Admitted.'''
    ds_content = "目标引理 split_assoc 是假命题，反例 G=[] G12=[None] G3=[] G1=[None] G2=[None]。\n```coq\n"+ds_false_block+"\n```"

    print("== 自检1：信号检测 ==")
    claimed, name, why = detect_falsification(ds_content, "split_assoc", [ds_false_block])
    assert claimed, "应检测到证伪声明"
    print("  claimed=%s neg=%s why=%s" % (claimed, name, why))

    print("== 自检2：反例参数解析 ==")
    args = parse_instance_args(ds_false_block)
    print("  instance args =", args)
    assert args == ["[]", "[None]", "[]", "[None]", "[None]"], args

    print("== 自检3：对抗实例生成（不编译，只看结构）==")
    ch = build_challenges(ds_false_block, args)
    assert ch, "应生成候选对抗"
    print("  生成 %d 组 候选×tactic；示例候选: %s" % (len(ch), sorted(set(c for c,_,_ in ch))))

    print("== 自检4：完整裁决（门1应编译失败 → refuted_claim；若环境无coqc则跳过强断言）==")
    verdict = adjudicate(ds_content, [ds_false_block], "split_assoc",
                         log=lambda *a: print("   ", *a))
    print("  verdict =", verdict.get("verdict"), "| gate1_rc =", verdict.get("gate1_rc"),
          "| winner =", verdict.get("gate2_winner"))
    assert verdict["verdict"] in ("refuted_claim", "plausibly_false")
    # 在装有 Rocq 的本机：门1必须抓到 DS 反例编译失败
    if verdict.get("gate1_rc") not in (None,) and "gate1_rc" in verdict:
        assert verdict["gate1_rc"] != 0 or verdict.get("gate2_winner") is not None, \
            "事故反例必须被门1编译失败或门2候选解推翻"

    print("== 自检5：正常证明文本不应触发守卫 ==")
    ok_text = "Lemma split_assoc : forall G, True. Proof. intros. exact I. Qed."
    v5 = adjudicate(ok_text, [ok_text], "split_assoc")
    assert v5["verdict"] == "no_claim", v5
    print("  verdict =", v5["verdict"], "OK")
    print("\n[falsification_guard] 离线自检全部通过。")
