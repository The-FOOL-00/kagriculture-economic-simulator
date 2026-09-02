# Kernel: lynnsakurai__farming-score-v3-replay-revised

## Notebook: farming-score-v3-replay-revised.ipynb (8 cells)

### [Markdown Cell 0]
# What Do We Learn From the Past Replays?




### [Markdown Cell 1]
## 1. Complete programme with guarded execution

Let $R(t)$ be the full programme action at turn $t$, and let $G$ be the visible-state guard network. The executed policy is

$$
\pi_t = G\!\left(x_t,R(t)\right).
$$

The guards align the live hand count, repair weeds, project same-turn shed operations, cap sales by executable inventory, order contested sales, and fund purchases sequentially. A failed precondition suppresses only the infeasible part and falls back to the programme elsewhere.


### [Markdown Cell 2]
## 2. Conserved livestock substitution

At registered pasture-compatible purchase nodes, dairy and wool pressure are

$$
\begin{aligned}
P_{\mathrm{wool}}
    &=2N_{\mathrm{Yarn}}+\frac{p_{\mathrm{wool}}}{200},\\
P_{\mathrm{dairy}}
    &=N_{\mathrm{Pizza}}+N_{\mathrm{IceCream}}
      +N_{\mathrm{Smoothie}}+\frac{p_{\mathrm{milk}}}{160}.
\end{aligned}
$$

If the pressure gap crosses its guard, a complete cow or sheep transaction bundle is relabelled. The transformation preserves

$$
\begin{aligned}
\text{pasture geometry}' &= \text{pasture geometry},\\
\text{animal count}' &= \text{animal count},\\
\text{service route}' &= \text{service route}.
\end{aligned}
$$

Animal-product sale slots are then assigned to the executable item with the greater exact marginal revenue.


### [Markdown Cell 3]
## 3. Guarded latent-pasture activation

At the verified checkpoint, an extra animal-hand bundle is activated only when the target is an empty serviced pasture and all visible feasibility conditions hold:

$$
\mathcal{F}
=\mathcal{F}_{\mathrm{geometry}}
\cap\mathcal{F}_{\mathrm{inventory}}
\cap\mathcal{F}_{\mathrm{capacity}}
\cap\mathcal{F}_{\mathrm{cash}}.
$$

The new hand follows a fixed pickup, movement, and placement transaction. Any mismatch cancels the intervention and returns control to the parent programme.


### [Markdown Cell 4]
## 4. Exact terminal frontier

Let $T=718$ be the final executable turn. For remaining quantity $q_i$ of product $i$ and current market inventory $I_i$, its executable terminal revenue is

$$
V_i(q_i;I_i)
=\sum_{k=0}^{q_i-1}p_i(I_i+k).
$$

The engine guarantees $p_i(I)\ge1$. Since inventory has no continuation value after $T$,

$$
q_i>0 \quad\Longrightarrow\quad V_i(q_i;I_i)>0.
$$

Therefore final liquidation weakly dominates retention. The frontier first expands an existing sell order for the same product, which costs no additional slot. If only $K$ new order slots remain, products without an existing slot are selected by

$$
\underset{S}{\operatorname{maximize}}
\quad\sum_{i\in S}V_i(q_i;I_i)
\qquad\text{subject to}\qquad |S|\le K.
$$

Because every selected product consumes one slot and revenues are separable, choosing the $K$ largest values is exact.


### [Code Cell 6]
```python
# Extract into an isolated folder and import the packaged entry point.
import importlib.util
import sys

PACKAGE_DIR = Path.cwd() / "generated_submission"
PACKAGE_DIR.mkdir(exist_ok=True)
with tarfile.open(ARCHIVE_PATH, "r:gz") as package:
    package.extractall(PACKAGE_DIR)

sys.path.insert(0, str(PACKAGE_DIR))
spec = importlib.util.spec_from_file_location(
    "generated_submission_main", PACKAGE_DIR / "main.py"
)
submission = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = submission
spec.loader.exec_module(submission)
assert callable(submission.kaggriculture_agent)
print("standalone package import: OK")

```

### [Markdown Cell 7]
## Attribution

The complete programme priors are the attributed CC0 public traces from Kenjo1209, episode 102192548 seat 1, and NIklitaCheporev, episode 101408728 seat 1. The supplied guard, demand-alignment, and latent-pasture network is preserved byte-for-byte; the added contribution is the complete terminal frontier described above.


