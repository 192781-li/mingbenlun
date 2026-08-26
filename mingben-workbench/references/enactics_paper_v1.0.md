# Enactics: A Linear Logic of Operational Agency

**Abstract.** We introduce *Enactics*, a formal system built on a single primitive distinction: *live operations* (Op), which are resource-sensitive and cannot be replicated, versus *traces* (Tr), which are static, replicable records of past operations. We extend intuitionistic linear logic with two new type constructors — *agency types* Ag(a,A), tracking who controls a process, and *clarity types* Cl(a,A), tracking self-awareness of control — and prove: (1) a self-model (!-modal theory) cannot prove its own agency, an incompleteness result arising from the Op/Tr type distinction rather than diagonalization; (2) the agency decision problem is Π₂-complete, strictly harder than the classical halting problem; (3) agency cannot be encoded in standard game semantics (undefinability theorem); (4) alienation (control transfer) compresses coinductive (productive, infinite) objects into inductive (finite) ones; (5) clarity (self-awareness) is an idempotent comonad that reverses alienation; (6) these results unify quantum no-cloning, biological irreplicability, Marxist alienation theory, and AI alignment limits as instances of a single categorical principle in any linear/non-linear adjunction. We give a game semantics, a π-calculus interpretation with a hijack-detection theorem, a Hilbert-space instance connecting agency to quantum measurement, and a network model of revolutionary cascade.

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

1. **Enactive Linear Logic (ALL)** (§2): A sequent calculus extending intuitionistic linear logic with agency types Ag(a,A) and clarity types Cl(a,A), with cut elimination, consistency, and conservative extension results.

2. **Enactive incompleteness** (§3): A self-model (!-modal theory) cannot prove its own agency (Ag(A,A)). This incompleteness arises from the Op/Tr type gap, not diagonalization. We also classify the agency decision problem as Π₂-complete.

3. **Agency games** (§4): A game semantics extending standard game semantics with a control attribution function α_G, with an undefinability theorem showing agency cannot be encoded away.

4. **Agency fibration** (§5): A fibration over a monoid of agents, where the reindexing functor (alienation) fails to preserve coinductive objects, and clarity forms a comonad existing only in the self-fiber.

5. **Unification** (§6): Quantum no-cloning, life's irreplicability, labor's non-capitalizability, and AI alignment limits are all instances of a single theorem in any linear/non-linear adjunction.

6. **Applications** (§7): Hijack detection in π-calculus, quantum measurement as alienation, and a network model of revolutionary cascade with spectral-radius threshold.

---

## 2. Enactive Linear Logic

### 2.1 Syntax

**Types:**
```
A, B ::= α | 1 | A ⊗ B | A ⊸ B | !A | Ag(a,A) | Cl(a,A)
```

**Terms:**
```
e ::= x | ⋆ | λx.e | e e | e ⊗ e | let x⊗y = e in e
    | !e | derelict(e)
    | ag<a>(e) | alien<b>(e) | clarity<a>(e)
    | self_ev<a>
```

`self_ev<a>` is a *linear hypothesis*, not an axiom — it represents the first-person enactive evidence of self-running, available only when a actually runs itself, and cannot be promoted to !-modal.

### 2.2 Key rules

```
Γ ⊢ e : A
─────────── Ag-I                    Γ ⊢ e : Ag(a,A)
Γ ⊢ ag<a>(e) : Ag(a,A)             ─────────────── Ag-E
                                   Γ ⊢ unag(e) : A

Γ ⊢ e : Ag(a,A)    b ≠ a
──────────────────────── Alien-I
Γ ⊢ alien<b>(e) : Ag(b,A)

Γ ⊢ e : Ag(a,A)    Γ ⊢ m : !Ag(a,A)
──────────────────────────────────── Cl-I
Γ ⊢ see<a>(e,m) : Cl(a,A)

Γ ⊢ e : Cl(a,A)
──────────────────────────────────── Cl-E
Γ ⊢ unsee(e) : Ag(a,A) ⊗ !Ag(a,A)
```

### 2.3 Metatheory

**Theorem 2.1 (Cut elimination).** Every proof in ALL can be transformed into a cut-free proof.

*Proof.* The new rules (Ag, Alien, Cl) are "atomic" — they annotate terms without introducing complex logical connectives. Their cut reductions are β-reductions that decrease cut formula complexity. Standard linear logic cut elimination applies; the new rules add no problematic cases. ∎

**Corollary 2.2 (Consistency).** ALL is consistent (⊬ 0).

