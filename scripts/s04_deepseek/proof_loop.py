# -*- coding: utf-8 -*-
"""
S04 agentic 证明闭环 —— DS 是主证明者，本模块只做本地执行与回喂（S04 只有 coqc 执行权）。
循环：build_messages -> DS(思考,给足token) -> 抽coq -> 编造引理校验 -> 备份 -> 整段替换/插入
      -> coqc -> 绿且目标段无 admit 则收敛；否则完整错误原样回喂进入下一轮。
安全：每轮改文件前整文件备份(.bak_rN)；锚点不唯一/找不到/引用未定义名 -> 不改文件直接回喂。
路径走 _paths.py。
"""
import os, re, shutil, subprocess, datetime, tempfile
from ds_v4 import chat
from s04_context import build_messages, approx_tokens
from _paths import COQC, COQBIN, COQLIB, THEORIES, CHANNEL

def extract_coq_blocks(content):
    return [b.strip() for b in re.findall(r"```(?:coq|Coq)?\s*\n(.*?)```", content, flags=re.S)]

def lemma_span(src, name):
    """从 Lemma/Theorem <name> 起，到列0 的 Qed./Admitted./Defined. 止（含）。找不到 None。"""
    m = re.search(r"(?m)^(?:Lemma|Theorem|Fact|Corollary)\s+"+re.escape(name)+r"\b", src)
    if not m: return None
    tail = re.search(r"(?m)^(Qed\.|Admitted\.|Defined\.)\s*$", src[m.end():])
    if not tail: return None
    return m.start(), m.end()+tail.end()

def apply_patch(file_path, target_lemma, blocks):
    """按协议应用 DS 代码块，返回 (ok, msg, new_src)。"""
    src = open(file_path, encoding="utf-8").read()
    insert_before, new_lemma = [], None
    for b in blocks:
        re.search(r"\(\*\s*INSERT-BEFORE:\s*([\w']+)\s*\*\)", b)
        body = re.sub(r"(?m)^\s*\(\*\s*INSERT-BEFORE:.*?\*\)\s*\n","",b).strip()
        if re.search(r"(?m)^(?:Lemma|Theorem)\s+"+re.escape(target_lemma)+r"\b", body):
            if new_lemma is not None:
                return False, "多个代码块都定义了目标lemma，拒绝盲改", src
            new_lemma = body
        elif body:
            insert_before.append(body)
    if new_lemma is None:
        return False, "DS 输出中没有目标 lemma %s 的完整新版本" % target_lemma, src
    span = lemma_span(src, target_lemma)
    if not span:
        return False, "源文件中定位不到 lemma %s 的起止" % target_lemma, src
    s,e = span
    ins = ("\n\n".join(insert_before)+"\n\n") if insert_before else ""
    return True, "替换目标lemma并插入%d段新引理"%len(insert_before), src[:s]+ins+new_lemma+src[e:]

