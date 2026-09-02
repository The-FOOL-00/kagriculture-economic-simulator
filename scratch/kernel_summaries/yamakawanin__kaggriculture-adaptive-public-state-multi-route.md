# Kernel: yamakawanin__kaggriculture-adaptive-public-state-multi-route

## Notebook: kaggriculture-adaptive-public-state-multi-route.ipynb (14 cells)

### [Markdown Cell 0]

# Kaggriculture — Adaptive Public-State Multi-Route Agent

This notebook packages the tested **Adaptive Champion V2** agent into a Kaggle-ready submission while documenting how the policy works.

## What this notebook does

1. Explains the strategy and its main adaptive mechanisms.
2. Writes the **exact tested agent source** to `main.py`.
3. Imports the generated module and performs structural sanity checks.
4. Creates `submission.tar.gz` with `main.py` at the archive root.
5. Leaves the final archive in the notebook working directory, ready to submit from Kaggle's **Output** panel.

The implementation is intentionally kept byte-for-byte equivalent to the provided Python agent instead of being "cleaned up" inside the submission path. For competition agents, a pretty refactor that changes one state reset or callable binding is a surprisingly efficient way to manufacture a mysterious validation failure.

**Source SHA-256:** `9b5e1157af3d4a643fcd818f5c290003d2672230d5ae8c0024fae0836cc894df`

---

## High-level idea

This is not a neural policy. It is a **replay-derived, rule-guarded ensemble**:

```text
                         public observation
                                |
                 +--------------+--------------+
                 |              |              |
               MOON           MUTOY          MUNIB
                 |              |              |
                 |        early-opener route   |
                 |                             |
                 +---------- meta-router ------+
                                |
                        optional market delta
                                |
                    public-regime expert gate
                                |
                           final action
                  {farmer, hands, market}
```

The agent combines several precomputed expert traces with state-dependent route selection and small corrective controllers. The important distinction is that the **macro plan is mostly replay/tape based**, while the **choice of which plan or market adjustment to use is adaptive**.


### [Markdown Cell 1]

## 1. Embedded expert policies

The top-level wrapper contains three embedded policies:

- **Moon**: the most sophisticated route-aware expert. It contains several replay-derived production layouts and additional execution guards.
- **Mutoy**: an alternative replay expert used for a very specific aggressive opening pattern.
- **Munib**: another replay expert. Two instances are created:
  - a **base** instance;
  - a **front-running** instance whose `_FR_ITEMS` are enabled for `WOOL`, `MILK`, `MELON`, and `STRAWBERRY`.

The payloads are stored as Base85 + zlib strings and loaded into isolated in-memory modules. This looks opaque in the submission file, but it has two practical advantages:

1. the agent stays single-file and self-contained;
2. the exact policy tapes and helper code cannot be accidentally altered by notebook formatting.

### What Moon does internally

Moon is itself adaptive. Its embedded source contains:

- multiple route tapes such as `10c4s_3q`, `8c6s_3q`, `6c8s_3q`, and YARN-specific variants;
- shop-based route selection;
- a legacy-layout fallback based on an observed opponent farm signature;
- weed repair;
- premium-market preemption and repayment;
- opponent market-race observation;
- terminal liquidation logic;
- feed / room safety guards;
- late tomato and egg adjustments.

So the outer wrapper is an ensemble over an expert that already contains several internal guards. Humanity discovered abstraction layers and immediately used them to hide another abstraction layer inside.


### [Markdown Cell 2]

## 2. Outer route selection

At the start of a game, all route state is reset and all embedded experts are advanced once so their internal state stays aligned.

### Early Mutoy gate

At step 1, the wrapper checks the opponent's public opening:

- `opponent_hires >= 4`
- `opponent_money <= 20`

If both conditions hold, the policy selects the **Mutoy** route.

This is an opponent-style classifier in miniature: the wrapper does not attempt to infer a hidden strategy name. It reacts to a concrete public-state signature.

### Moon vs Munib

