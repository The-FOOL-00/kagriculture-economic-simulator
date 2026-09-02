# Kernel: yhay81__fieldbook-commit-for-three-days

## Notebook: fieldbook-commit-for-three-days.ipynb (21 cells)

### [Markdown Cell 0]
<style>
:root { --soil:#2d261f; --paper:#fbf7ed; --paper2:#fffdf7; --leaf:#285943; --leaf2:#3f7558; --sage:#9aaf9d; --gold:#d99a3d; --rust:#b75d3e; --ink:#243029; --muted:#66736a; }
.jp-Notebook { background:var(--paper); }
.jp-RenderedHTMLCommon { color:var(--ink); font-family:Inter,"Avenir Next","Segoe UI",sans-serif; line-height:1.72; }
.jp-RenderedHTMLCommon p { max-width:820px; }
.fieldbook-hero { padding:58px 58px 48px; margin:10px 0 34px; background:radial-gradient(circle at 86% 12%,rgba(242,199,125,.18),transparent 28%),linear-gradient(135deg,#1f3d30,#3f6c50); color:#fffaf0; border-radius:14px; box-shadow:0 18px 45px rgba(36,48,40,.20); overflow:hidden; }
.fieldbook-hero .eyebrow { letter-spacing:.18em; font-size:11px; font-weight:700; color:#f2c77d; }
.fieldbook-hero h1 { font-family:Georgia,"Iowan Old Style",serif; font-size:46px; line-height:1.13; margin:18px 0 14px; color:#fffdf7; }
.fieldbook-hero h1 span { color:#f2c77d; }
.fieldbook-hero p { opacity:.86; margin:0 0 28px; letter-spacing:.06em; }
.fieldbook-pills { display:flex; flex-wrap:wrap; gap:8px; }
.fieldbook-pills span { border:1px solid rgba(255,255,255,.28); background:rgba(255,255,255,.08); border-radius:999px; padding:6px 10px; font-size:10px; letter-spacing:.08em; }
.jp-RenderedHTMLCommon h2 { color:var(--leaf); border-bottom:1px solid #d4cbb9; padding-bottom:9px; margin-top:42px; font-weight:750; }
.jp-RenderedHTMLCommon h3 { color:var(--leaf2); margin-top:28px; }
.jp-RenderedHTMLCommon blockquote { border-left:4px solid var(--gold); background:var(--paper2); padding:14px 20px; border-radius:0 8px 8px 0; font-size:1.06em; }
.jp-RenderedHTMLCommon code { color:#8d4934; background:#f3eadb; border-radius:4px; padding:2px 5px; }
.jp-RenderedHTMLCommon table { font-size:13px; border-collapse:separate; border-spacing:0; }
.jp-RenderedHTMLCommon th { background:var(--leaf); color:white; }
.fieldbook-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:22px 0 28px; }
.fieldbook-card { background:var(--paper2); border:1px solid #ddd3c1; border-top:4px solid var(--gold); border-radius:9px; padding:18px; }
.fieldbook-card b { display:block; color:var(--leaf); margin-bottom:5px; }
.fieldbook-card span { color:var(--muted); font-size:13px; }
.fieldbook-figure { background:var(--paper2); border:1px solid #ddd3c1; border-radius:12px; padding:18px 18px 10px; margin:24px 0; }
.fieldbook-figure figcaption { color:var(--muted); font-size:12px; margin:5px 8px 4px; }
.fieldbook-compare { width:100%; margin:20px 0; border:1px solid #ddd3c1; border-radius:9px; overflow:hidden; }
.fieldbook-compare th,.fieldbook-compare td { padding:10px 12px; border-bottom:1px solid #e8dfcf; text-align:left; }
.fieldbook-compare tr:last-child td { border-bottom:0; }
.fieldbook-compare td:first-child { color:var(--muted); width:21%; }
.fieldbook-compare td:nth-child(3) { background:#f1f6ef; }
.fieldbook-thanks { background:#f1f6ef; border-left:4px solid var(--leaf2); border-radius:0 8px 8px 0; padding:14px 18px; margin:20px 0; }
@media (max-width:700px) { .fieldbook-hero { padding:38px 28px; } .fieldbook-hero h1 { font-size:34px; } .fieldbook-grid { grid-template-columns:1fr; } }
</style>
<div class="fieldbook-hero">
<div class="eyebrow">🌾 KAGGRICULTURE · FIELD NOTE 01</div>
<h1>Keep the plan for three days.<br><span>Reconsider when a shop opens.</span></h1>
<p>observe once · choose a chunk · ignore weak noise</p>
<div class="fieldbook-pills"><span>🏪 SHOP MILESTONES</span><span>🧩 BRANCHABLE CHUNKS</span><span>📖 READABLE AGENT</span></div>
</div>

In Kaggriculture, the strongest reason to change strategy is the **new shop added every three days**. Fieldbook chooses a plan when a shop opens, then keeps it until the next shop.

The current agent only reselects at day 6 and day 9. It does not yet repeat this process for the full season.

<div class="fieldbook-grid">
<div class="fieldbook-card"><b>🏪 Observe once</b><span>The shop set is known at the start of the window.</span></div>
<div class="fieldbook-card"><b>🧭 Commit</b><span>Run the chosen movement and production plan for three days.</span></div>
<div class="fieldbook-card"><b>📡 Ignore weak noise</b><span>Most price and opponent changes do not justify a new route.</span></div>
</div>

### [Markdown Cell 1]
## 1. Why can the plan stay fixed for three days?

At the start of each three-day window, every shop available in that window is already known. Until the next shop opens, there is little reason to abandon the basic order of moving, planting, caring, and harvesting.

Prices and the opponent still provide signals, but they are much weaker than a shop unlock. Ignoring most of that noise still leaves a strong agent. So I **choose once, then usually commit for three days**.


### [Markdown Cell 2]
## 2. The strategy in one line

> Observe the shop → choose a three-day plan → execute it → observe the next shop

Today, Fieldbook chooses an intermediate plan on day 6 and a long plan on day 9.


<figure class="fieldbook-figure"><svg viewBox="0 0 980 275" width="100%" role="img" aria-label="Fieldbook selects at day 6 and day 9, then stays fixed">
<defs><style>.fb-box{fill:#fbf7ed;stroke:#285943;stroke-width:2}.fb-t{font:600 15px sans-serif;fill:#243029}.fb-s{font:12px sans-serif;fill:#66736a}.fb-line{stroke:#9aaf9d;stroke-width:3;fill:none}.fb-mark{stroke:#d99a3d;stroke-width:3}.fb-green{fill:#285943}.fb-gold{fill:#d99a3d}</style></defs>
<path class="fb-line" d="M62 94 H918"/>
<rect class="fb-box" x="62" y="55" width="194" height="78" rx="8"/><text class="fb-t" x="159" y="84" text-anchor="middle">day 0–3</text><text class="fb-s" x="159" y="108" text-anchor="middle">shared opening</text>
<rect class="fb-box" x="256" y="55" width="194" height="78" rx="8"/><text class="fb-t" x="353" y="84" text-anchor="middle">day 3–6</text><text class="fb-s" x="353" y="108" text-anchor="middle">shop 1 · still shared</text>
<rect class="fb-green" x="450" y="55" width="194" height="78" rx="8"/><text x="547" y="84" text-anchor="middle" style="font:600 15px sans-serif;fill:white">day 6–9</text><text x="547" y="108" text-anchor="middle" style="font:12px sans-serif;fill:#e5efe8">shop 2 · choose root</text>
<rect class="fb-gold" x="644" y="55" width="274" height="78" rx="8"/><text x="781" y="84" text-anchor="middle" style="font:600 15px sans-serif;fill:#30261e">day 9–30</text><text x="781" y="108" text-anchor="middle" style="font:12px sans-serif;fill:#493722">shop 3 · choose long tail</text>
<path class="fb-mark" d="M256 38 V150 M450 38 V150 M644 38 V150"/>
<text class="fb-s" x="256" y="27" text-anchor="middle">SHOP 1</text><text class="fb-s" x="450" y="27" text-anchor="middle">SHOP 2</text><text class="fb-s" x="644" y="27" text-anchor="middle">SHOP 3</text>
<path class="fb-line" stroke-dasharray="7 6" d="M663 203 H913"/><text class="fb-t" x="663" y="194">NEXT</text><text class="fb-s" x="788" y="229" text-anchor="middle">reselect on days 12, 15, 18…</text>
<text class="fb-s" x="781" y="158" text-anchor="middle">current agent does not reselect after day 9</text>
</svg><figcaption>Current implementation: two branch points. The three-day idea is only partially implemented.</figcaption></figure>

### [Markdown Cell 3]
## 3. Start from public match tapes

Strong action sequences are difficult to create from zero, so I first use public Leaderboard histories as a candidate library.

1. Cut public episodes at shop boundaries
2. Join candidates with similar shops and economic states
3. Compare them on unused seeds and both seats

At this stage, my work is the selection, connection, trade timing, and evaluation of those candidates.

But mining public tapes cannot create new strength forever. On its own, this method will eventually fall behind.

The next asset is a **three-day chunk** that is strong by itself and ends with cash, position, and inventory that connect cleanly to the next plan. I evaluate both strength and branchability.


<figure class="fieldbook-figure"><svg viewBox="0 0 980 245" width="100%" role="img" aria-label="From public tape mining to original branchable chunk development">
<defs><marker id="fb-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#9aaf9d"/></marker></defs>
<text x="42" y="34" style="font:700 12px sans-serif;fill:#b75d3e;letter-spacing:.12em">STARTING POINT</text>
<text x="600" y="34" style="font:700 12px sans-serif;fill:#285943;letter-spacing:.12em">DURABLE ADVANTAGE</text>
<g style="font-family:sans-serif"><rect x="42" y="62" width="165" height="92" rx="10" fill="#f7eadc" stroke="#b75d3e"/><text x="124" y="98" text-anchor="middle" font-size="25">📼</text><text x="124" y="126" text-anchor="middle" font-size="14" fill="#243029">Public episodes</text>
<rect x="260" y="62" width="165" height="92" rx="10" fill="#fffdf7" stroke="#d99a3d"/><text x="342" y="98" text-anchor="middle" font-size="25">✂️</text><text x="342" y="126" text-anchor="middle" font-size="14" fill="#243029">Cut at shops</text>
<rect x="478" y="62" width="165" height="92" rx="10" fill="#fffdf7" stroke="#9aaf9d"/><text x="560" y="98" text-anchor="middle" font-size="25">🧪</text><text x="560" y="126" text-anchor="middle" font-size="14" fill="#243029">Mutate & test</text>
<rect x="696" y="62" width="218" height="92" rx="10" fill="#eaf2e9" stroke="#285943" stroke-width="2"/><text x="805" y="98" text-anchor="middle" font-size="25">🧩</text><text x="805" y="124" text-anchor="middle" font-size="14" fill="#243029">Strong, clean endpoint</text><text x="805" y="143" text-anchor="middle" font-size="11" fill="#66736a">cash · position · inventory</text></g>
<path d="M207 108 H252 M425 108 H470 M643 108 H688" stroke="#9aaf9d" stroke-width="3" marker-end="url(#fb-arrow)"/>
<path d="M805 166 C805 220 560 220 560 166" fill="none" stroke="#285943" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#fb-arrow)"/><text x="682" y="219" text-anchor="middle" style="font:12px sans-serif;fill:#66736a">improve one chunk at a time</text>
</svg><figcaption>Public histories teach the shape. Search and endpoint quality create the next advantage.</figcaption></figure>

### [Markdown Cell 4]
### 🗂️ Six route candidates

Fieldbook selects from this small library on day 6 and day 9.

### [Markdown Cell 6]
## 4. What Fieldbook does today

The 719 actions are split into three parts.

- day 0–6: one shared opening
- day 6–9: an intermediate plan chosen from the first two shops, cash gap, and land gap
- day 9–30: a long tail chosen from the third shop and the day-6 state

The agent does not reselect after day 9, even when more shops open. Its only smaller adaptations are the day-6 economic gaps, a safe one-step SELL lead, and final liquidation.

Movement and production can stay fixed while trade time and quantity react to price or the opponent. The current SELL lead is the smallest example.

Long actions live in `fieldbook_tapes.py`; branching lives in `fieldbook_logic.py`.


### [Markdown Cell 7]
### 🧱 Separate logic from the tape

The cell below contains the branches. Long actions stay in `fieldbook_tapes.py`.

### [Code Cell 8]
```python
%%writefile fieldbook_logic.py
# SPDX-License-Identifier: Apache-2.0
"""ShopForge Fieldbook: six readable plans and a small public-state tree.

Generated from the public ShopForge episodes listed in ROUTE_SOURCES.
There is no compressed action blob and no exact-money lookup table.
"""

from __future__ import annotations

import copy

ITEMS = ('WHEAT',
 'CARROT',
 'TOMATO',
 'STRAWBERRY',
 'MELON',
 'EGG',
 'MILK',
 'WOOL',
 'FERTILIZER',
 'GOOSE',
 'COW',
 'SHEEP')
PRODUCTS = ITEMS[:9]
ROUTE_SOURCES = {0: {'action_sha256': '3319bb4e555847149dd5c82d3626a697056455d120fca487de52e1d5f4a9bfd4',
     'episode_id': 103823935,
     'label': 'BALANCED'},
 2: {'action_sha256': '39be02a28445bcd831735e8234903f1ccc1f5f2951ec66989bb9dcd0ea7e5df3',
     'episode_id': 104056237,
     'label': 'CASH_RECOVERY'},
 3: {'action_sha256': '94ef053e8ec78494c3df5d4e77a38e5e1d4306f263fbe8bf89ce6d4aab1572fe',
     'episode_id': 103609700,
     'label': 'YARN_ENGINE'},
 14: {'action_sha256': '45edb4cacfc0b74a450222454b0de14559399e3ae10267ea22035a50b2523729',
      'episode_id': 103576156,
      'label': 'YARN_LATE'},
 16: {'action_sha256': 'ec38433bc7080fca2139d2e2cae735f2c4a3c23c145a8e60c6762a41ff4ffab0',
      'episode_id': 103926612,
      'label': 'LAND_RECOVERY'},
 18: {'action_sha256': '355effb1b7a24b0fe98715e5b86b30e6cd19ff2312922f6c3ba845dd11f598bf',
      'episode_id': 103908697,
      'label': 'WHEAT_RECOVERY'}}
ROUTE_NAMES = {index: row["label"] for index, row in ROUTE_SOURCES.items()}

DEFAULT_SETTINGS = {
    "branch_depth": 2,
    "sell_lead": True,
    "terminal_liquidation": True,
    "severe_cash_gap": -199.0,
    "very_severe_cash_gap": -721.5,
    "wheat_cheap": 29.5,
    "low_cash": 242.5,
}

# One line is: step | farmer, hands... | market orders.
# The first unit is the farmer. Remaining units are farm hands.
from fieldbook_tapes import PLAN_SCRIPTS

# <FIELD_BOOK_PLAN_SCRIPTS>


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(k
```

### [Code Cell 9]
```python
import hashlib
from pathlib import Path

tape_candidates = [
    Path("fieldbook_tapes.py"),
    Path("/kaggle/input/shopforge-fieldbook-tapes/fieldbook_tapes.py"),
]
tape_path = next((path for path in tape_candidates if path.exists()), None)
expected_tape_sha256 = "114224c60244d2d905078ecaea409b3116994861f474e9717ddcd456a9f062f0"
assert tape_path is not None, "Add the private Fieldbook tape Dataset as a Notebook input"
assert hashlib.sha256(tape_path.read_bytes()).hexdigest() == expected_tape_sha256
tape_lines = tape_path.read_text(encoding="utf-8").splitlines()
print(f"separate tape: {len(tape_lines):,} lines / {tape_path.stat().st_size:,} bytes")
print("edit fieldbook_tapes.py to change individual planned actions")

```

### [Code Cell 10]
```python
import hashlib
import importlib.util
from pathlib import Path

TAPE_BEGIN = "# === BEGIN FIELD BOOK PLAN SCRIPTS ==="
TAPE_END = "# === END FIELD BOOK PLAN SCRIPTS ==="
TAPE_PLACEHOLDER = "from fieldbook_tapes import PLAN_SCRIPTS\n\n# <FIELD_BOOK_PLAN_SCRIPTS>"

logic_source = Path("fieldbook_logic.py").read_text(encoding="utf-8")
tape_source = tape_path.read_text(encoding="utf-8")
tape_begin = tape_source.index(TAPE_BEGIN) + len(TAPE_BEGIN) + 1
tape_end = tape_source.index("\n" + TAPE_END, tape_begin)
tape_block = tape_source[tape_begin:tape_end]
assert logic_source.count(TAPE_PLACEHOLDER) == 1
assembled_source = logic_source.replace(TAPE_PLACEHOLDER, tape_block)
Path("fieldbook_agent.py").write_text(assembled_source, encoding="utf-8")
Path("main.py").write_text(assembled_source, encoding="utf-8")

spec = importlib.util.spec_from_file_location("fieldbook_agent", "fieldbook_agent.py")
fieldbook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fieldbook)
artifact_sha256 = hashlib.sha256(Path("fieldbook_agent.py").read_bytes()).hexdigest()
submission_sha256 = hashlib.sha256(Path("main.py").read_bytes()).hexdigest()
assert submission_sha256 == artifact_sha256
print("agent SHA-256:", artifact_sha256)
print("main.py SHA-256:", submission_sha256)
print("routes:", {index: fieldbook.ROUTE_NAMES[index] for index in fieldbook.ROUTES})
assert len(fieldbook.ROUTES) == 6
assert all(len(route) == 719 for route in fieldbook.ROUTES.values())

tape_structure = pd.DataFrame([
    ("OPENING", "day 0–6", 144, "shared by all routes"),
    ("ROOT", "day 6–9", 72, "selected on day 6"),
    ("TAIL", "day 9–30", 503, "selected on day 9, then fixed"),
], columns=["segment", "period", "steps", "selection"])
display(fieldbook_table(tape_structure))

```

### [Markdown Cell 11]
## 5. Only two branch points

At day 6, the agent reads the first two shops plus cash and land gaps. At day 9, it reads the third shop. It chooses among six routes without using the seed, seat, opponent ID, or future shops.


### [Code Cell 12]
```python
strategy_rules = pd.DataFrame([
    (6, 144, "first shop is Yarn", "YARN_ENGINE"),
    (6, 144, "second shop is Yarn; land gap < 0", "LAND_RECOVERY"),
    (6, 144, "otherwise", "BALANCED"),
    (9, 216, "BALANCED; cash gap < 0", "CASH_RECOVERY"),
    (9, 216, "third shop is Yarn", "YARN_LATE"),
    (9, 216, "land recovery; wheat is cheap", "WHEAT_RECOVERY"),
], columns=["day", "step", "visible condition", "plan"])
display(fieldbook_table(strategy_rules))

```

### [Markdown Cell 13]
## 6. Simplicity keeps most of the strength

Across 27,520 games on 64 unused seeds, 215 opponents, and both seats, Fieldbook won 26,295 and lost 1,225 for a 0.95549 point rate. LossGuard scored 0.95883.

This does not guarantee Leaderboard performance, but two branches retained most of the strength on the frozen pool. The four games below are an execution check, not performance evidence.


<figure class="fieldbook-figure"><svg viewBox="0 0 980 245" width="100%" role="img" aria-label="Frozen pool point rate comparison">
<text x="42" y="34" style="font:700 12px sans-serif;fill:#66736a;letter-spacing:.1em">FROZEN POOL · 27,520 GAMES PER AGENT · BOTH SEATS</text>
<text x="42" y="82" style="font:600 15px sans-serif;fill:#243029">Fieldbook</text><rect x="172" y="62" width="760" height="28" rx="7" fill="#eadfcd"/><rect x="172" y="62" width="726.2" height="28" rx="7" fill="#285943"/><text x="888.2" y="82" text-anchor="end" style="font:700 14px sans-serif;fill:white">95.55%</text>
<text x="42" y="139" style="font:600 15px sans-serif;fill:#243029">LossGuard</text><rect x="172" y="119" width="760" height="28" rx="7" fill="#eadfcd"/><rect x="172" y="119" width="728.7" height="28" rx="7" fill="#d99a3d"/><text x="890.7" y="139" text-anchor="end" style="font:700 14px sans-serif;fill:#30261e">95.88%</text>
<line x1="172" y1="174" x2="932" y2="174" stroke="#d4cbb9"/><text x="42" y="204" style="font:700 22px Georgia,serif;fill:#285943">−0.33 pp</text><text x="172" y="201" style="font:13px sans-serif;fill:#66736a">for a six-route readable policy</text>
</svg><figcaption>Recorded local evidence, not a Leaderboard guarantee. Fieldbook gives up 0.334 percentage points here.</figcaption></figure>

### [Markdown Cell 14]
### 🧪 Execution check

Run only four games on the same seeds and both seats. This is not performance evidence.

### [Code Cell 15]
```python
from importlib.metadata import version
from kaggle_environments import make

def play_pair(seed, fieldbook_seat):
    fixed = fieldbook.make_agent(branch_depth=0, sell_lead=False, terminal_liquidation=False)
    adaptive = fieldbook.make_agent(branch_depth=2, sell_lead=True, terminal_liquidation=True)
    agents = [adaptive, fixed] if fieldbook_seat == 0 else [fixed, adaptive]
    env = make("kaggriculture", configuration={"episodeSteps":720, "seed":seed}, debug=False)
    env.run(agents)
    rewards = [float(state.reward) for state in env.state]
    fieldbook_reward, fixed_reward = rewards[fieldbook_seat], rewards[1 - fieldbook_seat]
    point = 1.0 if fieldbook_reward > fixed_reward else 0.5 if fieldbook_reward == fixed_reward else 0.0
    return {"seed":seed, "seat":fieldbook_seat, "point":point, "margin":fieldbook_reward-fixed_reward}

required_engine = "1.32.7"
installed_engine = version("kaggle-environments")
if installed_engine != required_engine:
    print(
        f"SKIPPED: this image has kaggle-environments {installed_engine}; "
        f"the recorded comparison requires {required_engine}."
    )
else:
    demo_seeds = [390700001, 390700002]
    demo_rows = [play_pair(seed, seat) for seed in demo_seeds for seat in (0, 1)]
    demo = pd.DataFrame(demo_rows)
    display(demo)
    summary = {"games":len(demo), "point_rate":demo.point.mean(), "mean_margin":demo.margin.mean()}
    print(summary)

```

### [Markdown Cell 16]
## 7. Next: stronger, cleaner chunks

The next version extends selection to days 12, 15, 18, and beyond. Chunk quality comes before branch count.

- Search for strong three-day chunks
- Score the ending state and keep chunks that connect cleanly
- Adapt only trade timing and quantity to price or the opponent
- Replace one window at a time and test on unused seeds and both seats

Daily generation and step-by-step search can come later. Public tapes are a teacher, not the final asset.


<table class="fieldbook-compare"><thead><tr><th></th><th>Current Fieldbook</th><th>Next Fieldbook</th></tr></thead><tbody>
<tr><td>Branch points</td><td>day 6 and day 9</td><td>every shop milestone</td></tr>
<tr><td>Plan unit</td><td>six long tapes</td><td>three-day chunks</td></tr>
<tr><td>Inside a chunk</td><td>one-step SELL lead</td><td>adaptive trade time and quantity</td></tr>
<tr><td>Source of strength</td><td>public tape mining</td><td>generate, mutate, and evaluate</td></tr>
</tbody></table>

### [Code Cell 17]
```python
# Change one thing at a time, then compare on unused seeds.
experiments = {
    "fixed": fieldbook.make_agent(branch_depth=0, sell_lead=False, terminal_liquidation=False),
    "root_only": fieldbook.make_agent(branch_depth=1, sell_lead=False, terminal_liquidation=True),
    "full": fieldbook.make_agent(),
    "wheat_cheap_32": fieldbook.make_agent(wheat_cheap=32.0),
}
milestones = pd.DataFrame([
    (3, "observe shop 1", "continue the shared opening"),
    (6, "observe shop 2", "choose an intermediate plan"),
    (9, "observe shop 3", "choose the long tail"),
    (12, "shop 4 and beyond", "no reselection yet; next target"),
], columns=["day", "shop milestone", "current behavior"])
display(fieldbook_table(milestones))
print("change one rule, then evaluate on unused seeds:", list(experiments))

```

### [Markdown Cell 18]
## 8. Credit and release boundary

The starting point is Milan Leonard's public episode `102248386`. I also used public histories from Milan Leonard, Kenjo1209, and Shuwen (Shawn) Ge. Episode IDs and hashes are recorded in `source_manifest.json`.

I thank these authors for making strong public histories available.

Handwritten code is Apache License 2.0. The Notebook builds `main.py`, but release and competition submission are separate audited actions outside the runtime.


<div class="fieldbook-thanks">🙏 <b>Thank you</b> to Milan Leonard, Kenjo1209, and Shuwen (Shawn) Ge for publishing the histories that made this study possible.</div>

### [Code Cell 19]
```python
# Only this exact file is a submission candidate. Do not submit here.
from importlib.metadata import version
print("kaggle-environments:", version("kaggle-environments"))
print("submission candidate: main.py")
print("submission SHA-256:", artifact_sha256)
print("KAGGLE NOTEBOOK: yhay81/fieldbook-commit-for-three-days")
print("RELEASE ACTIONS: OUTSIDE THIS NOTEBOOK")

```

### [Markdown Cell 20]
## Summary

**Choose when a shop opens. Usually keep the plan for three days. Next, build my own strong and branchable chunks.**