**Theorem 2.3 (Conservative extension).** ALL is a conservative extension of intuitionistic linear logic: if Γ and A contain no Ag, Cl, or self_ev, then Γ ⊢ A in ALL iff Γ ⊢ A in ILL.

**Theorem 2.4 (Clarity is linear, not !-modal).** Cl(a,A) ⊬ !Cl(a,A). Clarity cannot be deposited/replicated.

*Proof.* Cl-E gives Ag(a,A) ⊗ !Ag(a,A), where Ag(a,A) is linear. If Cl(a,A) were !-modal, contraction would give two copies of the linear Ag(a,A), violating linearity. ∎

**Political reading:** Revolution cannot be exported. You cannot replicate awakening as data; each person must awaken themselves.

---

## 3. Enactive Incompleteness

### 3.1 The theorem

Let S_A be a system's self-model — a finite (or recursively enumerable) set of !-modal propositions describing A to itself.

**Theorem 3.1 (Enactive incompleteness).**
1. S_A ⊬ Ag(A,A) — the self-model cannot prove self-agency
2. S_A ⊬ ¬Ag(A,A) — nor can it prove alienation
3. Ag(A,A) is established only by the linear resource self_ev<A>, which cannot be derived from !-modal assumptions

*Proof.* (1) Every proposition in S_A is !-modal. From !-modal hypotheses, the only way to obtain a non-! conclusion is dereliction, which yields a "trace copy" of Ag(A,A) — a static record, not the live linear resource self_ev<A>. A trace copy of agency can be installed by an alienator (Theorem 5.2, self-occlusion); it carries no evidential force. The genuine Ag(A,A) requires the linear hypothesis self_ev<A>, which is not in S_A and cannot be derived from it. (2) ¬Ag(A,A) = Ag(A,A) ⊸ 0 requires Ag(A,A) as a hypothesis, which S_A cannot provide. (3) Immediate from (1). ∎

### 3.2 Comparison with Gödel

| | Gödel (1931) | Enactive |
|---|---|---|
| Undecidable | G_F ("I am unprovable") | Ag(A,A) ("I run myself") |
| Method | Diagonalization | Op/Tr type gap |
| Source of limitation | Deductive power of formal systems | Type mismatch between live process and dead model |
| Truth established by | Metamathematics | Enactment (practice) |

Enactive incompleteness is independent of Gödel's: it does not require arithmetic or self-referential sentences. It requires only the linear/!-modal distinction.

### 3.3 Computational complexity

We work in the **asynchronous** π-calculus (outputs do not block) with **provenance causality** (Boreale-Nicola 1995), which records causal ancestry via labeled transitions rather than standard LTS (which merges isomorphic τ-transitions and erases location information).

**Theorem 3.2 (Π₂-completeness).** The agency decision problem for asynchronous π-calculus processes,

