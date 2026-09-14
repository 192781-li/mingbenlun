# -*- coding: utf-8 -*-
"""
S04 agentic 璇佹槑闂幆 鈥斺€?DS 鏄富璇佹槑鑰咃紝鏈ā鍧楀彧鍋氭湰鍦版墽琛屼笌鍥炲杺锛圫04 鍙湁 coqc 鎵ц鏉冿級銆?
寰幆锛歜uild_messages -> DS(鎬濊€?缁欒冻token) -> 鎶絚oq -> 鏉ユ簮鏍囩鍒嗘祦/缂栭€犳牎楠?鍗敓妫€鏌?
      -> 澶囦唤 -> 鏁存鏇挎崲/鍘婚噸鎻掑叆 -> coqc -> 缁夸笖銆愮洰鏍囨+鏈疆鏂板紩鐞嗐€戞棤 admit/Abort 鍒欐敹鏁涳紱
      鍚﹀垯瀹屾暣閿欒鍘熸牱鍥炲杺杩涘叆涓嬩竴杞€?
v2(2026-09-04) 渚濄€婂閮ㄥ紩鐞嗕笌鐭ヨ瘑鏉ユ簮鐧昏瑙勮寖銆嬪崌绾э細
  - known_src 姣忚疆鍒锋柊锛堜慨鈥滀笂涓€杞瘉鍏ャ€佷笅涓€杞璇垽缂栭€犫€濓級
  - @stdlib 鏍囩璞佸厤骞朵氦 coqc 缁堣锛汙prove/@cite 蹇呴』褰撹疆甯﹀畬鏁?Qed锛涙棤鏍囩鏈畾涔夊悕鎷︽埅
  - 鎷︽埅 Abort 搴熷潡銆佸潡鍐?涓庢枃浠跺悓鍚嶉噸澶嶅畾涔夛紱INSERT 宸插瓨鍦ㄥ紩鐞嗚嚜鍔ㄥ幓閲?
  - 鏀舵暃鍒ゆ嵁瑕嗙洊鏈疆 INSERT 鐨勫叏閮ㄨ緟鍔╁紩鐞嗭紙涓嶈杈呭姪寮曠悊鐣?admit锛?
瀹夊叏锛氭瘡杞敼鏂囦欢鍓嶆暣鏂囦欢澶囦唤(.bak_rN)銆傝矾寰勮蛋 _paths.py銆?
"""
import os, re, shutil, subprocess, datetime
from ds_v4 import chat
from s04_context import build_messages, approx_tokens
from _paths import COQC, COQBIN, COQLIB, THEORIES, CHANNEL
from falsification_guard import adjudicate as falsify_adjudicate

def extract_coq_blocks(content):
    return [b.strip() for b in re.findall(r"```(?:coq|Coq)?\s*\n(.*?)```", content, flags=re.S)]

_TOP = r"(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Let)"

def lemma_span(src, name):
    """浠?Lemma/Theorem <name> 璧凤紝鍒扮涓€涓灏剧粨鏉熸爣璁?Qed./Admitted./Defined./Abort. 姝紙鍚級銆?
    缁撴潫鏍囪鍏佽鍒?鍗曠嫭鎴愯锛屼篃鍏佽璺熷湪 'Proof. ' 鍚岃锛堝 'Proof. Admitted.'锛夈€傛壘涓嶅埌 None銆?""
    m = re.search(r"(?m)^(?:Lemma|Theorem|Fact|Corollary)\s+"+re.escape(name)+r"\b", src)
    if not m: return None
    tail = re.search(r"(?m)(Qed\.|Admitted\.|Defined\.|Abort\.)\s*$", src[m.end():])
    if not tail: return None
    return m.start(), m.end()+tail.end()

def def_span(src, name):
    """鍗曡鍗犱綅 Definition/Fixpoint/Let 鐨勫垏闄ゅ尯闂达紙浠?^Definition name 闈炶椽濠埌绗竴涓灏惧彞鐐癸級銆?
    浠呯敤浜庡垏闄?S04 棰勭珛鐨勩€愬崟琛屽崰浣嶅疄鐜般€戯紝濂借 DS 浜ゆ潵鐨勫悓鍚嶆寮?Definition 涓嶄骇鐢熼噸澶嶅畾涔夛紱
    DS 鑷繁浜ょ殑澶氳鎴愬搧 Definition 璧版彃鍏ャ€佷笉缁忚繃杩欓噷鍒囬櫎銆傛壘涓嶅埌 None銆?""
    m = re.search(r"(?ms)^(?:Definition|Fixpoint|Let)\s+"+re.escape(name)+r"\b.*?\.\s*$", src)
    return (m.start(), m.end()) if m else None

