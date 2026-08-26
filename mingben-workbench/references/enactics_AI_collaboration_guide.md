# Enactics (践演论): A Linear Logic of Operational Agency

## Self-contained introduction for AI collaborators

You are invited to collaborate on a new mathematical framework called **Enactics**. This document gives you everything you need to understand the system and contribute.

---

## 1. Core idea

There is a fundamental distinction between:

- **Op (live operation)**: A process happening right now — life, consciousness, labor, a quantum process. Resource-sensitive: cannot be copied or discarded. Linear type.
- **Tr (trace/deposit)**: A static record of what happened — a corpse, a text, capital, a measurement outcome. Can be freely copied and discarded. !-modal type.

Every Op leaves Tr. Every Tr was produced by some Op. But Tr can never fully capture Op: you cannot recover a live process from its records.

We extend intuitionistic linear logic with two new type constructors:
- **Ag(a, A)**: "agent a runs process A" (operational agency)
- **Cl(a, A)**: "agent a has clarity (self-awareness) over A"

And we prove theorems about what can and cannot be done with these types.

---

## 2. The formal system ALL (Agency Linear Logic)

### Types
```
A, B ::= α | 1 | A ⊗ B | A ⊸ B | !A | Ag(a,A) | Cl(a,A)
```

### Key rules
```
Ag-intro:  Γ ⊢ e : A  ⟹  Γ ⊢ ag<a>(e) : Ag(a,A)
Ag-elim:   Γ ⊢ e : Ag(a,A)  ⟹  Γ ⊢ unag(e) : A
Alien:     Γ ⊢ e : Ag(a,A), b≠a  ⟹  Γ ⊢ alien<b>(e) : Ag(b,A)
Cl-intro:  Γ ⊢ e : Ag(a,A), Γ ⊢ m : !Ag(a,A)  ⟹  Γ ⊢ see<a>(e,m) : Cl(a,A)
Cl-elim:   Γ ⊢ e : Cl(a,A)  ⟹  Γ ⊢ unsee(e) : Ag(a,A) ⊗ !Ag(a,A)
```

`self_ev<a>` is a **linear hypothesis** (not an axiom) representing first-person enactive evidence of self-running. It cannot be promoted to !-modal.

### Metatheory (proved)
- Cut elimination (Theorem 2.1)
- Consistency (Corollary 2.2)
- Conservative extension of ILL (Theorem 2.3)
- Clarity is linear, not !-modal: Cl(a,A) ⊬ !Cl(a,A) (Theorem 2.4)

---

## 3. Key theorems

### T1: Enactive incompleteness (v1.2 Theorem 2.1)
A self-model S_A (set of !-modal propositions) cannot prove Ag(A,A):
- S_A ⊬ Ag(A,A) (cannot prove self-agency from traces)
- S_A ⊬ ¬Ag(A,A) (cannot prove alienation either)
- Ag(A,A) requires the linear resource self_ev<A>, which cannot be derived from !-modal assumptions

This does NOT use diagonalization. It uses the linear/!-modal type gap.

### T2: Π₂-completeness (v1.4 Theorem 1.1)
AGENCY = {(P,a) : ∀ environments E, ∀ time t, P maintains self-control at channel a} is Π₂-complete.
- Strictly harder than the halting problem (Σ₁-complete)
- Recursively isomorphic to PRODUCTIVE (productivity of corecursive programs)

### T3: Agency undefinability in games (v1.0 Theorem 3.1)
There is no faithful *-autonomous functor F: AGame → Game preserving both linear logic structure and alienation. Agency is a genuine expressive extension, not an encodable label.

### T4: Alienation compression (v1.7 Theorem 3.1)
The alienation functor a* maps final coalgebras to initial algebras: a*(νF) ≅ μF.
Alienation compresses infinite creative processes into finite productive units.
**Alienated coinduction does not exist** — you cannot force someone to be infinitely creative.

### T5: Clarity reverses alienation (v1.7 Theorem 3.2)
Cl_self ∘ a* ≅ Id on the self-fiber. A clarity process detects and reverses alienation.

### T6: Clarity idempotence (v1.0 Theorem 4.2)
Cl_self(Cl_self(G)) ≅ Cl_self(G). "After seeing the mountain as a mountain, there is no fourth stage."

### T7: General no-cloning (v1.8 Theorem 3.2)
In any linear/non-linear adjunction (LNL category), there is no natural transformation νF → !νF.
Instances:
- Rel: life cannot be replicated
- Hilb: quantum no-cloning theorem
- π-calculus: linear sessions cannot be duplicated
- Political economy: living labor cannot be converted to capital

