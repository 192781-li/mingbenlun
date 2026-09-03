# -*- coding: utf-8 -*-
"""
S04 agentic 证明闭环 —— DS 是主证明者，本模块只做本地执行与回喂（S04 只有 coqc 执行权）。
循环：build_messages -> DS(思考,给足token) -> 抽coq -> 来源标签分流/编造校验/卫生检查
      -> 备份 -> 整段替换/去重插入 -> coqc -> 绿且【目标段+本轮新引理】无 admit/Abort 则收敛；
      否则完整错误原样回喂进入下一轮。
v2(2026-09-04) 依《外部引理与知识来源登记规范》升级：
  - known_src 每轮刷新（修“上一轮证入、下一轮被误判编造”）
  - @stdlib 标签豁免并交 coqc 终裁；@prove/@cite 必须当轮带完整 Qed；无标签未定义名拦截
  - 拦截 Abort 废块、块内/与文件同名重复定义；INSERT 已存在引理自动去重
  - 收敛判据覆盖本轮 INSERT 的全部辅助引理（不许辅助引理留 admit）
安全：每轮改文件前整文件备份(.bak_rN)。路径走 _paths.py。
"""
import os, re, shutil, subprocess, datetime
from ds_v4 import chat
from s04_context import build_messages, approx_tokens
from _paths import COQC, COQBIN, COQLIB, THEORIES, CHANNEL

def extract_coq_blocks(content):
    return [b.strip() for b in re.findall(r"```(?:coq|Coq)?\s*\n(.*?)```", content, flags=re.S)]

_TOP = r"(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Let)"

def lemma_span(src, name):
    """从 Lemma/Theorem <name> 起，到第一个行尾结束标记 Qed./Admitted./Defined./Abort. 止（含）。
    结束标记允许列0单独成行，也允许跟在 'Proof. ' 同行（如 'Proof. Admitted.'）。找不到 None。"""
    m = re.search(r"(?m)^(?:Lemma|Theorem|Fact|Corollary)\s+"+re.escape(name)+r"\b", src)
    if not m: return None
    tail = re.search(r"(?m)(Qed\.|Admitted\.|Defined\.|Abort\.)\s*$", src[m.end():])
    if not tail: return None
    return m.start(), m.end()+tail.end()

def _top_defined_names(text):
    return set(re.findall(r"(?m)^\s*"+_TOP+r"\s+([\w']+)", text))

def apply_patch(file_path, target_lemma, blocks):
    """按协议应用 DS 代码块，返回 (ok, msg, new_src, inserted, mode)。
    mode: "replace"=本轮交了目标lemma并替换；"insert_only"=本轮只交辅助引理，先插到目标前沉淀；"none"=无可应用。
    辅助引理允许分步交（insert_only 逐轮沉淀）；若 DS 重发【同名】辅助引理，视为修正版：切除文件中旧同名段、
    以新版替换（这样已沉淀但有编译错的辅助引理修得动，不会被"去重"跳过锁死）；纯噪声块（markdown 残留）丢弃。"""
    src = open(file_path, encoding="utf-8").read()
    existing = _top_defined_names(src)
    work = src                       # 动态工作串：同名旧段在此切除
    insert_before, new_lemma, skipped = [], None, []
    def _cut_name(text, name):
        sp = lemma_span(text, name)
        return (text[:sp[0]]+text[sp[1]:], True) if sp else (text, False)
    for b in blocks:
        body = re.sub(r"(?m)^\s*\(\*\s*INSERT-BEFORE:.*?\*\)\s*\n","",b).strip()
        if re.search(r"(?m)^(?:Lemma|Theorem)\s+"+re.escape(target_lemma)+r"\b", body):
            if new_lemma is not None:
                return False, "多个代码块都定义了目标lemma，拒绝盲改", src, [], "none"
            new_lemma = body
        elif body:
            # 噪声块（markdown 标题/纯说明，不含任何 Coq 顶层定义）直接丢弃，不插入 .v
            if not re.search(r"(?m)^\s*(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Inductive|Let)\b", body):
                skipped.append(["<噪声块,非顶层定义,丢弃>"]); continue
            names = _top_defined_names(body)
            for nm in sorted(names & existing):   # 同名：切除旧段，以本轮新版替换（修正错误版）
                work, did = _cut_name(work, nm)
                if did: skipped.append(["替换旧版:"+nm])
            insert_before.append(body); existing |= names
    span = lemma_span(work, target_lemma)
    if new_lemma is None:
        if not insert_before:
            return False, "DS 输出中没有目标 lemma %s 的完整新版本，也没有任何新引理" % target_lemma, src, [], "none"
        if not span:
            return False, "源文件中定位不到 lemma %s 的起止" % target_lemma, src, [], "none"
        ins = "\n\n".join(insert_before)+"\n\n"
        msg = "仅插入辅助引理%d段（本轮未交主引理，先沉淀，下一轮交主引理）"%len(insert_before)
        if skipped: msg += "；处理:%s"%skipped
        return True, msg, work[:span[0]]+ins+work[span[0]:], insert_before, "insert_only"
    if not span:
        return False, "源文件中定位不到 lemma %s 的起止" % target_lemma, src, [], "none"
    s,e = span
    ins = ("\n\n".join(insert_before)+"\n\n") if insert_before else ""
    msg = "替换目标lemma并插入%d段新引理"%len(insert_before)
    if skipped: msg += "；处理:%s"%skipped
    return True, msg, work[:s]+ins+new_lemma+work[e:], insert_before, "replace"

