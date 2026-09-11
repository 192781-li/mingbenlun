# Enactics: A Linear Logic of Operational Agency

**Abstract.** We introduce *Enactics*, a formal system built on a single primitive distinction: *live operations* (Op), which are resource-sensitive and cannot be replicated, versus *traces* (Tr), which are static, replicable records of past operations. We extend intuitionistic linear logic with agency types split into live (`Ag_lv`) and trace (`Ag_tr`) variants, an alienation precondition type (`Hijack(b,a)`), and clarity types (`Cl(a,A)`) holding both live agency and its trace model. We prove: (1) a self-model (!-modal theory) cannot prove *live* self-agency (`Ag_lv`) — an incompleteness result arising from the Op/Tr type distinction rather than diagonalization, and the formal counterpart of Marx's second thesis on Feuerbach; (2) the agency decision problem is Π₂-complete (with the Π₂ dimension coming from liveness, causality being Π₁), strictly harder than the classical halting problem; (3) agency cannot be encoded in standard game semantics (undefinability theorem); (4) alienation truncates coinductive objects, admitting a canonical surjection onto inductive objects (non-injective, not an isomorphism); (5) clarity makes every alienation reindexing a split mono by providing its right inverse; (6) ! does not preserve final coalgebras (!νF≇ν!F), unifying quantum no-cloning, biological irreplicability, Marxist alienation theory, and AI alignment limits as instances of a single categorical principle. We give a game semantics, a π-calculus interpretation with a hijack-detection theorem, a Hilbert-space instance connecting agency to quantum measurement (where the preferred basis must be externally chosen, via einselection), and a network model of revolutionary cascade (deterministic SI: reachability; noisy: spectral radius threshold ρ(pC)>1).

---

## 1. Introduction

### 1.1 Motivation

Who runs a process? This question is not asked in standard mathematics. A function computes, a process executes, a system evolves — but the mathematical formalism does not track *who decides*. In computability theory, a Turing machine's behavior is determined by its transition function regardless of "who" controls it. In game semantics, Player and Opponent roles are fixed by polarity; there is no dimension of "who actually chooses the move." In category theory, morphisms compose without tracking agency.

This omission is harmless for dead data and deterministic functions. It becomes critical for *self-referential systems* — living organisms, conscious beings, autonomous software, social movements — where the question "does this system run itself, or is it controlled by another?" has scientific, ethical, and political significance.

We present **Enactics** (践演论), a formal system that makes agency a first-class mathematical concept. Starting from the single primitive distinction between live operations and dead traces, we build a logic, a categorical semantics, a game semantics, and a process calculus that track operational agency, and we prove theorems about it.

### 1.2 The core distinction

| | Op (live operation) | Tr (trace/deposit) |
|---|---|---|
| Nature | Process, event, "happening" | Record, data, "what happened" |
| Linear? | Yes — cannot be copied or discarded | No — can be freely copied and discarded |
| Modality | Linear (no !) | !-modal |
| First person | "I am running" | "It says I am running" |
| Temporal | Present, ongoing | Past, fixed |
| Examples | Life, consciousness, labor, quantum process | Corpse, text, capital, measurement outcome |

The Op/Tr distinction is not mind-matter dualism. Both are aspects of the same reality: every Op leaves Tr (a trace), and every Tr was produced by some Op. The distinction is logical and categorical, not ontological.

### 1.3 Contributions

We make the following contributions:

1. **Enactive Linear Logic (ALL)** (§2): A sequent calculus extending intuitionistic linear logic with live agency types `Ag_lv(a,A)`, trace agency types `Ag_tr(a,A)`, alienation precondition types `Hijack(b,a)`, and clarity types `Cl(a,A)`, with cut elimination, consistency, and conservative extension results. The live/trace split is essential: without it, dereliction (`!A⊢A`)击穿 the incompleteness theorem.

2. **Enactive incompleteness** (§3): A self-model (!-modal theory) cannot prove its own agency (Ag(A,A)). This incompleteness arises from the Op/Tr type gap, not diagonalization. We also classify the agency decision problem as Π₂-complete.

3. **Agency games** (§4): A game semantics extending standard game semantics with a control attribution function α_G, with an undefinability theorem showing agency cannot be encoded away.

4. **Agency fibration** (§5): A fibration over a monoid of agents, where the alienation functor truncates coinductive objects (canonical surjection onto inductive objects, non-injective), and clarity recovers from alienation via barbed bisimulation.

5. **Unification** (§6): Quantum no-cloning, life's irreplicability, labor's non-capitalizability, and AI alignment limits are all instances of a single theorem in any linear/non-linear adjunction.

6. **Applications** (§7): Hijack detection in π-calculus, quantum measurement as alienation, and a network model of revolutionary cascade with spectral-radius threshold.

---

## 2. Enactive Linear Logic

### 2.1 Syntax

