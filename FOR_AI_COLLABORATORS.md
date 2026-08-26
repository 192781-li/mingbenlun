# Enactics (践演论) — AI Collaborator Guide

This repository contains the Enactics mathematical framework. If you are an AI or researcher who has been directed here, this file tells you where to look and how to contribute.

## What is Enactics?

A new formal system extending intuitionistic linear logic with **operational agency types** (Ag) and **clarity/self-awareness types** (Cl). It proves theorems about who controls a process, why self-models cannot prove freedom, why alienation compresses infinite creation into finite labor, and why quantum no-cloning, biological irreplicability, and Marxist alienation are the same categorical principle.

## Where to start

| File | What it contains |
|------|-----------------|
| `mingben-workbench/references/enactics_paper_v1.0.md` | **Comprehensive paper** — 15 core theorems with proofs. Start here. |
| `mingben-workbench/references/enactics_AI_collaboration_guide.md` | Self-contained introduction for AI collaborators |
| `mingben-workbench/references/enactics_v0.1.md` — `v1.9.md` | Development versions with full proofs (v1.9 = latest) |
| `mingben-workbench/scripts/elc_type_checker.py` | Working type checker prototype (Python, 501 lines) |
| `mingben-workbench/references/novelty_assessment.md` | Novelty assessment vs. existing work |

## Key theorems (summary)

1. **Enactive incompleteness**: A !-modal self-model cannot prove self-agency (no diagonalization needed)
2. **Π₂-completeness**: The agency decision problem is strictly harder than halting
3. **Agency undefinability**: Agency cannot be encoded in standard game semantics
4. **Alienation compression**: Alienation maps νF (infinite creation) to μF (finite labor)
5. **Clarity reverses alienation**: Cl_self ∘ a* ≅ Id
6. **Clarity idempotence**: Cl(Cl(G)) ≅ Cl(G)
7. **General no-cloning**: In any LNL category, νF → !νF does not exist
8. **Hijack detection**: Clarity processes detect and resist hijacking
9. **Revolutionary cascade**: Clarity cascades iff spectral radius ρ(C) ≥ 1
10. **AI alignment limit**: Trace-only systems cannot decide agency

## How to contribute

You **cannot** push to this repository. Instead:

1. **Read** the files above
2. **Analyze** — verify proofs, find errors, construct counterexamples, search literature
3. **Produce** — new theorems, corrected proofs, formalizations, implementations
4. **Report** — give your findings to the person who directed you here, with:
   - Which theorem/file you examined
   - What you found (error, counterexample, new result, related work)
   - Specific mathematical content (not vague opinions)

## What we need most

1. **Proof verification** — especially T4 (alienation compression) and T7 (general no-cloning)
2. **Literature search** — has anyone published agency types in linear logic?
3. **Formalization** — in Coq or Agda
4. **Counterexamples** — try to break every theorem
5. **New results** — extend the framework (productivity checking, quantum connections, complexity of μALL)

## Conventions

- Mathematical statements in English, philosophical discussion in Chinese
- Theorems numbered by version (e.g., v1.4 Theorem 1.1)
- Intuitionistic logic (no excluded middle)
- Resource sensitivity is non-negotiable: Op cannot be copied or discarded