def run_coqc(theories_dir, fname):
    cmd = ("set PATH=%s;%%PATH%% && set COQLIB=%s && cd /d %s && coqc.exe -R .. ALL %s 2>&1"
           % (COQBIN, COQLIB, theories_dir, fname))
    p = subprocess.run(["cmd","/c",cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "")+(p.stderr or "")

def append_channel(target, rnd, tag, text):
    """每轮 DS 调用/判断留痕到 DeepSeek干渠.md（只追加）。"""
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
        for m in re.finditer(r"(?m)^\s*(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Let)\s+([\w']+)", b):
            names.add(m.group(1))
    return names

def _local_names(blocks):
    local=set(); txt="\n".join(blocks)
    for m in re.finditer(r"intros\s+([^.]*)\.", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"(?:induction|destruct)\s+([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    for m in re.finditer(r"as\s+([\[\]\(\)\|\w'\s]+?)(?:,|=>|\.|$)", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"forall\s+([^,]+),", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"fun\s+([^=]+)=>", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"(?:assert|set|remember|pose)\s*\(?\s*([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    for m in re.finditer(r"specialize\s+([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    return local

def check_referenced_lemmas(blocks, known_src):
    """抓 apply/rewrite/exact 引用、但材料/本块/局部/白名单都没有的名字（防编造）。
    判据（2026-09-03 修正假阳性）：
      - 顶层声明名 + Inductive 构造子名 + 【Layer全文出现过的完整词】(兜底,覆盖 ty_in 等构造子、Bool 等模块名)
        + 块内自定义名/局部绑定名 + Coq 白名单 一并视为合法；
      - 只有"全文从未出现、块内也没给出其 Lemma 定义"的纯凭空名才判编造；
        DS 若用 INSERT-BEFORE 完整证明了某新引理，_defined_names 会收录并放行，最终由 coqc 终裁。"""
    known=set(re.findall(r"(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Inductive|CoInductive|Let|Notation)\s+([\w']+)", known_src))
    for im in re.finditer(r"Inductive\s+[A-Za-z_][\w']*[^.]*?:=(.*?)\.", known_src, flags=re.S):
        known |= set(re.findall(r"[A-Za-z_][\w']*", im.group(1)))
    known |= set(re.findall(r"[A-Za-z_][\w']*", known_src))   # 全文完整词兜底
    known |= _defined_names(blocks); known |= _local_names(blocks); known |= _BUILTIN
    missing={}
    pat=re.compile(r"(?:e?apply|erewrite|rewrite|e?exact)\s+(?:@\s*)?([A-Za-z_][\w']*)")
    for b in blocks:
        for m in pat.finditer(b):
            ident=m.group(1)
            if ident in known: continue
            missing.setdefault(ident,0); missing[ident]+=1
    return sorted(missing)

def detect_need(content):
    return re.findall(r"(?m)^\s*NEED:\s*(.+)$", content)

def proof_loop(task_brief, file_path, target_lemma, theories_dir=None, layer_files=("Layer1.v","Layer2.v"),
               strategy_docs=(), philos_docs=(), extra_notes="", model="deepseek-v4-pro", max_rounds=5, log=print):
    theories_dir = theories_dir or str(THEORIES)
    fname = os.path.basename(file_path)
    history=[]; coqc_error=""; result={"rounds":[],"converged":False}
    known_src = ""
    for lf in layer_files:
        p=os.path.join(theories_dir, lf)
        known_src += open(p,encoding="utf-8").read() if os.path.exists(p) else ""
    for rnd in range(1,max_rounds+1):
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
                        ("user","材料A已包含 %s 完整全文，请在其中检索；若确属外部缺失，明确名字与用途，不要用未定义名。"%("、".join(layer_files)))]
            result["rounds"].append({"r":rnd,"need":needs}); continue
        blocks = extract_coq_blocks(out["content"])
        missing = check_referenced_lemmas(blocks, known_src)
        if missing:
            log("[round %d] 疑似编造/未定义引理 %s，不改文件，回喂"%(rnd,missing))
            history += [("assistant",out["content"][:6000]),
                        ("user","你引用了 %s，但材料A与本块定义中都不存在。禁止未定义名：要么作为新引理完整证明，要么改用真实存在的引理，重给完整版本。"%missing)]
            result["rounds"].append({"r":rnd,"missing":missing}); continue
        bak = file_path + (".bak_r%d"%rnd)
        shutil.copy2(file_path, bak)
        ok,msg,new_src = apply_patch(file_path,target_lemma,blocks)
        if not ok:
            log("[round %d] 未改文件：%s，回喂"%(rnd,msg))
            history += [("assistant",out["content"][:6000]),
                        ("user","输出无法应用：%s。请严格按协议给目标 Lemma %s 从 Lemma 行到 Qed. 的完整新版本，新引理用 INSERT-BEFORE 标记。"%(msg,target_lemma))]
            result["rounds"].append({"r":rnd,"apply":msg}); continue
        open(file_path,"w",encoding="utf-8").write(new_src)
        rc,err = run_coqc(theories_dir,fname)
        span = lemma_span(open(file_path,encoding="utf-8").read(),target_lemma)
        seg = open(file_path,encoding="utf-8").read()[span[0]:span[1]] if span else ""
        has_admit = ("admit" in seg)
        log("[round %d] coqc exit=%d 目标段含admit=%s"%(rnd,rc,has_admit))
        if rc==0 and not has_admit:
            log("[round %d] ✅ 编译通过且目标lemma无admit，收敛"%rnd)
            result.update(converged=True,final_round=rnd,backup=bak); break
        coqc_error = err if err.strip() else ("exit=%d 但无错误文本；目标段仍含 admit"%rc)
        history += [("assistant",out["content"][:6000]),
                    ("user","应用后 coqc 未通过（rc=%s），目标段含admit=%s。完整错误见材料末尾，定位根因并给完整修正版。"%(rc,has_admit))]
        result["rounds"].append({"r":rnd,"apply":msg,"coqc_rc":rc,"err_head":err[:400]})
    return result

if __name__ == "__main__":
    # 离线自检：补丁协议解析（不调用 API、不花钱）
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
    ok,msg,new=apply_patch(tmp,"foo",blks)
    print("apply:",ok,msg); print(new)
    print("编造检查(应为空):",check_referenced_lemmas(blks,"Lemma foo : False."))
    os.remove(tmp)