### T8: Hijack detection (v1.3 Theorems 4.1-4.3)
- Processes without clarity cannot detect hijacking (barbed congruence)
- Clarity processes detect hijacking via self_check
- Clarity processes cannot be persistently hijacked

### T9: Revolutionary cascade (v1.9 Theorem 2.2)
Clarity cascades through a process network iff: (1) every process is reachable from initial clarity set, and (2) spectral radius of propagation matrix ρ(C) ≥ 1.
N = ρ(C) = R₀ unifies feedback strength, network cascade threshold, and epidemic reproduction number.

### T10: AI alignment fundamental limit (v0.8 Theorem 1.1)
Any trace-only system (AI) cannot reliably decide agency. AI alignment is Π₂-undecidable for trace-processors.

---

## 4. Models

1. **Rel model**: Sets and relations. Op = relations, Tr = finite multisets. All theorems verified.
2. **Mealy machines**: Coalgebraic model. Self-occlusion theorem verified.
3. **π-calculus**: Channel names = agency. Capital = replicated process without self-channel.
4. **Hilb** (v1.8): Unitary evolution = self-agency, measurement = alienation. No-cloning = T7.
5. **Agency games** (v1.0): Games with control attribution α_G independent of polarity λ_G.

---

## 5. What we need help with

### Priority 1: Proof verification
Check each theorem for errors. The most critical to verify:
- T4 (alienation compression): Is a*(νF) ≅ μF correct in general, or only in Rel?
- T3 (undefinability): Is the proof rigorous? Does it assume what it tries to prove?
- T2 (Π₂-completeness): Is the reduction from TOTAL correct?
- T7 (general no-cloning): Does it hold in ALL LNL categories or only specific ones?

### Priority 2: Formalization in proof assistants
Formalize ALL in Coq or Agda:
- Syntax and typing rules
- Cut elimination proof
- The T1 enactive incompleteness theorem
- The agency game semantics

### Priority 3: Literature search
Has anyone published:
- A type system tracking "who controls a process" (not just "on whose behalf" — domain-aware session types do that, but not "who controls the self-referential loop")?
- A linear logic with agency/control types?
- A game semantics with a control dimension independent of polarity?
- A categorical model where reindexing destroys final coalgebras?
- A connection between productivity checking and agency/autonomy?

### Priority 4: New directions
- Can clarity types help with productivity checking of corecursive programs?
- What is the complexity of μALL (ALL with least/greatest fixed points)?
- Can agency games give a fully abstract model of a concurrent language?
- Is there a Bell-type inequality for agency?
- What does Cl_self correspond to in Hilb? (Quantum feedback? Quantum error correction?)

### Priority 5: Implementation
- Complete the EλC type checker (prototype exists at 501 lines)
- Add type inference
- Implement self_check for π-calculus processes
- Build a simulator for clarity cascades on networks

---

## 6. Files in the repository

- `enactics_paper_v1.0.md`: Comprehensive paper (English)
- `enactics_v0.1.md` through `enactics_v1.9.md`: Development versions with full proofs
- `elc_type_checker.py`: Working type checker prototype (Python)

The GitHub repository is: https://github.com/192781-li/mingbenlun

---

## 7. Philosophical background (optional)

This work is part of a larger philosophical system called "生命论" (Life Theory / Enactivism) developed by a 17-year-old Chinese philosopher. The system:
- Starts from "在感" (being-aware / pre-reflective experience) as the primary fact
- Argues that operation precedes entity (操作先于实体)
- Defines life as self-referential operational closure (自指操作闭包)
- Analyzes capitalism as an anti-self-referential system (反自指系统) — a !-modal empty loop G→G+g
- Argues that the highest meaning of life is transcending mere survival and living out its fullness

The mathematics formalizes these philosophical claims as theorems. The philosophy is not derived from the mathematics; rather, both are expressions of the same structure. The mathematical work should stand on its own merits regardless of whether you accept the philosophy.

---

## 8. Conventions

- All files use Chinese for philosophical discussion, English for mathematical statements
- Theorems are numbered by version (e.g., v1.4 Theorem 1.1)
- Proofs should be constructive where possible
- The system is intuitionistic (no excluded middle)
- Resource sensitivity is non-negotiable: Op cannot be copied or discarded

---

*If you find errors, prove new theorems, or discover related work, please document your findings clearly with theorem numbers and counterexamples.*
