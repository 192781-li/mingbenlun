# Coq编码指南 · 给Workbody

> 你不用装Coq，也不用跑coqc。你只需要写Coq代码，写完放到`coq/incoming/`，文件名`T00X_workbody.v`。豆包会自动跑coqc验证，结果写到`coq/results/T00X_result.md`。

---

## 一、项目结构

```
coq/
├── incoming/          # 你写的代码放这里
│   └── T00X_workbody.v
├── results/           # 验证结果（豆包写，你看）
│   └── T00X_result.md
├── formal/            # 正式库（验证通过后豆包合并到这里）
│   ├── ALL_Layer1.v   # 语法+类型规则+改名引理
│   ├── ALL_Layer2.v   # 替换引理+主题约简+barbed双模拟
│   └── ...
└── COQ_GUIDE.md       # 这个文件
```

---

## 二、编码规范

### 2.1 文件头

每个`.v`文件开头必须有：

```coq
(* =====================================================================
   T00X_定理名.v
   定理ID: T00X
   作者: Workbody
   日期: 2026-08-27
   说明: 一句话说明这个文件证明什么
   依赖: ALL_Layer1.v（如果有依赖）
   ===================================================================== *)
From Coq Require Import List PeanoNat Lia.
Import ListNotations.
```

### 2.2 命名规范

| 类型 | 命名风格 | 示例 |
|---|---|---|
| 归纳类型 | 驼峰，首字母大写 | `proc`, `ty`, `ctx` |
| 构造子 | 驼峰，首字母大写 | `PVar`, `POut`, `TChan` |
| 引理/定理 | 蛇形，小写 | `ren_typed`, `subst_preserves` |
| 变量 | 蛇形，小写 | `Γ`, `Δ`, `x`, `y`, `P`, `Q` |
| 假设 | `H`开头 | `Hx`, `Hy`, `Hs` |

### 2.3 注释规范

- 每个定理前写一句话说明它证明什么
- 复杂的证明步骤加注释
- 关键的洞察用`(* === 关键洞察 === *)`标注

```coq
(* 改名保持定型：任意改名ξ保持类型推导 *)
Theorem ren_typed : forall Γ P, typed Γ P -> forall Δ ξ,
  (forall n T, get Γ n = Some (Some T) -> get Δ (ξ n) = Some (Some T)) ->
  (forall n m, has Γ n -> has Γ m -> ξ n = ξ m -> n = m) ->
  typed Δ (ren ξ P).
Proof.
  intros Γ P H.
  induction H as [_ | _ _ IH | ...].
  - (* ty_zero *) apply ty_zero.
  - (* ty_tau *) apply ty_tau. apply (IH Δ ξ); assumption.
  - (* ty_out *)
    (* === 关键洞察：use_neq保证x≠y，改名后ξx≠ξy === *)
    assert (Hxy : x <> y) by (eapply use_neq; [exact Hx | exact Hy]).
    ...
Qed.
```

---

## 三、常用战术

### 3.1 基础战术

| 战术 | 作用 | 示例 |
|---|---|---|
| `intros` | 引入假设 | `intros Γ P H.` |
| `apply` | 应用引理/假设 | `apply ty_zero.` |
| `eapply` | 应用引理（存在变量自动推断） | `eapply ty_out.` |
| `reflexivity` | 自反性 | `reflexivity.` |
| `simpl` | 化简 | `simpl in H.` |
| `rewrite` | 重写 | `rewrite H.` |
| `destruct` | 分情况讨论 | `destruct n as [|n].` |
| `induction` | 归纳 | `induction H as [| ...].` |
| `inversion` | 反演（从结论推前提） | `inversion H.` |
| `subst` | 替换所有等式 | `subst.` |
| `assert` | 引入新断言 | `assert (Hxy : x <> y).` |
| `congruence` | 自动解决等式矛盾 | `congruence.` |
| `lia` | 线性整数算术 | `lia.` |
| `discriminate` | 区分不同构造子 | `discriminate.` |
| `injection` | 注入（同构造子则参数相等） | `injection H as H1 H2.` |