If no Mutoy route has been locked in, the wrapper computes Moon and Munib actions in parallel.

When the two first disagree, the wrapper chooses Munib if:

- the divergence happens before step 200; or
- the first three shops are `BAKERY, BAKERY, BAKERY`; or
- the first three shops are `PET_CAFE, ICE_CREAM_SHOP, ICE_CREAM_SHOP`.

Otherwise it stays with Moon.

This is a **first-divergence router**: instead of switching experts every turn, it waits until their behavior meaningfully separates and then commits to a route.


### [Markdown Cell 3]

## 3. Market overlay instead of a full-policy switch

From step 217 onward, the wrapper can keep Moon's normal action while importing only the **market difference** between:

- Munib base; and
- Munib with front-running enabled.

The helper computes sell totals per item, takes the delta, and applies only that delta to Moon's market orders.

That means the agent can preserve Moon's farmer movement and hand actions while borrowing Munib's market timing.

Conceptually:

```text
Moon full action
    +
(Munib-front market - Munib-base market)
    =
Moon execution with Munib market timing
```

This component-level mixing is safer than replacing the entire expert whenever a market opportunity appears.


### [Markdown Cell 4]

## 4. No-hindsight YARN repair

A later patch changes Moon's route-label logic for the **second YARN_STORE** case.

The core issue is causal timing:

- the second YARN shop only becomes observable around step 144;
- the original second-YARN tape had already diverged around step 72.

Selecting that tape from the beginning would therefore use information that was not yet observable.

The repair uses the `6c8s_3q` route when a second YARN store becomes observable because that route remains prefix-aligned longer. This is an important principle for replay-derived agents:

> A route should only diverge after the public evidence needed to select it actually exists.

Without that rule, a replay policy can quietly become a hindsight oracle instead of a legitimate agent.


### [Markdown Cell 5]

## 5. Public-state expert market regime

The final wrapper maintains a small public-state regime classifier.

At **step 145**, it counts visible opponent farm contents. The expert-market regime activates when the opponent has at least:

- 10 `MELON`
- 3 `COW`

At intervention steps **145** and **504**, the wrapper compares the incumbent action with a separately stateful expert-Moon proposal.

The expert market is used only when:

1. the public regime is active;
2. farmer and hand actions agree between incumbent and expert;
3. the market actions differ;
4. at step 504, the agent itself has at least one `GOOSE`.

The agreement requirement is a useful safety constraint. It avoids combining a market order with a completely different physical execution plan.

### Important implementation note

The file also defines an intermediate wrapper that would copy the expert's **farmer** component. As written, the final public-regime controller anchors `_emr_base_agent` to the earlier base router, so that intermediate farmer-replacement wrapper is **not on the final execution path**. The final submitted policy uses the expert instance as a proposal source for the gated market interventions.

This notebook preserves that behavior exactly rather than silently "fixing" it.


### [Markdown Cell 6]

## 6. Execution guards

Replay agents fail when the world differs slightly from the replay. The embedded experts therefore include several repair layers.

A representative example is **weed repair**:

1. if a replay says `BUILD_PASTURE` or `PLANT`;
2. but the current tile is still a `WEED`;
3. the agent temporarily issues `DIG`;
4. remembers the intended action;
5. replays the following actor actions to re-align with the tape.

Other guards handle inventory reservations, market repayment after front-running, terminal liquidation, and movement / capacity constraints.

The strategy is therefore better described as:

> **precomputed macro schedule + causal route selection + online execution repair**

rather than simply "copy a replay."


### [Markdown Cell 7]

## 7. Strengths and limitations

### Strengths

- **Deterministic and cheap**: no model loading, GPU, or network access.
- **Strong long-horizon coordination**: replay tapes encode coherent production schedules.
- **Adaptive where it matters**: shop order, opponent opening, market state, and visible farm composition can alter behavior.
- **Submission-safe**: standard-library only and fully self-contained.
- **Component-level intervention**: market behavior can be modified without throwing away the whole base plan.