def _top_defined_names(text):
    return set(re.findall(r"(?m)^\s*"+_TOP+r"\s+([\w']+)", text))

def apply_patch(file_path, target_lemma, blocks):
    """鎸夊崗璁簲鐢?DS 浠ｇ爜鍧楋紝杩斿洖 (ok, msg, new_src, inserted, mode)銆?
    mode: "replace"=鏈疆浜や簡鐩爣lemma骞舵浛鎹紱"insert_only"=鏈疆鍙氦杈呭姪寮曠悊锛屽厛鎻掑埌鐩爣鍓嶆矇娣€锛?none"=鏃犲彲搴旂敤銆?
    杈呭姪寮曠悊鍏佽鍒嗘浜わ紙insert_only 閫愯疆娌夋穩锛夛紱鑻?DS 閲嶅彂銆愬悓鍚嶃€戣緟鍔╁紩鐞嗭紝瑙嗕负淇鐗堬細鍒囬櫎鏂囦欢涓棫鍚屽悕娈点€?
    浠ユ柊鐗堟浛鎹紙杩欐牱宸叉矇娣€浣嗘湁缂栬瘧閿欑殑杈呭姪寮曠悊淇緱鍔紝涓嶄細琚?鍘婚噸"璺宠繃閿佹锛夛紱绾櫔澹板潡锛坢arkdown 娈嬬暀锛変涪寮冦€?""
    src = open(file_path, encoding="utf-8").read()
    work = src                       # 鍔ㄦ€佸伐浣滀覆锛氬悓鍚嶆棫娈靛湪姝ゅ垏闄?
    insert_before, new_lemma, skipped = [], None, []
    for b in blocks:
        body = re.sub(r"(?m)^\s*\(\*\s*INSERT-BEFORE:.*?\*\)\s*\n","",b).strip()
        if re.search(r"(?m)^(?:Lemma|Theorem)\s+"+re.escape(target_lemma)+r"\b", body):
            if new_lemma is not None:
                return False, "澶氫釜浠ｇ爜鍧楅兘瀹氫箟浜嗙洰鏍噇emma锛屾嫆缁濈洸鏀?, src, [], "none"
            new_lemma = body
        elif body:
            # 鍣０鍧楋紙markdown 鏍囬/绾鏄庯紝涓嶅惈浠讳綍 Coq 椤跺眰瀹氫箟锛夌洿鎺ヤ涪寮冿紝涓嶆彃鍏?.v
            if not re.search(r"(?m)^\s*(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Inductive|Let)\b", body):
                skipped.append(["<鍣０鍧?闈為《灞傚畾涔?涓㈠純>"]); continue
            insert_before.append(body)
    # 鍐欏叆鍓嶇粺涓€娓呭満锛氭湰杞换浣曞潡锛堝惈鐩爣鍧楀唴宓岀殑 Definition/Fixpoint锛夎寮曞叆鐨勯《灞傚悕锛?
    # 鎶?work 涓叾銆愭墍鏈夈€戞棫鍚屽悕娈靛惊鐜叏鍒囷紙lemma_span/def_span 閮借瘯锛夛紝鏉滅粷 DS 鍒嗗潡鏂瑰紡
    # 涓嶅悓鎴栧巻鍙叉畫鐣欏浠藉鑷寸殑 "already exists"锛?026-09-04 pick_prefix 涓夎疆绱Н閲嶅瀹氫箟鍥哄寲锛夈€?
    incoming = _top_defined_names("\n".join(insert_before + ([new_lemma] if new_lemma else [])))
    incoming.discard(target_lemma)   # 鐩爣 lemma 鐢变笅鏂?span 鏁存鏇挎崲锛屼笉鍦ㄦ鍒?
    def _cut_all(text, name):
        cnt = 0
        while True:
            sp = lemma_span(text, name) or def_span(text, name)
            if not sp: break
            text = text[:sp[0]] + text[sp[1]:]; cnt += 1
        return text, cnt
    for nm in sorted(incoming):
        work, c = _cut_all(work, nm)
        if c: skipped.append(["鍒囬櫎鏃у悓鍚?d浠?%s"%(c, nm)])
    span = lemma_span(work, target_lemma)
    if new_lemma is None:
        if not insert_before:
            return False, "DS 杈撳嚭涓病鏈夌洰鏍?lemma %s 鐨勫畬鏁存柊鐗堟湰锛屼篃娌℃湁浠讳綍鏂板紩鐞? % target_lemma, src, [], "none"
        if not span:
            return False, "婧愭枃浠朵腑瀹氫綅涓嶅埌 lemma %s 鐨勮捣姝? % target_lemma, src, [], "none"
        ins = "\n\n".join(insert_before)+"\n\n"
        msg = "浠呮彃鍏ヨ緟鍔╁紩鐞?d娈碉紙鏈疆鏈氦涓诲紩鐞嗭紝鍏堟矇娣€锛屼笅涓€杞氦涓诲紩鐞嗭級"%len(insert_before)
        if skipped: msg += "锛涘鐞?%s"%skipped
        return True, msg, work[:span[0]]+ins+work[span[0]:], insert_before, "insert_only"
    if not span:
        return False, "婧愭枃浠朵腑瀹氫綅涓嶅埌 lemma %s 鐨勮捣姝? % target_lemma, src, [], "none"
    s,e = span
    ins = ("\n\n".join(insert_before)+"\n\n") if insert_before else ""
    msg = "鏇挎崲鐩爣lemma骞舵彃鍏?d娈垫柊寮曠悊"%len(insert_before)
    if skipped: msg += "锛涘鐞?%s"%skipped
    return True, msg, work[:s]+ins+new_lemma+work[e:], insert_before, "replace"

def run_coqc(theories_dir, fname):
    cmd = ("set PATH=%s;%%PATH%% && set COQLIB=%s && cd /d %s && coqc.exe -Q . ALL %s 2>&1"
           % (COQBIN, COQLIB, theories_dir, fname))
    p = subprocess.run(["cmd","/c",cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "")+(p.stderr or "")

def append_channel(target, rnd, tag, text):
    try:
        CHANNEL.parent.mkdir(parents=True, exist_ok=True)
        ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(CHANNEL,"a",encoding="utf-8") as f:
            f.write("\n\n## %s [proof_loop] %s 路 round%d 路 %s\n\n%s\n"%(ts,target,rnd,tag,text))
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
    # as 妯″紡锛氭妸 as 鍚庢暣娈电粦瀹氭ā寮忥紙鍏佽 [[..]|[..]] 宓屽銆?|..&..)銆亅 , 绌烘牸锛夊悆鍒?. ; 鎹㈣锛屽啀鎻愭爣璇嗙
    for m in re.finditer(r"\bas\s+([\[\]\(\)\|\w'\s&,]+?)[.;\n]", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"\bas\s+([A-Za-z_][\w']*)", txt): local.add(m.group(1))  # as name锛堜笉甯︽嫭鍙凤級
    for m in re.finditer(r"forall\s+([^,]+),", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"fun\s+([^=]+)=>", txt): local |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    for m in re.finditer(r"(?:assert|set|remember|pose)\s*\(?\s*([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    for m in re.finditer(r"specialize\s+([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    # eqn:NAME / eqn : NAME / eqn:(NAME)锛歞estruct/inversion/case 鐢?eqn 缁戝畾鐨勭瓑寮忓亣璁惧悕锛堝 destruct .. eqn:EG锛?
    for m in re.finditer(r"\beqn\s*:\s*\(?([A-Za-z_][\w']*)", txt): local.add(m.group(1))
    return local

def parse_stdlib_names(content, blocks):
    """鎻愬彇 (* @stdlib names: a, b, c *) 涓樉寮忓０鏄庛€佷氦 coqc 缁堣鐨勫簱寮曠悊鍚嶃€?""
    names=set()
    for m in re.finditer(r"@stdlib[^\n*]*?names\s*:\s*([^*)]+)", content+"\n"+"\n".join(blocks)):
        names |= set(re.findall(r"[A-Za-z_][\w']*", m.group(1)))
    return names