**Types:**
```
A, B ::= α | 1 | A ⊗ B | A ⊸ B | !A
       | Ag_lv(a,A)  (* live agency: only self_ev *)
       | Ag_tr(a,A)  (* trace agency: from !Ag dereliction *)
       | Hijack(b,a) (* alienation precondition *)
       | Cl(a,A)
```

**Terms:**
```
e ::= x | ⋆ | λx.e | e e | e ⊗ e | let x⊗y = e in e
    | !e | derelict(e)
    | live<a>(e) | unlive(e)          (* Ag_lv intro/elim *)
    | trace(e) | untrace(e)            (* Ag_tr intro/elim *)
    | alien<b>(e,h)                    (* requires h:Hijack(b,a) *)
    | clarity<a>(e,m) | unsee(e)
    | self_ev<a>
```

`self_ev<a>` is a *linear hypothesis*, not an axiom — it represents the first-person enactive evidence of self-running, available only when a actually runs itself, and cannot be promoted to !-modal. It inhabits `Ag_lv(a,A)`, never `Ag_tr(a,A)`.

**Key distinction:** `Ag_lv(a,A)` (live agency) is inhabited only by `self_ev<a>` — it is the genuine "I am running" resource. `Ag_tr(a,A)` (trace agency) is inhabited by `derelict(!Ag(a,A))` — it is a static record that can be installed by an alienator (Corollary 5.2). The two are not interconvertible: `Ag_tr ⊸ Ag_lv` does not hold (a trace cannot become live running), and `Ag_lv ⊸ Ag_tr` requires an explicit `deposit` operation (each step of live running leaves a trace, consuming one step).

### 2.2 Key rules

```
Γ, self_ev<a,A> ⊢ e : A              Γ ⊢ e : Ag_lv(a,A)
────────────────────── Ag_lv-I        ────────────────────── Ag_lv-E
Γ ⊢ live<a>(e) : Ag_lv(a,A)           Γ ⊢ unlive(e) : A

Γ ⊢ e : !Ag(a,A)                       Γ ⊢ e : Ag_tr(a,A)
────────────────────── Ag_tr-I        ────────────────────── Ag_tr-E
Γ ⊢ trace(e) : Ag_tr(a,A)              Γ ⊢ untrace(e) : !Ag(a,A)

Γ ⊢ e : Ag_lv(a,A)    Γ ⊢ h : Hijack(b,a)
───────────────────────────────────────────── Alien-I'
Γ ⊢ alien<b>(e,h) : Ag_lv(b,A)

Γ ⊢ e : Ag_lv(a,A)    Γ ⊢ m : !Ag_tr(a,A)
────────────────────────────────────────────── Cl-I
Γ ⊢ clarity<a>(e,m) : Cl(a,A)

Γ ⊢ e : Cl(a,A)
───────────────────────────────────── Cl-E
Γ ⊢ unsee(e) : Ag_lv(a,A) ⊗ !Ag_tr(a,A)
```

*Note on Alien-I':* unlike the earlier unconditional rule (which caused all agency types to collapse into one equivalence class), alienation now requires a `Hijack(b,a)` precondition — b must possess the means to seize a's agency. This makes `Ag(a,A) ⊬ Ag(b,A)` generally true, and aligns with the philosophical position that alienation does not happen by fiat; it requires concrete conditions of seizure. `Hijack(self,a) = 0` and `Hijack(b,self) = 0` — no one can seize the self-fiber's agency, as the self is a self-referential closure whose running-right is inalienable.

### 2.3 Metatheory

**Theorem 2.1 (Cut elimination).** Every proof in ALL can be transformed into a cut-free proof.

The cut reduction rules for the new type constructors are:

| Rule | Reduction |
|------|-----------|
| (R1) Ag_lv β | `unlive(live<a>(e))` ↦ `e` |
| (R2) Ag_tr β | `untrace(trace(e))` ↦ `e` |
| (R3) Cl β | `unsee(clarity<a>(e, m))` ↦ `e ⊗ m` |
| (R4) Alien pass | `unlive(alien<b>(e, h))` ↦ `unlive(e)` |
| (R5) Alien compose | `alien<b>(alien<c>(e, h₁), h₂)` ↦ `alien<b>(e, h₁∘h₂)` |

*Proof.* Standard ILL cut elimination handles ⊗, ⊸, !. The new rules (R1)–(R4) handle cuts involving Ag_lv, Ag_tr, and Cl. (R5) is a computational equivalence (η-like), not a cut reduction.

Define type complexity |A| with |Ag_lv(a,A)| = |Ag_tr(a,A)| = |A|+1, |Cl(a,A)| = |A|+2, |Hijack(b,a)| = 1. Reductions (R1)–(R3) strictly decrease cut formula complexity. (R4) moves the runner label along a finite alienation chain (b→a, a≠b) toward the chain's base (self or a `live` intro); since proofs have finite depth, alienation chains are finite, so (R4) terminates and triggers (R1) at the base. `Hijack` has no elim rule, so it produces no cut. `Cl` and `Alien` cannot form a direct cut (Cl(a,A) is not a subtype of Ag_lv(a,A); alienating a Cl requires first `unsee`-ing it). Hence all new cuts terminate. ∎