### Limitations

- The macro policy still depends heavily on a finite set of precomputed trajectories.
- Route classification uses hand-built thresholds and specific shop regimes.
- Some adaptive logic is highly targeted to known matchup patterns.
- The large compressed payloads make line-by-line auditing harder.
- There is an intermediate hybrid wrapper that is shadowed by the final controller, so future refactors should verify the actual call graph before changing anything.

For a public Kaggle release, the main value of this notebook is therefore not pretending the policy is a generic planner. It is showing how a strong deterministic agent can be built from **expert schedules plus carefully causal adaptation**.


### [Markdown Cell 8]

## 8. Build the exact submission agent

The next cell writes the original tested source to `main.py`.

**Do not add another Python function to `main.py` after the final `kaggle_agent` definition.**  
The supplied loader-fixed version intentionally keeps that callable last.


### [Code Cell 9]
```python
%%writefile main.py
"""V21-R1 public-state multi-route Kaggriculture agent."""

from __future__ import annotations

import base64
import copy
import types
import zlib


_MOON_PAYLOAD = 'c-rjx+0uf{x;2QNudDc6pg(9i0~EWmrB?(*P!JAO5K)l6QEach-npt)>|59eGs1&}NXaLY%+V0zzyJHc3BD;%m*^5TQG~>lri}dG|HOsmyQgM)j(zj_&nXJCbC?y`KWS9t=YJk<e*Nci4$rB3`sZApPetxV;XjwcOzrGn|Mg#+tDF7v_cQ;o&R6s9Mycullb-+mm^>{`|I^t?qu`(XarW=$|8KN^^3*(?v;XU#Fv|Zq{|#|Y|0_S6!T-trxw^J}4*$ubB0c?ekN$c;|Md^)N8#U9dOip7|2*?=NZZX!%Rk%yxZywfzsoq6@n4z2In4j{U;q8z|NUQX5JzeLk7Z`(F804yrzn2@Z`;eF@PFHZnP306{qkMwzYaLLS*%3m@IOm+Xs`bn|IZ)(<wvHSLI3XaFZ*wz!CzHb2K~RI{LAWh{(aLvL;vS*O>d)Z%R9Q}TZkn1$lu1>heQO8?-B?>dkM9|??Pa4xo0)!>I4PR{duugWT3s0ychh4nWLf{-d;gA8**=X+Bw~J5p=%#3@c~T5^L^X2kLz~ypy`hzOU<7yV>xi!=z<UmSuT|!Rt9cwB9Lk8J=li?>2v?^L;)0;jUJ-yVbL^9uW=hCxP#n^;+9{52R1}4XPeAdZC=CBTT#x#lSp=NO8KBlG_;D+eW3%i%O+t>f`!{wY$f|FBuK*b4A^Q_#`=P)uhJW=slah!kGjdv~0#N^%B`TJ!}#`4xzo7-2A@(pyHYe5>+}p<0Aw=)=?M7xyHOaPUBh9oT2=9q&0_cxTm0gt<R<{l{zxsfhmoct{$nY+tk4PP1AJnPOG7875lQWbc4CvG-8Uf8KCHfo9~hK%H6tgmuIMTRs^py#NE}SxarxhSz$Y!8xM|N1g@Zias~CDTQV2<tM5EMf|Y&5Wx!_SVy)s5*UGf<ux0XZeX0}_`%&b3_DGb+=8cKi%}!N51qZ+EHAii@$i-+IBAyio>b&w(prga5I@v6$yA}|<#;LonPcyaXM8j$`K0ae8q*m_U9G=Q)1HZpNz53*2=?3Lub$_FGjC7;OQuBS&gsW<;bHx7J?cuavY)?1JRhQkp3wQcH-UQj#-DftIY%iBMysx<OQav`}-=cr-2+vB*9b6~xYthNQotMpfqpu}JDDkLWKZf0IP-Nps<r~Vw55)dj9)8;7DK_qUCv1M2o7+d^?j!AmN#Zd5TU$UJVK{$$equgu&)4-yCm%*xx#Q2D_P8JHx1NaUHP<I@HrPOdI@d5Sd$|h_$>h-emei4Bd!YF{4hOfsW2{b@cvhJgG|Al`{yGp1Vx3iygH&urUB#i#5lXEKtg(bv;jXMabmTYR+S=*SJi0A%#k^5t(yKLDsgZt_U$R*@f2m5a^J%@-a+Pss34?0VL0<P@bH=i)5O#NDnvC^UwZS#N--WTkFe8T~3l;F)%PZ=|&#VDjm;IEA9fGm{-TGHD#A{@(l1_WHUT&`ZSVxU>^NGDj6;1463Zg;QTKE~mL83mZgWfh_ccW|=K@II)?dKxeMsEaywvQX(xO-^W%B`!u?j+53v~Mk!tKI8W9Ii08S@)RsAn(4-j2w0vo8MkIxJGA;5K8#5kRG38*U<j_m?87)f))95ayNZtI5|fB`FK%5s;@JHQ)ul5gU~9aW7O6tufD1})ap0<0XWyYO#7h6E)jp;SC)%7Rk-HfYih>@=JrRIC?7qICoDACk$S$1oU2`;-lnDB)2(&EKI8d}_)W&6e0t(rk#1e7`>S<cPqpju-1E#+S;t(9PZcM~cV`f}*#5euM|)s$x`W8f+P0y+ItcOEb#E-Gev|zXdwN$q!`%i&i6uNrBlt<Rj*UJ{xSN){udD;taE<V
```

### [Markdown Cell 10]

## 9. Structural validation

This check does not try to estimate leaderboard strength. It verifies the boring things that tend to ruin submissions:

- `main.py` imports successfully;
- `agent` exists and is callable;
- `kaggle_agent` exists and is callable;
- the expert tape contains all 720 steps;
- the final top-level callable remains `kaggle_agent`.


### [Code Cell 11]
```python

from pathlib import Path
import importlib.util

main_path = Path("main.py")
assert main_path.exists(), "main.py was not created"

spec = importlib.util.spec_from_file_location("kaggriculture_submission_main", main_path)
submission_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(submission_module)

assert callable(submission_module.agent), "main.py must expose a callable agent"
assert callable(submission_module.kaggle_agent), "loader-fixed kaggle_agent is missing"
assert len(submission_module._EXPERT_TAPE) == 720, "expert tape must contain 720 steps"

top_level_callables = [
    name
    for name, value in submission_module.__dict__.items()
    if callable(value) and not name.startswith("__")
]
assert top_level_callables[-1] == "kaggle_agent", (
    f"Expected final callable kaggle_agent, got {top_level_callables[-1]}"
)

print("Structural validation passed.")
print("Final callable:", top_level_callables[-1])
print("Expert tape length:", len(submission_module._EXPERT_TAPE))
print("main.py size:", main_path.stat().st_size, "bytes")

```

### [Markdown Cell 12]

## 10. Create `submission.tar.gz`

Kaggriculture expects `main.py` at the archive root for a packaged submission.  
The final cell creates exactly that archive and checks its contents.

After running the notebook on Kaggle:

1. **Save Version → Save & Run All**
2. open the saved notebook version;
3. go to **Output**;
4. submit `submission.tar.gz` to the Kaggriculture competition.

No Internet access is required by the agent itself.


### [Code Cell 13]
```python

from pathlib import Path
import tarfile

main_path = Path("main.py")
archive_path = Path("submission.tar.gz")

with tarfile.open(archive_path, "w:gz") as tf:
    tf.add(main_path, arcname="main.py")

with tarfile.open(archive_path, "r:gz") as tf:
    members = tf.getnames()

assert members == ["main.py"], f"Unexpected archive contents: {members}"

print(f"Ready: {archive_path.resolve()}")
print(f"Archive size: {archive_path.stat().st_size / 1024:.1f} KiB")
print("Contents:", members)

```