def run_coqc(theories_dir, fname):
    cmd = ("set PATH=%s;%%PATH%% && set COQLIB=%s && cd /d %s && coqc.exe -R .. ALL %s 2>&1"
           % (COQBIN, COQLIB, theories_dir, fname))
    p = subprocess.run(["cmd","/c",cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "")+(p.stderr or "")

def append_channel(target, rnd, tag, text):
    try:
        CHANNEL.parent.mkdir(parents=True, exist_ok=True)
        ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(CHANNEL,"a",encoding="utf-8") as f:
            f.write("\n\n## %s [proof_loop] %s · round%d · %s\n\n%s\n"%(ts,target,rnd,tag,text))
    except Exception as e:
        print("[channel warn]",e)

_BUILTIN = set("""intros intro induction destruct inversion subst simpl reflexivity symmetry rewrite
erewrite eapply apply exact eexact constructor econstructor auto eauto lia tauto contradiction
discriminate injection unfold fold change assert generalize revert rename clear set remember
left right split f_equal exfalso exists dependent specialize assumption trivial
nat_rec eq_refl I True False and or not iff ex Some None O S nil cons list nat Type Prop
eq_ind eq_ind_r eq_rec eq_sym f_equal2 f_equal3 Nat PeanoNat List Lia ClassicalEpsilon
ltac_match match if then else fun forall let in end with as return where by repeat try
do at once first solve intuition congruence omega nia ring field cbv cbn hnf compute lazy
vm_compute native_compute admit Admitted Qed Defined Proof Lemma Theorem Fixpoint Definition
Inductive CoFixpoint Corollary Example Remark Fact Class Instance Structure""".split())

def _defined_names(blocks):
    names=set()
    for b in blocks:
        names |= _top_defined_names(b)
    return names

def _local_names(blocks):
    local=set(); txt="\n".join(blocks)
    for m in re.finditer(r"intros\s+([^.]*)\.", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"(?:induction|destruct)\s+([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    # as 模式：把 as 后整段绑定模式（允许 [[..]|[..]] 嵌套、(|..&..)、| , 空格）吃到 . ; 换行，再提标识符
    for m in re.finditer(r"\bas\s+([\[\]\(\)\|\w'\s&,]+?)[.;\n]", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"\bas\s+([A-Za-z_][\w']*)", txt): local.add(m.group(1))  # as name（不带括号）
    for m in re.finditer(r"forall\s+([^,]+),", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"fun\s+([^=]+)=>", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"(?:assert|set|remember|pose)\s*\(?\s*([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    for m in re.finditer(r"specialize\s+([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    # eqn:NAME / eqn : NAME / eqn:(NAME)：destruct/inversion/case 用 eqn 绑定的等式假设名（如 destruct .. eqn:EG）
    for m in re.finditer(r"\beqn\s*:\s*\(?([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    return local

def parse_stdlib_names(content, blocks):
    """提取 (* @stdlib names: a, b, c *) 中显式声明、交 coqc 终裁的库引理名。"""
    names=set()
    for m in re.finditer(r"@stdlib[^\n*]*?names\s*:\s*([^*)]+)", content+"\n"+"\n".join(blocks)):
        names |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    return names

def check_hygiene(blocks):
    """卫生检查：不许 Abort 废块；块内不许同名重复定义。返回问题列表。"""
    issues=[]
    for i,b in enumerate(blocks):
        if re.search(r"\bAbort\.", b):
            issues.append("代码块%d 含 Abort. 废块（草稿不许入库，请只交 Qed 成品）"%(i+1))
    seen={}
    for b in blocks:
        for n in _top_defined_names(b):
            seen[n]=seen.get(n,0)+1
    dup=sorted(n for n,c in seen.items() if c>1)
    if dup: issues.append("同名定义在本轮重复出现: %s（每个引理只给一份）"%dup)
    return issues

def check_referenced_lemmas(blocks, known_src, extra_known=None):
    """抓 apply/rewrite/exact 引用、但材料/本块/局部/白名单/显式声明都没有的名字（防编造）。"""
    known=set(re.findall(r"(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Inductive|CoInductive|Let|Notation)\s+([\w']+)", known_src))
    for im in re.finditer(r"Inductive\s+[A-Za-z_][\w']*[^.]*?:=(.*?)\.", known_src, flags=re.S):
        known |= set(re.findall(r"[A-Za-z_][\w']*", im.group(1)))
    known |= set(re.findall(r"[A-Za-z_][\w']*", known_src))   # 全文完整词兜底
    known |= _defined_names(blocks); known |= _local_names(blocks); known |= _BUILTIN
    if extra_known: known |= extra_known
    missing={}
    pat=re.compile(r"(?:e?apply|erewrite|rewrite|e?exact)\s+(?:@\s*)?([A-Za-z_][\w']*)")
    for b in blocks:
        for m in pat.finditer(b):
            ident=m.group(1)
            if ident in known: continue
            if ident.startswith("IH"): continue   # induction 自动生成的归纳假设 IHtyped/IHtyped1..
            missing.setdefault(ident,0); missing[ident]+=1
    return sorted(missing)

def detect_need(content):
    return re.findall(r"(?m)^\s*NEED:\s*(.+)$", content)

def _read_known(theories_dir, layer_files):
    s=""
    for lf in layer_files:
        p=os.path.join(theories_dir, lf)
        s += open(p,encoding="utf-8").read() if os.path.exists(p) else ""
    return s

def proof_loop(task_brief, file_path, target_lemma, theories_dir=None, layer_files=("Layer1.v","Layer2.v"),
               strategy_docs=(), philos_docs=(), extra_notes="", model="deepseek-v4-pro", max_rounds=5, log=print):
    theories_dir = theories_dir or str(THEORIES)
    fname = os.path.basename(file_path)
    history=[]; coqc_error=""; result={"rounds":[],"converged":False}
    for rnd in range(1,max_rounds+1):
        known_src = _read_known(theories_dir, layer_files)   # v2: 每轮刷新，收录上一轮新证入的引理
        msgs = build_messages(task_brief, layer_files=layer_files, strategy_docs=strategy_docs,
                              philos_docs=philos_docs, coqc_error=coqc_error, history=history,
                              extra_notes=extra_notes)
        log("[round %d] 上下文约 %d token，调用 %s ..."%(rnd, approx_tokens(msgs), model))
        out = chat(msgs, model=model, thinking="enabled", max_tokens=32000,
                   task_name="proofloop_%s_r%d"%(target_lemma,rnd))
        log("[round %d] status=%s finish=%s rounds=%d 输出%d字符 reasoning%d字符 费用%.4f元"
            %(rnd,out["status"],out["finish"],out["rounds"],len(out["content"]),len(out["reasoning"]),out["cost_yuan"]))
        append_channel(target_lemma,rnd,"DS输出",out["content"][:2000]+"\n[reasoning摘要]\n"+out["reasoning"][:1500])
        needs = detect_need(out["content"])
        if needs:
            log("[round %d] DS 声明缺材料：%s，回喂引导"%(rnd,needs))
            history += [("assistant",out["content"][:6000]),
                        ("user","材料A已包含 %s 完整全文，请在其中检索；若确属外部缺失，按来源规范打 @stdlib/@cite 标签，不要用无名未定义名。"%("、".join(layer_files)))]
            result["rounds"].append({"r":rnd,"need":needs}); continue
        blocks = extract_coq_blocks(out["content"])
        hyg = check_hygiene(blocks)
        if hyg:
            log("[round %d] 卫生检查不过 %s，不改文件，回喂"%(rnd,hyg))
            history += [("assistant",out["content"][:6000]),
                        ("user","输出卫生问题：%s。请去掉 Abort 草稿、每个引理只保留一份成品（Lemma..Qed.），主定理用到的辅助引理当轮全部以 INSERT-BEFORE 成品块交齐，重给完整版本。"%hyg)]
            result["rounds"].append({"r":rnd,"hygiene":hyg}); continue
        stdlib = parse_stdlib_names(out["content"], blocks)
        if stdlib: log("[round %d] @stdlib声明(交coqc终裁,记得登记台账): %s"%(rnd,sorted(stdlib)))
        missing = check_referenced_lemmas(blocks, known_src, extra_known=stdlib)
        if missing:
            log("[round %d] 未定义名 %s（无@prove完整证明/@stdlib声明），不改文件，回喂"%(rnd,missing))
            history += [("assistant",out["content"][:6000]),
                        ("user","你引用了 %s，但材料A、本轮代码块定义中都不存在。按来源规范处置：①自证辅助引理：当轮用 INSERT-BEFORE 块连完整 Qed 证明一起给；②确属Coq库已证引理：打 (* @stdlib names: .. *) 并确保已 Require Import；③文献结论：打 @cite 但仍须本库重证。禁止只留名字。重给完整版本。"%missing)]
            result["rounds"].append({"r":rnd,"missing":missing}); continue
        bak = file_path + (".bak_r%d"%rnd)
        shutil.copy2(file_path, bak)
        ok,msg,new_src,inserted,mode = apply_patch(file_path,target_lemma,blocks)
        if not ok:
            log("[round %d] 未改文件：%s，回喂"%(rnd,msg))
            history += [("assistant",out["content"][:6000]),
                        ("user","输出无法应用：%s。请严格按协议给目标 Lemma %s 从 Lemma 行到 Qed. 的完整新版本，新引理用 INSERT-BEFORE 标记。"%(msg,target_lemma))]
            result["rounds"].append({"r":rnd,"apply":msg}); continue
        open(file_path,"w",encoding="utf-8").write(new_src)
        rc,err = run_coqc(theories_dir,fname)
        full = open(file_path,encoding="utf-8").read()
        span = lemma_span(full,target_lemma)
        seg = full[span[0]:span[1]] if span else ""
        ins_txt = "\n".join(inserted)
        bad = lambda t: ("admit" in t) or ("Abort." in t)
        tgt_bad, ins_bad = bad(seg), bad(ins_txt)
        if mode == "insert_only":
            # 分步交：本轮只沉淀辅助引理。编译过且辅助无 admit 就算沉淀成功，不收敛，下轮交主引理。
            log("[round %d] 辅助沉淀 coqc exit=%d 新引理admit/abort=%s"%(rnd,rc,ins_bad))
            result["rounds"].append({"r":rnd,"mode":"insert_only","apply":msg,"coqc_rc":rc,"err_head":err[:400]})
            if rc==0 and not ins_bad:
                names=[n for b in inserted for n in _top_defined_names(b)]
                history += [("assistant",out["content"][:6000]),
                            ("user","辅助引理 %s 已收录进文件且 coqc 编译通过，无需重证，下一轮可直接引用。现在【只】需给出目标 Lemma %s 从 Lemma 行到 Qed. 的完整证明块（不要再只交辅助引理，也不要重复已收录的），并保证它引用的名字都已在材料A或已收录引理中。"%(names,target_lemma))]
            else:
                coqc_error = err if err.strip() else ("exit=%d；新引理问题=%s"%(rc,ins_bad))
                history += [("assistant",out["content"][:6000]),
                            ("user","刚插入的辅助引理编译未过（rc=%s，新引理admit/abort=%s）。错误见材料末尾，请修正这些辅助引理后重交，然后再给主引理 %s。"%(rc,ins_bad,target_lemma))]
            continue
        log("[round %d] coqc exit=%d 目标段admit=%s 新引理admit/abort=%s"%(rnd,rc,tgt_bad,ins_bad))
        if rc==0 and not tgt_bad and not ins_bad:
            log("[round %d] ✅ 编译通过且目标+新引理均无admit，收敛"%rnd)
            result.update(converged=True,final_round=rnd,backup=bak); break
        coqc_error = err if err.strip() else ("exit=%d 但无错误文本；目标段admit=%s 新引理问题=%s"%(rc,tgt_bad,ins_bad))
        history += [("assistant",out["content"][:6000]),
                    ("user","应用后未收敛（rc=%s，目标段admit=%s，新引理admit/abort=%s）。完整错误见材料末尾，定位根因并给完整修正版；主定理用到的全部辅助引理当轮交齐到 Qed，不许 Abort/Admitted。"%(rc,tgt_bad,ins_bad))]
        result["rounds"].append({"r":rnd,"apply":msg,"coqc_rc":rc,"err_head":err[:400]})
    return result

if __name__ == "__main__":
    import tempfile
    sample='''说明。
```coq
(* INSERT-BEFORE: foo *)
Lemma helper : True. Proof. exact I. Qed.
```
```coq
Lemma foo : True.
Proof. exact I. Qed.
```
'''
    blks=extract_coq_blocks(sample); print("blocks:",len(blks))
    with tempfile.NamedTemporaryFile("w",suffix=".v",delete=False,encoding="utf-8") as f:
        f.write("Lemma foo : False.\nProof. admit.\nAdmitted.\n"); tmp=f.name
    ok,msg,new,ins,mode=apply_patch(tmp,"foo",blks)
    print("apply(replace):",ok,mode,msg); print(new)
    print("编造检查(应为空):",check_referenced_lemmas(blks,"Lemma foo : False."))
    print("卫生(应空):",check_hygiene(blks))
    # insert_only：本轮只交辅助引理，应插到 foo 前且 mode=insert_only
    with tempfile.NamedTemporaryFile("w",suffix=".v",delete=False,encoding="utf-8") as f:
        f.write("Lemma foo : False.\nProof. admit.\nAdmitted.\n"); tmp2=f.name
    ok2,msg2,new2,ins2,mode2=apply_patch(tmp2,"foo",blks[:1])
    print("apply(insert_only):",ok2,mode2,msg2,"| helper在foo前:", new2.index("helper")<new2.index("Lemma foo"), "| foo仍Admitted:", "Admitted." in new2)
    # 同名替换：文件里已有错误版 helper(Admitted)，本轮给 Qed 新版，应切除旧版、只留一份新版
    with tempfile.NamedTemporaryFile("w",suffix=".v",delete=False,encoding="utf-8") as f:
        f.write("Lemma helper : True. Proof. Admitted.\n\nLemma foo : False.\nProof. admit.\nAdmitted.\n"); tmp3=f.name
    ok3,msg3,new3,ins3,mode3=apply_patch(tmp3,"foo",blks)
    print("apply(同名替换):",ok3,mode3,msg3,"| helper只出现一次:", new3.count("Lemma helper")==1,
          "| 旧Admitted版已切除:", "Proof. Admitted." not in new3)
    abort=blks+["Lemma x:True. Proof. Abort."]
    print("卫生(应抓到Abort):",check_hygiene(abort))
    import os as _os; _os.remove(tmp); _os.remove(tmp2); _os.remove(tmp3)