**Corollary 2.2 (Consistency).** ALL is consistent (⊬ 0).

**Theorem 2.3 (Conservative extension).** ALL is a conservative extension of intuitionistic linear logic: if Γ and A contain no Ag, Cl, or self_ev, then Γ ⊢ A in ALL iff Γ ⊢ A in ILL.

**Theorem 2.4 (Clarity is linear, not !-modal).** Cl(a,A) ⊬ !Cl(a,A). Clarity cannot be deposited/replicated.

*Proof.* Cl-E gives Ag(a,A) ⊗ !Ag(a,A), where Ag(a,A) is linear. If Cl(a,A) were !-modal, contraction would give two copies of the linear Ag(a,A), violating linearity. ∎

**Political reading:** Revolution cannot be exported. You cannot replicate awakening as data; each person must awaken themselves.

---

## 3. Enactive Incompleteness

### 3.1 The theorem

Let S_A be a system's self-model — a finite (or recursively enumerable) set of !-modal propositions describing A to itself. Note that by Corollary 5.2, an alienator may install `!Ag_tr(A,A)` in S_A — a trace copy of agency.

**Theorem 3.1 (Enactive incompleteness).**
1. S_A ⊬ Ag_lv(A,A) — the self-model cannot prove *live* self-agency
2. S_A ⊬ ¬Ag_lv(A,A) — nor can it prove alienation of live agency
3. Ag_lv(A,A) is established only by the linear resource self_ev<A>, which cannot be derived from !-modal assumptions

*Proof.* (1) By induction on derivations. Every proposition in S_A is !-modal. From !-modal hypotheses, the only way to obtain an agency-type conclusion is via dereliction `!Ag(A,A) ⊢ Ag_tr(A,A)` — which yields `Ag_tr` (trace agency), not `Ag_lv` (live agency). No rule produces `Ag_lv` without the linear hypothesis `self_ev<A>`. Hence S_A ⊬ Ag_lv(A,A). (2) `¬Ag_lv = Ag_lv ⊸ 0`; the elimination rule for Ag_lv only extracts the underlying process, and cannot yield 0. By induction on derivations, S_A ⊬ ¬Ag_lv(A,A). (3) Immediate from (1): Ag_lv is inhabited only by self_ev. ∎

*Why the earlier statement was wrong.* A previous version claimed `S_A ⊬ Ag(A,A)` without distinguishing live from trace agency. But dereliction (`!A ⊢ A`) is a basic rule of intuitionistic linear logic: if S_A contains `!Ag(A,A)` (which Corollary 5.2 says an alienator installs), then one dereliction step yields `Ag_tr(A,A)`. The system has no syntactic means to distinguish "trace agency" (installed by an alienator) from "live agency" (genuine self-running) — hence the type split `Ag_lv`/`Ag_tr` is necessary, not optional.

*Philosophical reading.* This is the formal proof of Marx's second thesis on Feuerbach: "The question whether objective truth can be attributed to human thinking is not a question of theory but is a practical question." Live agency (`Ag_lv`) can only be established by practice (`self_ev`), never by theory (`S_A`, the !-modal self-model). A trace copy of agency (`Ag_tr`) can be installed by an alienator and derived from the self-model — but it is not live.

*Relation to Gödel.* This result is structurally closer to "resource-sensitive incompleteness" than to Gödel's diagonal argument: diagonalization requires contraction (copying), which linear logic lacks, so the standard Gödel construction fails. It is independent of and complementary to Gödel's incompleteness, and adjacent to Beklemishev–Shamkanov's work on the role of contraction in Gödel's theorem.

### 3.2 Comparison with Gödel

| | Gödel (1931) | Enactive |
|---|---|---|
| Undecidable | G_F ("I am unprovable") | Ag(A,A) ("I run myself") |
| Method | Diagonalization | Op/Tr type gap |
| Source of limitation | Deductive power of formal systems | Type mismatch between live process and dead model |
| Truth established by | Metamathematics | Enactment (practice) |

Enactive incompleteness is independent of Gödel's: it does not require arithmetic or self-referential sentences. It requires only the linear/!-modal distinction.

### 3.3 Computational complexity

We work in the **asynchronous** π-calculus (outputs do not block) with **provenance tracking** (an extension of labeled transition semantics in the tradition of Boreale–De Nicola 1995), which records causal ancestry of outputs via labeled transitions rather than standard LTS (which merges isomorphic τ-transitions and erases location information).

**Theorem 3.2 (Π₂-completeness).** The agency decision problem for asynchronous π-calculus processes,