def check_hygiene(blocks):
    """鍗敓妫€鏌ワ細涓嶈 Abort 搴熷潡锛涘潡鍐呬笉璁稿悓鍚嶉噸澶嶅畾涔夈€傝繑鍥為棶棰樺垪琛ㄣ€?""
    issues=[]
    for i,b in enumerate(blocks):
        if re.search(r"\bAbort\.", b):
            issues.append("浠ｇ爜鍧?d 鍚?Abort. 搴熷潡锛堣崏绋夸笉璁稿叆搴擄紝璇峰彧浜?Qed 鎴愬搧锛?%(i+1))
    seen={}
    for b in blocks:
        for n in _top_defined_names(b):
            seen[n]=seen.get(n,0)+1
    dup=sorted(n for n,c in seen.items() if c>1)
    if dup: issues.append("鍚屽悕瀹氫箟鍦ㄦ湰杞噸澶嶅嚭鐜? %s锛堟瘡涓紩鐞嗗彧缁欎竴浠斤級"%dup)
    return issues

def check_referenced_lemmas(blocks, known_src, extra_known=None):
    """鎶?apply/rewrite/exact 寮曠敤銆佷絾鏉愭枡/鏈潡/灞€閮?鐧藉悕鍗?鏄惧紡澹版槑閮芥病鏈夌殑鍚嶅瓧锛堥槻缂栭€狅級銆?""
    known=set(re.findall(r"(?:Lemma|Theorem|Fact|Corollary|Definition|Fixpoint|Inductive|CoInductive|Let|Notation)\s+([\w']+)", known_src))
    for im in re.finditer(r"Inductive\s+[A-Za-z_][\w']*[^.]*?:=(.*?)\.", known_src, flags=re.S):
        known |= set(re.findall(r"[A-Za-z_][\w']*", im.group(1)))
    known |= set(re.findall(r"[A-Za-z_][\w']*", known_src))   # 鍏ㄦ枃瀹屾暣璇嶅厹搴?
    known |= _defined_names(blocks); known |= _local_names(blocks); known |= _BUILTIN
    if extra_known: known |= extra_known
    missing={}
    pat=re.compile(r"(?:e?apply|erewrite|rewrite|e?exact)\s+(?:@\s*)?([A-Za-z_][\w']*)")
    for b in blocks:
        for m in pat.finditer(b):
            ident=m.group(1)
            if ident in known: continue
            if ident.startswith("IH"): continue   # induction 鑷姩鐢熸垚鐨勫綊绾冲亣璁?IHtyped/IHtyped1..
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
        known_src = _read_known(theories_dir, layer_files)   # v2: 姣忚疆鍒锋柊锛屾敹褰曚笂涓€杞柊璇佸叆鐨勫紩鐞?
        msgs = build_messages(task_brief, layer_files=layer_files, strategy_docs=strategy_docs,
                              philos_docs=philos_docs, coqc_error=coqc_error, history=history,
                              extra_notes=extra_notes)
        log("[round %d] 涓婁笅鏂囩害 %d token锛岃皟鐢?%s ..."%(rnd, approx_tokens(msgs), model))
        out = chat(msgs, model=model, thinking="enabled", max_tokens=64000,
                   task_name="proofloop_%s_r%d"%(target_lemma,rnd))
        log("[round %d] status=%s finish=%s rounds=%d 杈撳嚭%d瀛楃 reasoning%d瀛楃 璐圭敤%.4f鍏?
            %(rnd,out["status"],out["finish"],out["rounds"],len(out["content"]),len(out["reasoning"]),out["cost_yuan"]))
        append_channel(target_lemma,rnd,"DS杈撳嚭",out["content"][:2000]+"\n[reasoning鎽樿]\n"+out["reasoning"][:1500])
        needs = detect_need(out["content"])
        if needs:
            log("[round %d] DS 澹版槑缂烘潗鏂欙細%s锛屽洖鍠傚紩瀵?%(rnd,needs))
            history += [("assistant",out["content"][:6000]),
                        ("user","鏉愭枡A宸插寘鍚?%s 瀹屾暣鍏ㄦ枃锛岃鍦ㄥ叾涓绱紱鑻ョ‘灞炲閮ㄧ己澶憋紝鎸夋潵婧愯鑼冩墦 @stdlib/@cite 鏍囩锛屼笉瑕佺敤鏃犲悕鏈畾涔夊悕銆?%("銆?.join(layer_files)))]
            result["rounds"].append({"r":rnd,"need":needs}); continue
        blocks = extract_coq_blocks(out["content"])
        # 璇佷吉瀹堝崼锛堟渶楂樹紭鍏堬紝鍏堜簬涓€鍒囧簲鐢級锛欴S 鑻ュ甯冪洰鏍囧懡棰樹负鍋?浜?~forall 鍙嶄緥锛屽繀椤昏繃鍙岄棬锛?
        # 绂佹鍑嚜鐒惰瑷€鎴栦竴浠芥病缂栬瘧杩囩殑鍙嶄緥灏辩洸淇?鍛介涓哄亣"锛?026-09-04 split_assoc 浜嬫晠鍥哄寲锛夈€?
        verdict = falsify_adjudicate(out["content"], blocks, target_lemma,
                                     layer_files=layer_files, log=log)
        if verdict["verdict"] == "refuted_claim":
            log("[round %d] 璇佷吉瀹堝崼鎺ㄧ炕 DS 鐨勪负鍋囦富寮狅紙gate1_rc=%s winner=%s锛夛紝涓嶆敼鏂囦欢锛屽洖鍠傜户缁瘉鐪?
                % (rnd, verdict.get("gate1_rc"), verdict.get("gate2_winner")))
            history += [("assistant", out["content"][:6000]),
                        ("user", "[璇佷吉瀹堝崼路鏈烘楠岃瘉] " + verdict["feedback"])]
            result["rounds"].append({"r": rnd, "guard": "refuted_claim",
                                     "gate1_rc": verdict.get("gate1_rc"),
                                     "gate2_winner": verdict.get("gate2_winner")})
            continue
        if verdict["verdict"] == "plausibly_false":
            log("[round %d] 璇佷吉瀹堝崼锛氬弽渚嬬嫭绔嬬紪璇戦€氳繃涓斿€欓€夎В鍧囪瘉涓嶅嚭锛岀枒浼间负鍋囷紝halt 鍐荤粨鐑ч挶锛屼氦浜哄伐/S01/S00瑁佸喅锛堟案涓嶈嚜鍔ㄦ敼鍒わ級" % rnd)
            result.update(converged=False, halted_falsification=verdict)
            break
        hyg = check_hygiene(blocks)
        if hyg:
            log("[round %d] 鍗敓妫€鏌ヤ笉杩?%s锛屼笉鏀规枃浠讹紝鍥炲杺"%(rnd,hyg))
            history += [("assistant",out["content"][:6000]),
                        ("user","杈撳嚭鍗敓闂锛?s銆傝鍘绘帀 Abort 鑽夌銆佹瘡涓紩鐞嗗彧淇濈暀涓€浠芥垚鍝侊紙Lemma..Qed.锛夛紝涓诲畾鐞嗙敤鍒扮殑杈呭姪寮曠悊褰撹疆鍏ㄩ儴浠?INSERT-BEFORE 鎴愬搧鍧椾氦榻愶紝閲嶇粰瀹屾暣鐗堟湰銆?%hyg)]
            result["rounds"].append({"r":rnd,"hygiene":hyg}); continue
        stdlib = parse_stdlib_names(out["content"], blocks)
        if stdlib: log("[round %d] @stdlib澹版槑(浜oqc缁堣,璁板緱鐧昏鍙拌处): %s"%(rnd,sorted(stdlib)))
        missing = check_referenced_lemmas(blocks, known_src, extra_known=stdlib)
        if missing:
            log("[round %d] 鏈畾涔夊悕 %s锛堟棤@prove瀹屾暣璇佹槑/@stdlib澹版槑锛夛紝涓嶆敼鏂囦欢锛屽洖鍠?%(rnd,missing))
            history += [("assistant",out["content"][:6000]),
                        ("user","浣犲紩鐢ㄤ簡 %s锛屼絾鏉愭枡A銆佹湰杞唬鐮佸潡瀹氫箟涓兘涓嶅瓨鍦ㄣ€傛寜鏉ユ簮瑙勮寖澶勭疆锛氣憼鑷瘉杈呭姪寮曠悊锛氬綋杞敤 INSERT-BEFORE 鍧楄繛瀹屾暣 Qed 璇佹槑涓€璧风粰锛涒憽纭睘Coq搴撳凡璇佸紩鐞嗭細鎵?(* @stdlib names: .. *) 骞剁‘淇濆凡 Require Import锛涒憿鏂囩尞缁撹锛氭墦 @cite 浣嗕粛椤绘湰搴撻噸璇併€傜姝㈠彧鐣欏悕瀛椼€傞噸缁欏畬鏁寸増鏈€?%missing)]
            result["rounds"].append({"r":rnd,"missing":missing}); continue
        bak = file_path + (".bak_r%d"%rnd)
        shutil.copy2(file_path, bak)
        ok,msg,new_src,inserted,mode = apply_patch(file_path,target_lemma,blocks)
        if not ok:
            log("[round %d] 鏈敼鏂囦欢锛?s锛屽洖鍠?%(rnd,msg))
            history += [("assistant",out["content"][:6000]),
                        ("user","杈撳嚭鏃犳硶搴旂敤锛?s銆傝涓ユ牸鎸夊崗璁粰鐩爣 Lemma %s 浠?Lemma 琛屽埌 Qed. 鐨勫畬鏁存柊鐗堟湰锛屾柊寮曠悊鐢?INSERT-BEFORE 鏍囪銆?%(msg,target_lemma))]
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
            # 鍒嗘浜わ細鏈疆鍙矇娣€杈呭姪寮曠悊銆傜紪璇戣繃涓旇緟鍔╂棤 admit 灏辩畻娌夋穩鎴愬姛锛屼笉鏀舵暃锛屼笅杞氦涓诲紩鐞嗐€?
            log("[round %d] 杈呭姪娌夋穩 coqc exit=%d 鏂板紩鐞哸dmit/abort=%s"%(rnd,rc,ins_bad))
            result["rounds"].append({"r":rnd,"mode":"insert_only","apply":msg,"coqc_rc":rc,"err_head":err[:400]})
            if rc==0 and not ins_bad:
                names=[n for b in inserted for n in _top_defined_names(b)]
                history += [("assistant",out["content"][:6000]),
                            ("user","杈呭姪寮曠悊 %s 宸叉敹褰曡繘鏂囦欢涓?coqc 缂栬瘧閫氳繃锛屾棤闇€閲嶈瘉锛屼笅涓€杞彲鐩存帴寮曠敤銆傜幇鍦ㄣ€愬彧銆戦渶缁欏嚭鐩爣 Lemma %s 浠?Lemma 琛屽埌 Qed. 鐨勫畬鏁磋瘉鏄庡潡锛堜笉瑕佸啀鍙氦杈呭姪寮曠悊锛屼篃涓嶈閲嶅宸叉敹褰曠殑锛夛紝骞朵繚璇佸畠寮曠敤鐨勫悕瀛楅兘宸插湪鏉愭枡A鎴栧凡鏀跺綍寮曠悊涓€?%(names,target_lemma))]
            else:
                coqc_error = err if err.strip() else ("exit=%d锛涙柊寮曠悊闂=%s"%(rc,ins_bad))
                history += [("assistant",out["content"][:6000]),
                            ("user","鍒氭彃鍏ョ殑杈呭姪寮曠悊缂栬瘧鏈繃锛坮c=%s锛屾柊寮曠悊admit/abort=%s锛夈€傞敊璇鏉愭枡鏈熬锛岃淇杩欎簺杈呭姪寮曠悊鍚庨噸浜わ紝鐒跺悗鍐嶇粰涓诲紩鐞?%s銆?%(rc,ins_bad,target_lemma))]
            continue
        log("[round %d] coqc exit=%d 鐩爣娈礱dmit=%s 鏂板紩鐞哸dmit/abort=%s"%(rnd,rc,tgt_bad,ins_bad))
        if rc==0 and not tgt_bad and not ins_bad:
            log("[round %d] 鉁?缂栬瘧閫氳繃涓旂洰鏍?鏂板紩鐞嗗潎鏃燼dmit锛屾敹鏁?%rnd)
            result.update(converged=True,final_round=rnd,backup=bak); break
        coqc_error = err if err.strip() else ("exit=%d 浣嗘棤閿欒鏂囨湰锛涚洰鏍囨admit=%s 鏂板紩鐞嗛棶棰?%s"%(rc,tgt_bad,ins_bad))
        history += [("assistant",out["content"][:6000]),
                    ("user","搴旂敤鍚庢湭鏀舵暃锛坮c=%s锛岀洰鏍囨admit=%s锛屾柊寮曠悊admit/abort=%s锛夈€傚畬鏁撮敊璇鏉愭枡鏈熬锛屽畾浣嶆牴鍥犲苟缁欏畬鏁翠慨姝ｇ増锛涗富瀹氱悊鐢ㄥ埌鐨勫叏閮ㄨ緟鍔╁紩鐞嗗綋杞氦榻愬埌 Qed锛屼笉璁?Abort/Admitted銆?%(rc,tgt_bad,ins_bad))]
        result["rounds"].append({"r":rnd,"apply":msg,"coqc_rc":rc,"err_head":err[:400]})
    return result

if __name__ == "__main__":
    import tempfile
    sample='''璇存槑銆?
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
    print("缂栭€犳鏌?搴斾负绌?:",check_referenced_lemmas(blks,"Lemma foo : False."))
    print("鍗敓(搴旂┖):",check_hygiene(blks))
    # insert_only锛氭湰杞彧浜よ緟鍔╁紩鐞嗭紝搴旀彃鍒?foo 鍓嶄笖 mode=insert_only
    with tempfile.NamedTemporaryFile("w",suffix=".v",delete=False,encoding="utf-8") as f:
        f.write("Lemma foo : False.\nProof. admit.\nAdmitted.\n"); tmp2=f.name
    ok2,msg2,new2,ins2,mode2=apply_patch(tmp2,"foo",blks[:1])
    print("apply(insert_only):",ok2,mode2,msg2,"| helper鍦╢oo鍓?", new2.index("helper")<new2.index("Lemma foo"), "| foo浠岮dmitted:", "Admitted." in new2)
    # 鍚屽悕鏇挎崲锛氭枃浠堕噷宸叉湁閿欒鐗?helper(Admitted)锛屾湰杞粰 Qed 鏂扮増锛屽簲鍒囬櫎鏃х増銆佸彧鐣欎竴浠芥柊鐗?
    with tempfile.NamedTemporaryFile("w",suffix=".v",delete=False,encoding="utf-8") as f:
        f.write("Lemma helper : True. Proof. Admitted.\n\nLemma foo : False.\nProof. admit.\nAdmitted.\n"); tmp3=f.name
    ok3,msg3,new3,ins3,mode3=apply_patch(tmp3,"foo",blks)
    print("apply(鍚屽悕鏇挎崲):",ok3,mode3,msg3,"| helper鍙嚭鐜颁竴娆?", new3.count("Lemma helper")==1,
          "| 鏃dmitted鐗堝凡鍒囬櫎:", "Proof. Admitted." not in new3)
    abort=blks+["Lemma x:True. Proof. Abort."]
    print("鍗敓(搴旀姄鍒癆bort):",check_hygiene(abort))
    import os as _os; _os.remove(tmp); _os.remove(tmp2); _os.remove(tmp3)
