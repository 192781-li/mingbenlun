# -*- coding: utf-8 -*-
import os, sys
d = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,d)
from proof_loop import check_referenced_lemmas, extract_coq_blocks
from _paths import THEORIES

known = ""
for lf in ("Layer1.v","Layer2.v"):
    known += (THEORIES/lf).read_text(encoding="utf-8")

# 1) 合法引用：typed 构造子 / Bool 模块 / 局部 pose 名，应全部放行
ok_block = ["""
Lemma subst_ren_general : forall D Q, typed D Q -> True.
Proof.
  intros D Q HTD. pose (Rk := eq_refl 0).
  eapply ty_in. apply ty_out. rewrite Bool.andb_true_iff in Hget.
  exact (ty_par Hget). apply ty_var. apply ty_zero. apply ty_tau.
Qed.
"""]
m1 = check_referenced_lemmas(ok_block, known)
print("合法块 missing(应为空):", m1)

# 2) 纯凭空引理（全文无、块内未定义），应被拦
fake_block = ["""
Lemma subst_ren_general : True. Proof. apply totally_fake_lemma_xyz. Qed.
"""]
m2 = check_referenced_lemmas(fake_block, known)
print("凭空名 missing(应含 totally_fake_lemma_xyz):", m2)

# 3) INSERT-BEFORE 自定义并完整证明的 helper，应放行
self_block = ["""
(* INSERT-BEFORE: subst_ren_general *)
Lemma my_helper : True. Proof. exact I. Qed.
""", """
Lemma subst_ren_general : True. Proof. apply my_helper. Qed.
"""]
m3 = check_referenced_lemmas(self_block, known)
print("块内自定义 helper missing(应为空):", m3)
assert m1 == [], "假阳性未消除!"
assert "totally_fake_lemma_xyz" in m2, "编造拦截失效!"
assert m3 == [], "自定义helper被误拦!"
print("ALL GUARD TESTS PASS")