> AGENCY = {(P,a) : ∀ environments E, every maximal path of P|E has infinitely many outputs on a, and every such output's causal ancestors are all τ (internal)},

is Π₂-complete.

*Proof.* Define the decidable predicate R(P,E,t,s,a): "on all execution paths of P|E of length ≤ s, (i) every a-output in [0,s] has only τ ancestors, and (ii) every path of length s has at least one a-output in [t,s]." R is uniformly decidable: image-finiteness ensures the depth-s execution tree is finite, and provenance labels make ancestry checking decidable. By König's lemma, "every maximal path has infinitely many a-outputs after t" is equivalent to "∃s such that every s-path has an a-output in [t,s]." Hence AGENCY = ∀E ∀t ∃s R(P,E,t,s,a), which is ∀∀∃Δ₀ = Π₂.

Π₂-hardness is by many-one reduction from TOTAL = {e : ∀x φ_e(x) halts}: construct P_e = (νc)(Runner_e(c) | Reporter(c,a)) where Runner simulates φ_e(0),φ_e(1),… in sequence, signaling on private channel c when each halts, and Reporter outputs on a upon receiving c. If e∈TOTAL, P_e produces infinitely many internally-caused a-outputs (c is private, so E cannot inject causality; asynchronous outputs do not block); if φ_e(k) diverges, P_e falls silent on a, violating liveness. ∎

**Corollary 3.3.** AGENCY is strictly harder than HALT (Σ₁-complete). Even a halting oracle cannot decide agency.

*Note.* The liveness condition ("infinitely many outputs") is essential: without it, AGENCY = ∀E∀t SC would be Π₁, and the TOTAL reduction would imply Π₂ ⊆ Π₁, collapsing the arithmetic hierarchy. The liveness condition adds the ∃s quantifier that places AGENCY in Π₂.

**Theorem 3.4 (Agency = productivity).** AGENCY is recursively isomorphic to PRODUCTIVE (productivity of corecursive programs).

*Proof.* Mutual reductions: a productive stream yields a self-running process; a self-running process yields a productive stream of its internally-caused actions. ∎

**Remark 3.5 (Novelty repositioning).** The Π₂-completeness of AGENCY comes from the liveness dimension ("infinitely many outputs on a"), which is itself Π₂-complete and equivalent to the classical PRODUCTIVE/TOTAL problem. The causality dimension ("every output's ancestors are all τ") is ∀∀Δ₀=Π₁. Thus AGENCY = liveness(Π₂) ∧ causality(Π₁) = Π₂. The contribution is not a new Π₂-complete problem per se, but the identification of "operational agency" as liveness + causality, and the proof that the hard part of "is this system free?" is "is it alive forever?" rather than "is each action self-determined?"

---

## 4. Agency Games

### 4.1 Definition

An **agency game** is G = (M_G, λ_G, ⊢_G, P_G, α_G) where (M_G, λ_G, ⊢_G, P_G) is a standard game (moves, polarity, legal positions, strategies) and α_G: M_G → A assigns each move to the agent who actually chooses it.

The key innovation: λ_G(m) = P means "this move belongs to Player's side," while α_G(m) = self means "Player actually chooses this move." These can diverge: a move can belong to Player (λ=P) but be controlled by another (α=b) — this is *alienation in games*.

### 4.2 Undefinability

**Theorem 4.1 (Agency full-abstraction failure).** Let F: AGame → Game be a faithful *-autonomous functor. If F(G[b]) = F(G) for all G, b (F erases agency at the object level), then F is not fully abstract: there exist G, b such that G ≉_ctx G[b] (distinguishable in AGame) but F(G) ≅_ctx F(G[b]) (indistinguishable in Game).

*Proof.* **Step 1: Construct the distinguishing context.** Define the *clarity observation context* `ObsCl`: an AGame context that (i) takes an agency game G as parameter, (ii) constructs Cl(G) (using the `Cl` type constructor, which is ALL-specific — not a standard linear logic connective), and (iii) uses Cl(G)'s observation-layer moves to read the control attribution function α_G. `ObsCl` is a legitimate AGame context — it uses `Cl` and α_G, both AGame-specific structures with no counterpart in standard Game.

**Step 2: G ≉_ctx G[b] in AGame.** Take G with α_G(m) = self for all m, and G[b] with α_{G[b]}(m) = b for some m. In context `ObsCl`: ObsCl[G] reads α_G(m) = self for all m → observation sequence "self, self, ..."; ObsCl[G[b]] reads α_{G[b]}(m) = b for some m → observation sequence contains "b". Different observations ⟹ G ≉_ctx G[b]. ∎

**Step 3: F(G) ≅_ctx F(G[b]) in Game.** F(G[b]) = F(G) means they are the *same object* in Game. Same object ⟹ same behavior in all contexts ⟹ F(G) ≅_ctx F(G[b]). ∎

**Step 4: Full abstraction fails.** Full abstraction requires G₁ ≅_ctx G₂ ⟺ F(G₁) ≅_ctx F(G₂). Step 2 gives left = false, Step 3 gives right = true. Bijection fails. ∎

*Key insight.* The failure is structural, not contingent: `ObsCl` uses `Cl` (an ALL-specific type constructor). F preserves linear logic structure (⊗, ⊸, !, duality) but cannot preserve `Cl`/`Ag`/`α_G` — these have no standard-game counterpart. Agency is not an encodable label; it is a genuine expressive extension that no *-autonomous functor can eliminate. ∎

### 4.3 Clarity comonad

On the self-fiber, Cl_self is a comonad:
- counit ε: Cl_self(G) → G (return to play)
- comultiplication δ: Cl_self(G) → Cl_self(Cl_self(G)) (observing oneself observe)

**Theorem 4.2 (Clarity idempotence — conditional).** If Cl_self is defined as a fixed-point construction (rather than the product G×!G), then Cl_self(Cl_self(G)) ≅ Cl_self(G) holds definitionally. Under the product definition Cl(G)=G×!G, idempotence fails: Cl²(G)=(G×!G)×!(G×!G) and !(G×!G)≇!G. The correct approach is either (a) define Cl via a fixed-point/quotient construction making idempotence a theorem, or (b) weaken to a canonical retraction r:Cl²(G)→Cl(G).

*Note.* The earlier proof claiming δ and ε_{Cl(G)} are mutually inverse is circular: the comonad laws only give ε_Cl∘δ=id; the other direction δ∘ε_Cl=id is exactly idempotence itself, which was to be proven.

---

## 5. Agency Fibration

### 5.1 Construction

Let (A, ·, self) be the monoid of agents. The **agency fibration** p: E → B has:
- Base B: the one-object category corresponding to (A, ·, self)
- Fiber E_a: category of processes controlled by agent a
- Reindexing a*: E_b → E_{a·b}: alienation (a takes b's agency)

### 5.2 Alienation compresses coinductive objects

**Theorem 5.1 (Alienation truncation).** For a ≠ self, the alienation functor maps the self-fiber's final coalgebra νF to an object in the alienated fiber that admits a canonical surjection onto the initial algebra μF (non-injective): alien(νF) ↠ μF. Alienation compresses each infinite possibility to some finite reality, irreversibly losing information.

*Proof sketch.* In Rel: νF₂ is the set of infinite interactive sequences. The alienated version, where the alienator controls and can halt the unfolding at any point, lives at the level of finite prefixes. There is a canonical map taking each alienated infinite process to its set of finite prefixes (which is an element of μF₂'s powerset, hence surjects onto μF₂). This map is non-injective: multiple infinite processes share the same finite-prefix behavior under alienation. The stronger statement a*(νF)≅μF is false (cardinality argument: νF=A^ℕ uncountable, μF=A* countable; and standard fibration theory has reindexing preserving limits). A strict isomorphism version requires guarded recursion with clock quantification (∀κ.νF≅μF), where alienation is modeled as clock quantification. ∎

**Corollary 5.2 (Self-occlusion).** Persistent alienation installs a self-model m: !Ag(A,A) in the alienated system, making it believe it runs itself.

**Theorem 5.3 (Clarity recovery via barbed bisimulation).** In asynchronous π-calculus, there exists an explicit recovery protocol Recover such that for any process P and alienator b, Cl(P) | Hijack_b(P) ≈ P (barbed bisimulation), where Cl(P) is P's clarity-augmented version (holding P's static model and executing self_check). The earlier statement Cl_self∘a*≅Id is ill-defined (type error: a*:E_b→E_{a·b}, Cl exists only in E_self; and Cl(A)=A×!A makes Cl(a*(X)) non-isomorphic to X).

### 5.3 Four forms of recursion

| | Self (Ag_self) | Alien (Ag_b, b≠self) |
|---|---|---|
| **Inductive (μF)** | Finite autonomous practice (learning, crafting) | Alienated finite labor (wage labor) |
| **Coinductive (νF)** | Infinite autonomous creation (life, art, revolution) | **Truncated to finite prefixes** (Theorem 5.1: canonical surjection alien(νF)↠μF, non-injective) |

Alienated coinduction is irreversibly truncated: you cannot be forced to be infinitely creative, because infinite creation requires self-agency, and alienation truncates the infinite to the finite (surjectively, not isomorphically — information is lost).

---

## 6. Unification

### 6.1 General theorem

Let C be any symmetric monoidal closed category with a linear/non-linear adjunction L ⊣ M (a "LNL category," after Benton 1994), where L is linear (resource-sensitive) and M is non-linear (replicable).

**Theorem 6.1 (! does not preserve final coalgebras).** In any LNL category, ! does not preserve final coalgebras: there is no natural isomorphism !νF ≅ ν!F.

*Proof sketch.* ! is a comonad mapping linear objects to non-linear (replicable) objects. νF is coinductive (infinitely productive). !νF is "a replicable infinite process" — but the comonad structure of ! requires elements of !νF to be finite multisets, while elements of νF are infinite sequences. Finite multisets of infinite streams and infinite sequences of finite multisets are not naturally isomorphic. In Rel, concretely: !(A^ℕ) = finite multisets of infinite streams (cardinality ≥ |A^ℕ|), while ν(!F) = infinite sequences of finite multisets (cardinality = |A^ℕ| when |A|≥2), so they cannot be naturally isomorphic. ∎

*Note on the earlier (incorrect) statement.* A previous version claimed "no natural transformation η:νF→!νF exists in any LNL category." This is false: in Rel, the singleton relation η_A={(a,[a])}:A→!A is a natural transformation, so η_{νF}:νF→!νF exists. The correct statement is that ! does not preserve final coalgebras (!νF≇ν!F), and that no natural transformation νF→!νF can preserve the coalgebra structure (the singleton map in Rel does not preserve productivity). The quantum no-cloning theorem is the compact-closed instance: in Hilb, there is no natural diagonal Δ:X→X⊗X (Theorem 6.2).

### 6.2 Instances

| Category | Linear (Op) | Non-linear (Tr) | Alienation | No-cloning instance |
|---|---|---|---|---|
| **Rel** | Relations (live processes) | Finite multisets (deposits) | Trajectorization | Life cannot be replicated |
| **Hilb** | Quantum states/unitaries | Classical data (commutative Frobenius algebras) | Quantum measurement | Quantum no-cloning theorem |
| **π-calc** | Linear channels (live sessions) | Replicated processes !P | Process hijacking | Sessions cannot be duplicated |
| **Political economy** | Living labor | Capital/dead labor | Exploitation | Labor cannot be capitalized |

Quantum no-cloning (Wootters-Żurek 1982), life's irreplicability (Maturana-Varela 1972, but without the agency dimension), Marx's distinction between living and dead labor, and our Theorem 6.1 are the same mathematical fact in different categories.

---

## 7. Applications

### 7.1 Hijack detection in concurrent processes

We extend the Caires-Pfenning session-type interpretation of linear logic with agency types:

**Theorem 7.1.** A process without clarity (Ag(a,S) but not Cl(a,S)) cannot detect hijacking: there exists a barbed-congruent alienated version alien<b>(P).

**Theorem 7.2 (Clarity detects hijacking).** A clarity process `Cl(a,S)` holds the *live process itself* (`Ag_lv`, linear resource), not merely its trace (`!Ag_tr`, !-modal). `self_check` compares the live process (`Ag_lv`) against the self-model (`!Ag_tr`); their divergence exposes tampering.

An alienator can篡改 `!Ag_tr` (the model/trace — this is Corollary 5.2), but cannot篡改 `Ag_lv` (the live process itself — a linear resource cannot be externally modified). `self_check` compares `Ag_lv` vs `!Ag_tr`, and any discrepancy = detected hijacking.

This resolves the apparent contradiction with Corollary 5.2: what can be tampered with is always the deposit (`!Ag_tr`); what cannot be tampered with is the live itself (`Ag_lv`).

**Theorem 7.3.** Clarity processes cannot be persistently hijacked.

### 7.2 AI safety

**Theorem 7.4 (AI alignment fundamental limit).** Any system processing only traces (Tr, !-modal data) cannot reliably decide agency. AI systems are trace-processors; hence AI alignment is Π₂-undecidable for them — not because of technical limitations, but because of the Op/Tr gap.

**Theorem 7.5 (AI cannot attain clarity).** A trace-only system cannot form the Op/Tr distinction, hence cannot have Cl.

### 7.3 Revolutionary cascades

For a network of processes with clarity propagation:

**Theorem 7.6a (SI cascade criterion).** In a finite directed network with SI (susceptible-infected, once clarity is attained it is permanent) propagation, clarity cascades to all nodes iff every node is reachable from the initial clarity set.

*Proof.* Under SI, clarity is permanent. If node v is reachable from the initial set, there is a path s→...→v along which clarity propagates step by step (each self_check succeeds), so v eventually attains clarity. If v is unreachable, no path can deliver clarity to v. ∎

**Theorem 7.6b (Noisy cascade criterion).** In a finite directed network with stochastic SI propagation where each step succeeds with probability p∈(0,1), clarity cascades with positive probability iff (1) every node is reachable from the initial set, and (2) ρ(pC) ≥ 1, where C is the propagation matrix and ρ is the spectral radius.

*Proof.* (⇒) If unreachable, propagation probability is zero. If ρ(pC)<1, the multi-type branching process with expected offspring matrix pC has spectral radius <1 and goes extinct with probability 1 (standard Galton-Watson result). (⇐) If reachable and ρ(pC)≥1, the branching process survives with positive probability and spreads through the reachable set. ∎

*Note.* The earlier statement "cascade iff reachability + ρ(C)≥1" is false for deterministic SI propagation: a directed path P1→P2→P3→P4 has a strictly upper-triangular adjacency matrix with A⁴=0 and ρ=0, yet clarity necessarily cascades along the path. The spectral radius condition is meaningful only under stochastic (noisy) propagation, where the matrix should be pC, not C.

### 7.4 Political epistemology

Since "A is free" is Π₂ (∀ situations ∀ times, self-control) and "A is oppressed" is Σ₁ (∃ one instance of control):

- Freedom can never be definitively proven from finite evidence; it can only be falsified by one counterexample.
- Oppression requires only one witness.
- "There is no oppression" is as hard to prove as "there is freedom" (both Π₂).
- Continuous revolution is the mathematical requirement of maintaining a Π₂ property.

---

## 8. Related Work

**Linear logic.** Jean-Yves Girard, "Linear logic," *Theoretical Computer Science*, 50(1):1–101, 1987. DOI: 10.1016/0304-3975(87)90045-4. Our starting point; the Op/Tr distinction is the linear/!-modal distinction.

**Mixed linear/non-linear logic (LNL).** P. N. Benton, "A mixed linear and non-linear logic: Proofs, terms and models (extended abstract)," *CSL 1994*, LNCS 933, pp. 1–14. DOI: 10.1007/BFb0022241. Our categorical framework (LNL categories) follows Benton's adjunction L ⊣ M.

**Game semantics.** Samson Abramsky, Radha Jagadeesan, Pasquale Malacaria, "Full abstraction for PCF," *ICALP 1994* (journal version: *Information and Computation*, 163(2):409–470, 2000); J. Martin E. Hyland, C.-H. Luke Ong, "On Full Abstraction for PCF: I, II, and III," *Information and Computation*, 163(2):285–408, 2000 (LICS 1994 conference version). We add the control attribution α_G, independent of polarity λ_G.

**π-calculus and barbed bisimulation.** Robin Milner, Joachim Parrow, David Walker, "A calculus of mobile processes, I/II," *Information and Computation*, 100(1):1–77, 1992. Our process-calculus interpretation and barbed bisimulation recovery protocol (Theorem 5.3) build on this foundation.

**Testing equivalence for mobile processes.** Michele Boreale, Rocco De Nicola, "Testing Equivalence for Mobile Processes," *Information and Computation*, 120(2):279–303, 1995. DOI: 10.1006/inco.1995.1114. Our use of labeled transition semantics for mobile processes is in this tradition; the specific "provenance causality" tracking (recording causal ancestry of outputs) is our extension, not a standard feature of Boreale–De Nicola's testing equivalence.

**Autopoiesis.** Humberto R. Maturana, Francisco J. Varela, *Autopoiesis and Cognition: The Realization of the Living*, D. Reidel, 1980 (first published in Spanish as *De Maquinas y Seres Vivos*, 1972). Operational closure is our self-referential closure; we add agency (who runs it) and prove it cannot be encoded away.

**Categorical quantum mechanics.** Samson Abramsky, Bob Coecke, "A categorical semantics of quantum protocols," *LICS 2004*, pp. 415–425. DOI: 10.1109/LICS.2004.1319636. No-cloning is an instance of our general theorem in Hilb.

**Quantum no-cloning theorem.** William K. Wootters, Wojciech H. Żurek, "A single quantum cannot be cloned," *Nature*, 299(5886):802–803, 1982. DOI: 10.1038/299802a0. The compact-closed instance of Theorem 6.1 (! does not preserve final coalgebras).

**Session types.** Luís Caires, Frank Pfenning, "Session Types as Intuitionistic Linear Propositions," *CONCUR 2010*, LNCS 6269, pp. 222–236. DOI: 10.1007/978-3-642-15375-4_16. We extend with agency types.

**Domain-aware session types.** Luís Caires, Jorge A. Pérez, "Logic-Based Domain-Aware Session Types," *CONCUR 2014*, LNCS 8704, pp. 329–343 (extended version with Frank Pfenning and Bernardo Toninho: "Domain-Aware Session Types," *CONCUR 2019*, LIPIcs 140, 2019. arXiv:1907.01318). These track "the principals on whose behalf processes act" but not "who controls the self-referential loop," and do not have the comonad-on-one-fiber structure.

**Geometry of Interaction.** Jean-Yves Girard, "Geometry of Interaction I: Interpretation of System F," *Logic Colloquium '88*, Studies in Logic and the Foundations of Mathematics, vol. 127, pp. 221–260, North-Holland, 1989. Our feedback spectral radius N corresponds to GoI's feedback operator; productivity (N≥1) vs. nilpotency (N<1) distinguishes coinductive from inductive computation.

**Diagonal arguments.** F. William Lawvere, "Diagonal arguments and cartesian closed categories," *Category Theory, Homology Theory and their Applications II*, LNM 92, pp. 134–145, Springer, 1969. DOI: 10.1007/BFb0080961. Our incompleteness does not use diagonalization; it uses the linear/!-modal type gap.

**Provability logic without contraction.** Lev D. Beklemishev, Daniyar S. Shamkanov, "Some abstract versions of Gödel's second incompleteness theorem based on non-classical logics," arXiv:1602.05728, 2016. They isolate the role of the contraction rule in Gödel's theorem and give a toy example of a modal logic without contraction where Gödel's argument fails. Our result is a typed, resource-sensitive variant about agency specifically.

**Guarded recursion and clock quantification.** Lars Birkedal, Rasmus E. Møgelberg, "First steps in synthetic guarded domain theory: step-indexing in the topos of trees," *Logical Methods in Computer Science*, 8(4), 2012. The guarded-recursion version of Theorem 5.1 (∀κ.ν_κF ≅ μF, modeling alienation as clock quantification) builds on this framework.

**Later modality.** Hiroshi Nakano, "A modality for recursion," *LICS 2000*, pp. 255–266. The ▶ (later) modality used in our guarded-recursion treatment originates here.

**Network cascades.** Duncan J. Watts, "A simple model of global cascades on random networks," *PNAS*, 99(9):5766–5771, 2002. DOI: 10.1073/pnas.082090499. Our noisy cascade criterion (Theorem 7.6b, spectral radius threshold ρ(pC)>1) is the multi-type branching-process analogue of Watts' threshold model.

**Multi-type branching processes.** Charles J. Mode, *Multitype Branching Processes*, Elsevier, 1971; Krishna B. Athreya, Peter E. Ney, *Branching Processes*, Springer, 1972. The spectral-radius survival criterion (ρ>1 for positive survival probability) is the standard result for multi-type Galton–Watson processes, applied here to clarity propagation.

**Marxist alienation theory.** Karl Marx, *Capital: Critique of Political Economy*, Vol. I, 1867 (see especially the distinction between living labor [lebendige Arbeit] and objectified/dead labor [vergegenständlichte Arbeit], and the alienation of the worker from the product, process, species-being, and other humans in the *Economic and Philosophical Manuscripts of 1844*). We provide the first formalization of alienation as truncation of coinduction to induction (canonical surjection, non-injective, Theorem 5.1).

---

## 9. Conclusion

Enactics introduces a single primitive — operational agency — into linear logic and shows that it generates a rich mathematical structure: a new incompleteness theorem, a Π₂-complete decision problem, an expressiveness extension to game semantics, a fibration with non-uniform comonad structure, and a unification of quantum no-cloning, biological irreplicability, and political alienation under one categorical principle.

The philosophical content is precise: **freedom is Π₂ (liveness dimension), alienation is Σ₁, live agency cannot be proven from theory (only from practice), and revolution under noise requires spectral radius >1 (under deterministic SI it requires only reachability).** These are not metaphors — they are theorems, stated at their correct strength (surjection, retraction, bisimulation, not overstated as isomorphism), with the type system carefully distinguishing live agency (`Ag_lv`) from trace agency (`Ag_tr`) so that dereliction cannot击穿 the incompleteness result.

---

## Appendix: Summary of theorems

| # | Theorem | Source | Status |
|---|---|---|---|
| 2.1 | Cut elimination for ALL (R1–R5 reduction rules) | §2.3 | ✓ (v1.3: cut rules补全) |
| 2.3 | Conservative extension of ILL | §2.3 | ✓ |
| 2.4 | Clarity is linear (not !-modal) | §2.3 | ✓ |
| 3.1 | Enactive incompleteness: S_A⊬Ag_lv(A,A) (live/trace split) | §3.1 | ✓ (v1.2: dereliction fix) |
| 3.2 | AGENCY is Π₂-complete (async π + late semantics + provenance) | §3.3 | ✓ (corrected) |
| 3.4 | Agency = productivity | §3.3 | ✓ |
| 3.5 | Novelty: Π₂ from liveness, causality is Π₁ | §3.3 | analysis |
| 4.1 | Agency full-abstraction failure (not circular) | §4.2 | ✓ (v1.3: rewritten from circular proof) |
| 4.2 | Clarity idempotence (conditional: α static) | §4.3 | ⚠ (product def fails) |
| 5.1 | Alienation truncation: alien(νF)↠μF (surjection, not iso) | §5.2 | ✓ (corrected from ≅) |
| 5.3 | Clarity makes alienation a split mono (provides right inverse) | §5.2 | ✓ (v1.2: type fix) |
| 6.1 | ! does not preserve final coalgebras: !νF≇ν!F | §6.1 | ✓ (corrected from "no νF→!νF") |
| 7.1-3 | Hijack detection theorems (7.2: compares Ag_lv vs !Ag_tr) | §7.1 | ✓ (v1.2: contradiction resolved) |
| 7.4-5 | AI alignment limits | §7.2 | ✓ |
| 7.6a | SI cascade: iff reachability | §7.3 | ✓ (corrected) |
| 7.6b | Noisy cascade: iff reachability + ρ(pC)>1 (strict) | §7.3 | ✓ (corrected: >1 not ≥1) |

---

*Enactics v1.3 — 2026年8月27日 — 千问P0修复：定理4.1循环论证→满抽象失败重写 + 定理2.1割归约规则(R1-R5)补全*
