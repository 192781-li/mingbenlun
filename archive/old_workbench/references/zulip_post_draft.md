# Zulip发帖草稿

**发布位置**：Category Theory Zulip → "theory: type theory & logic" stream
**标题**：Is this known? Distributive law of linear exponential comonad over polynomial functors

---

## 正文

Hi all,

I'm working in intuitionistic multiplicative-additive linear logic (IMELL) with the standard linear exponential comonad `!`. I've been studying when the distributive law / natural transformation

    !F(X) → F(!X)

exists for polynomial functors F built from X, constants, ⊗, &, ⊕, ⊸, and !. I have a recursive characterization (four judgments P/D/Q/R tracking promotability and derelictability through each connective), and the main result is:

**The distributive law !F(X) → F(!X) exists if and only if X does not occur in the codomain of a linear implication (behind ⊸) or in a branch of ⊕, unless it is under a !.**

Concretely:
- `!(X ⊗ B) → !X ⊗ B` is derivable (via monoidal strength + dereliction)
- `!(X & B) → !X & B` is derivable
- `!(A ⊸ (X ⊗ B)) → A ⊸ (!X ⊗ B)` is NOT derivable — this is the key case
- `!(X ⊕ B) → !X ⊕ B` is NOT derivable
- `!(X ⊸ B) → !X ⊸ B` IS derivable (X in domain is fine — dereliction on !X gives X)

The proof for the key case `!(A ⊸ (X ⊗ B)), A ⊢ !X ⊗ B` is by case analysis on the last rule (⊗R with four possible context splits, all fail; promotion can't be last since the conclusion doesn't start with !).

Two questions:

1. **Is this characterization already known?** I've found related work on "strong functors" w.r.t. ! (e.g., Clairambault et al. 2019 on denotational semantics of μLL), but their strength is `!X ⊗ F(Y) → F(!X ⊗ Y)`, which is a different notion from `!F(X) → F(!X)`. I haven't found a paper that characterizes which polynomial functors admit the distributive law.

2. **The ⊸ case has an interesting interpretation**: `F(X) = A ⊸ (X ⊗ B)` is the Mealy machine functor. The non-existence of `!F ⇒ F!` says that the exponential comonad doesn't lift to interactive coalgebras — you can't "capitalize" (turn into !-modal/replicable) an interactive process that takes input A and produces a fresh X. It does lift to non-interactive coalgebras `F₁(X) = X ⊗ B`. This gives a categorical formulation of Marx's "formal/real subsumption" and, separately, seems to correspond to the quantum no-programming theorem (Nielsen-Chuang 1997). Is anyone aware of prior work connecting linear logic distributive laws to either of these?

Happy to share the full proof (about 10 pages with sequent calculus derivations) if helpful.

Thanks!