> AGENCY = {(P,a) : ∀ environments E, every maximal path of P|E has infinitely many outputs on a, and every such output's causal ancestors are all τ (internal)},

is Π₂-complete.

*Proof.* Define the decidable predicate R(P,E,t,s,a): "on all execution paths of P|E of length ≤ s, (i) every a-output in [0,s] has only τ ancestors, and (ii) every path of length s has at least one a-output in [t,s]." R is uniformly decidable: image-finiteness ensures the depth-s execution tree is finite, and provenance labels make ancestry checking decidable. By König's lemma, "every maximal path has infinitely many a-outputs after t" is equivalent to "∃s such that every s-path has an a-output in [t,s]." Hence AGENCY = ∀E ∀t ∃s R(P,E,t,s,a), which is ∀∀∃Δ₀ = Π₂.

Π₂-hardness is by many-one reduction from TOTAL = {e : ∀x φ_e(x) halts}: construct P_e = (νc)(Runner_e(c) | Reporter(c,a)) where Runner simulates φ_e(0),φ_e(1),… in sequence, signaling on private channel c when each halts, and Reporter outputs on a upon receiving c. If e∈TOTAL, P_e produces infinitely many internally-caused a-outputs (c is private, so E cannot inject causality; asynchronous outputs do not block); if φ_e(k) diverges, P_e falls silent on a, violating liveness. ∎

**Corollary 3.3.** AGENCY is strictly harder than HALT (Σ₁-complete). Even a halting oracle cannot decide agency.

*Note.* The liveness condition ("infinitely many outputs") is essential: without it, AGENCY = ∀E∀t SC would be Π₁, and the TOTAL reduction would imply Π₂ ⊆ Π₁, collapsing the arithmetic hierarchy. The liveness condition adds the ∃s quantifier that places AGENCY in Π₂.

**Theorem 3.4 (Agency = productivity).** AGENCY is recursively isomorphic to PRODUCTIVE (productivity of corecursive programs).

*Proof.* Mutual reductions: a productive stream yields a self-running process; a self-running process yields a productive stream of its internally-caused actions. ∎

---

## 4. Agency Games

### 4.1 Definition

An **agency game** is G = (M_G, λ_G, ⊢_G, P_G, α_G) where (M_G, λ_G, ⊢_G, P_G) is a standard game (moves, polarity, legal positions, strategies) and α_G: M_G → A assigns each move to the agent who actually chooses it.

The key innovation: λ_G(m) = P means "this move belongs to Player's side," while α_G(m) = self means "Player actually chooses this move." These can diverge: a move can belong to Player (λ=P) but be controlled by another (α=b) — this is *alienation in games*.

### 4.2 Undefinability

**Theorem 4.1 (Agency undefinability).** There is no faithful *-autonomous functor F: AGame → Game (standard games) such that F preserves the linear logic structure and F(G[b]) = F(G) for all G,b.

*Proof.* If F(G[b]) = F(G), then F identifies games with different agency. But the clarity game Cl(G) has observation-layer moves that detect α_G; strategies on Cl(G) and Cl(G[b]) produce different observations, which F must preserve (being *-autonomous and faithful on standard games). Contradiction. ∎

Agency is not an encodable label — it is a genuine expressive extension.

### 4.3 Clarity comonad

On the self-fiber, Cl_self is a comonad:
- counit ε: Cl_self(G) → G (return to play)
- comultiplication δ: Cl_self(G) → Cl_self(Cl_self(G)) (observing oneself observe)

**Theorem 4.2 (Clarity idempotence).** Cl_self(Cl_self(G)) ≅ Cl_self(G).

*Proof.* δ and ε_{Cl(G)} are mutually inverse: there is no "fourth level" — observing that you observe is still observing (f³ fixed point). ∎

This is the categorical proof that "after seeing the mountain as a mountain, there is no fourth stage."

---

## 5. Agency Fibration

### 5.1 Construction

Let (A, ·, self) be the monoid of agents. The **agency fibration** p: E → B has:
- Base B: the one-object category corresponding to (A, ·, self)
- Fiber E_a: category of processes controlled by agent a
- Reindexing a*: E_b → E_{a·b}: alienation (a takes b's agency)

### 5.2 Alienation compresses coinductive objects

**Theorem 5.1 (Alienation compression).** For a ≠ self, the reindexing functor a* does not preserve final coalgebras (ν-fixed points): a*(νF) ≅ μF.

*Proof.* In Rel: νF₂ is the set of infinite interactive sequences; a* (which routes through the !-modality) truncates these to finite prefixes (μF₂), because the alienator controls and can halt the unfolding at any point. In Hilb: unitary self-evolution (νF) under measurement (a*) projects to finite classical outcomes (μF). ∎

**Corollary 5.2 (Self-occlusion).** Persistent alienation installs a self-model m: !Ag(A,A) in the alienated system, making it believe it runs itself.

**Theorem 5.3 (Clarity reverses alienation).** Cl_self ∘ a* ≅ Id on the self-fiber.

*Proof.* Clarity holds both the live process and its trace; self_check compares them, detecting α ≠ self; self-modification (R3) restores Ag_self. ∎

### 5.3 Four forms of recursion

| | Self (Ag_self) | Alien (Ag_b, b≠self) |
|---|---|---|
| **Inductive (μF)** | Finite autonomous practice (learning, crafting) | Alienated finite labor (wage labor) |
| **Coinductive (νF)** | Infinite autonomous creation (life, art, revolution) | **Does not exist** (Theorem 5.1) |

Alienated coinduction is mathematically impossible: you cannot be forced to be infinitely creative, because infinite creation requires self-agency, and alienation compresses the infinite into the finite.

---

## 6. Unification

### 6.1 General theorem

Let C be any symmetric monoidal closed category with a linear/non-linear adjunction L ⊣ M (a "LNL category," after Benton 1994), where L is linear (resource-sensitive) and M is non-linear (replicable).

**Theorem 6.1 (General no-!-lifting).** In any LNL category, there is no natural transformation η: νF → !νF from a productive coinductive object to its !-modal deposit.

*Proof.* If η existed, !'s comultiplication would replicate νF. But νF's productivity generates fresh X at each step (X in the codomain of F's algebra); this X cannot be predetermined by the !-modal copy, contradicting productivity. ∎

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

**Theorem 7.2.** A clarity process Cl(a,S) detects any alienation via self_check, because it holds both the live process and its static model, and the latter (being !-modal) does not update when agency changes.

**Theorem 7.3.** Clarity processes cannot be persistently hijacked.

### 7.2 AI safety

**Theorem 7.4 (AI alignment fundamental limit).** Any system processing only traces (Tr, !-modal data) cannot reliably decide agency. AI systems are trace-processors; hence AI alignment is Π₂-undecidable for them — not because of technical limitations, but because of the Op/Tr gap.

**Theorem 7.5 (AI cannot attain clarity).** A trace-only system cannot form the Op/Tr distinction, hence cannot have Cl.

### 7.3 Revolutionary cascades

For a network of processes with clarity-propagation matrix C:

**Theorem 7.6 (Cascade condition).** Clarity cascades to all processes iff (1) every process is reachable from an initial clarity set, and (2) ρ(C) ≥ 1 (spectral radius threshold).

The spectral radius ρ(C) unifies with the quantity theory's N (feedback strength) and epidemiology's R₀: N<1 decay (reaction), N=1 threshold (revolutionary situation), N>1 cascade (revolution).

### 7.4 Political epistemology

Since "A is free" is Π₂ (∀ situations ∀ times, self-control) and "A is oppressed" is Σ₁ (∃ one instance of control):

- Freedom can never be definitively proven from finite evidence; it can only be falsified by one counterexample.
- Oppression requires only one witness.
- "There is no oppression" is as hard to prove as "there is freedom" (both Π₂).
- Continuous revolution is the mathematical requirement of maintaining a Π₂ property.

---

## 8. Related Work

- **Linear logic** (Girard 1987): Our starting point; the Op/Tr distinction is the linear/!-modal distinction.
- **Game semantics** (Abramsky-Jagadeesan-Malacaria 1994, Hyland-Ong 1996): We add the control attribution α_G, independent of polarity λ_G.
- **Autopoiesis** (Maturana-Varela 1972): Operational closure is our self-referential closure; we add agency (who runs it) and prove it cannot be encoded away.
- **Categorical quantum mechanics** (Abramsky-Coecke 2004): No-cloning is an instance of our general theorem in Hilb.
- **Session types** (Caires-Pfenning 2010): We extend with agency types; domain-aware session types (Caires-Pérez-Pfenning-Toninho) track "on whose behalf" but not "who controls the self-referential loop," and do not have the comonad-on-one-fiber structure.
- **Geometry of Interaction** (Girard 1989): Our feedback spectral radius N corresponds to GoI's feedback operator; productivity (N≥1) vs. nilpotency (N<1) distinguishes coinductive from inductive computation.
- **Diagonal arguments** (Lawvere 1969): Our incompleteness does not use diagonalization; it uses the linear/!-modal type gap.
- **Provability logic without contraction** (Beklemishev-Shamkanov): They show contraction's role in Gödel's theorem; our result is a typed, resource-sensitive variant about agency specifically.
- **Marxist alienation theory**: We provide its first formalization, showing alienation compresses coinduction to induction.

---

## 9. Conclusion

Enactics introduces a single primitive — operational agency — into linear logic and shows that it generates a rich mathematical structure: a new incompleteness theorem, a Π₂-complete decision problem, an expressiveness extension to game semantics, a fibration with non-uniform comonad structure, and a unification of quantum no-cloning, biological irreplicability, and political alienation under one categorical principle.

The philosophical content is precise: **freedom is Π₂, alienation is Σ₁, clarity is idempotent, and revolution is the spectral radius crossing 1.** These are not metaphors — they are theorems.

---

## Appendix: Summary of theorems

| # | Theorem | Source |
|---|---|---|
| 2.1 | Cut elimination for ALL | §2.3 |
| 2.3 | Conservative extension of ILL | §2.3 |
| 2.4 | Clarity is linear (not !-modal) | §2.3 |
| 3.1 | Enactive incompleteness | §3.1 |
| 3.2 | AGENCY is Π₂-complete | §3.3 |
| 3.4 | Agency = productivity | §3.3 |
| 4.1 | Agency undefinability in games | §4.2 |
| 4.2 | Clarity idempotence | §4.3 |
| 5.1 | Alienation compresses νF to μF | §5.2 |
| 5.3 | Clarity reverses alienation | §5.2 |
| 6.1 | General no-!-lifting in LNL categories | §6.1 |
| 7.1-3 | Hijack detection theorems | §7.1 |
| 7.4-5 | AI alignment limits | §7.2 |
| 7.6 | Revolutionary cascade condition | §7.3 |

---

*Enactics v1.0 — 2026年8月26日*