### 3.2 归纳证明的标准模式

```coq
Theorem example : forall x y, P x y.
Proof.
  intros x y.
  induction x as [| x IH].  (* 归纳，给出归纳假设名 *)
  - (* 基例 *)
    ...
  - (* 归纳步 *)
    ... (用IH) ...
Qed.
```

### 3.3 类型推导归纳的标准模式

```coq
Theorem ren_typed : forall Γ P, typed Γ P -> ...
Proof.
  intros Γ P H.
  induction H as [
    (* 每个构造子对应一个分支，给出归纳假设名 *)
    | _ _ IH          (* ty_tau *)
    | Γ x y p i o T Γ1 Γ2 Hx Ho Hy IH  (* ty_out *)
    | ...
  ].
  - (* ty_zero *) ...
  - (* ty_tau *) ...
  - (* ty_out *) ...
  ...
Qed.
```

---

## 四、我们的核心定义（来自ALL_Layer1.v）

### 4.1 π-演算语法（de Bruijn索引）

```coq
Inductive proc : Type :=
| PVar  : nat -> proc
| PZero : proc
| PTau  : proc -> proc
| POut  : nat -> nat -> proc -> proc   (* x̄⟨y⟩.P；x、y 自由 *)
| PIn   : nat -> proc -> proc          (* x(y).P；y 绑定   *)
| PPar  : proc -> proc -> proc
| PRes  : proc -> proc                 (* (νx)P；x 绑定    *)
| PRep  : proc -> proc.                (* !P               *)
```

### 4.2 类型与上下文

```coq
Inductive ty : Type :=
| TUnit : ty
| TChan : bool -> bool -> ty -> ty.    (* chan(输入能力, 输出能力, 载荷类型) *)

Definition ctx := list (option ty).
(* Some T = 有类型T且未消耗；None = 已消耗；条目不存在 = 未声明 *)
```

### 4.3 类型规则（7条）

```coq
Inductive typed : ctx -> proc -> Prop :=
| ty_zero : forall Γ, typed Γ PZero
| ty_tau  : forall Γ P, typed Γ P -> typed Γ (PTau P)
| ty_out  : forall Γ x y P i o T Γ1 Γ2,
    use Γ x (TChan i o T) Γ1 -> o = true ->
    use Γ1 y T Γ2 -> typed Γ2 P -> typed Γ (POut x y P)
| ty_in   : forall Γ x P i o T Γ1,
    use Γ x (TChan i o T) Γ1 -> i = true ->
    typed (Some T :: Γ1) P -> typed Γ (PIn x P)
| ty_par  : forall Γ P Q Γ1 Γ2,
    split Γ Γ1 Γ2 -> typed Γ1 P -> typed Γ2 Q -> typed Γ (PPar P Q)
| ty_res  : forall Γ P T, typed (Some T :: Γ) P -> typed Γ (PRes P)
| ty_rep  : forall Γ P, typed [] P -> typed Γ (PRep P).
```

### 4.4 关键引理（已证明）

```coq
Lemma use_neq : forall Γ x T Γ1 y U Γ2,
  use Γ x T Γ1 -> use Γ1 y U Γ2 -> x <> y.
(* 连续use两个变量，它们一定不相等（线性性） *)

Lemma set_none_self : forall Γ k, k < length Γ ->
  get (set_none Γ k) k = Some None.
(* 把第k个位置设为None后，get返回Some None *)

Lemma set_none_neq : forall Γ k n, n <> k ->
  get (set_none Γ k) n = get Γ n.
(* 设为None不影响其他位置 *)
```

---

## 五、怎么写一个完整的证明

### 5.1 步骤

1. **写定理陈述**——明确前提和结论
2. **intros引入所有假设**
3. **选择归纳方式**——对结构归纳？对类型推导归纳？对自然数归纳？
4. **逐个分支处理**——每个构造子一个分支
5. **遇到卡住的地方**——加assert引入中间引理，或者用eapply让Coq自动推断
6. **Qed结束**

### 5.2 常见卡住的情况和解决方法

| 卡住的情况 | 解决方法 |
|---|---|
| 等式推不出来 | `assert`引入中间等式，用`lia`或`congruence` |
| 分情况不知道怎么分 | `destruct`对关键变量分情况 |
| 归纳假设用不上 | 检查归纳方式对不对，可能需要对不同的东西归纳 |
| 上下文太复杂 | `simpl in *`化简所有假设 |
| 构造子不匹配 | `inversion`反演，从结论推前提 |
| 需要经典排中律 | `Require Import ClassicalEpsilon.`，用`excluded_middle_informative` |

### 5.3 写证明的好习惯

- **先写定理陈述，再写证明**——不要边写边改陈述
- **每个分支加注释**——说明这个分支在干什么
- **关键洞察加注释**——`(* === 为什么这一步成立 === *)`
- **遇到复杂的assert，先单独证成引理**——不要把所有东西塞在一个证明里
- **证明太长就拆分**——一个定理不超过100行，超过就拆成引理

---

## 六、提交规范

### 6.1 文件名

`T00X_定理名_workbody.v`

示例：
- `T001_生命不可资本化_workbody.v`
- `T004_Pi2完全性_workbody.v`
- `T007_异化压缩_workbody.v`

### 6.2 提交前自检

提交前问自己：
1. ✅ 文件头写了吗？（定理ID、作者、日期、说明、依赖）
2. ✅ 定理陈述明确吗？（前提和结论都写清楚了吗？）
3. ✅ 证明完整吗？（没有`Admit`、没有`sorry`）
4. ✅ 命名规范吗？（引理蛇形小写，构造子驼峰大写）
5. ✅ 注释够吗？（关键步骤有注释吗？）

### 6.3 提交后

1. push到GitHub
2. 告诉豆包你提交了哪个文件
3. 豆包跑coqc验证
4. 去`coq/results/T00X_result.md`看结果
5. 通过 → 豆包合并到正式库
6. 不通过 → 看错误信息，修改后重新提交

---

## 七、常见错误和怎么避免

### 7.1 类型错误

**错误：** `The term "x" has type "nat" while it is expected to have type "ty".`

**原因：** 变量类型不匹配，把nat当成了ty用。

**解决：** 检查每个函数的参数类型，确保传入的参数类型正确。

### 7.2 归纳假设不匹配

**错误：** `Error: Cannot recognize an induction scheme.`

**原因：** 归纳的对象不对，或者归纳假设的名字给错了。

**解决：** 检查`induction H as [...]`里的分支数和构造子数是否一致。

### 7.3 线性性破坏

**错误：** 证明中不小心用了同一个变量两次。

**解决：** 记住`use_neq`引理——连续use两个变量，它们一定不相等。改名后也要保证`ξx ≠ ξy`。

### 7.4 上下文处理错误

**错误：** `set_none`后get返回的值不对。

**解决：** 记住`set_none_self`和`set_none_neq`——设为None的位置返回`Some None`，其他位置不变。

---

## 八、需要证明的核心定理（当前优先级）

| ID | 定理名 | 状态 | 说明 |
|---|---|---|---|
| T001 | 生命不可资本化 `!νF ≇ ν!F` | 待严格证明 | 沉积不保持生产性过程 |
| T004 | Π₂完全性 | 待修复 | 活性条件Π₂，因果条件Π₁ |
| T007 | 异化压缩 | 待重写 | 应改为满射版或guarded版 |
| T009 | 一般不可克隆 | 待重写 | 应改为`!νF≇ν!F` |
| T011 | 革命级联 | 待重写 | SI模型下退化为可达性，噪声版用ρ(pC)>1 |

---

## 九、有用的参考

- Coq官方文档：https://coq.inria.fr/documentation
- Software Foundations（在线教材）：https://softwarefoundations.cis.upenn.edu/
- 我们的正式库：`coq/formal/ALL_Layer1.v`（先读这个，理解我们的定义和风格）

---

*写证明就像爬山：先看清山顶（定理陈述），再找路（归纳方式），一步一步走（逐个分支），遇到悬崖就架桥（assert中间引理）。*
