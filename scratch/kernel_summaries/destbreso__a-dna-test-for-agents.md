# Kernel: destbreso__a-dna-test-for-agents

## Notebook: a-dna-test-for-agents.ipynb (30 cells)

### [Markdown Cell 0]
Two replay streams sit in front of you. Maybe they are the same agent on different days. Maybe one is a mutant of the other, or both descend from something a third team published weeks ago, or one carries an adaptive layer that rewrites half its turns and hides the resemblance. On this leaderboard the question is not academic: [the field plays one opening](https://www.kaggle.com/code/destbreso/everyone-is-playing-the-same-opening), [clades sweep the board and go extinct in days](https://www.kaggle.com/code/destbreso/the-leaderboard-has-a-fossil-record), and [the top is populated by mutants of shared stock](https://www.kaggle.com/code/destbreso/mutants-at-the-top-genetic-potential-of-a-replay). Almost everything is related to almost everything, and yet there has been no instrument that answers the three questions attribution actually needs: **are these two streams kin, where exactly did they split, and can I still tell after one of them starts adapting?**

The tools that exist fail in complementary ways. A full-stream similarity compares 719 turns against 719, costs quadratic work, returns one number, and reads adaptive noise as difference, so the most interesting agents, the live ones, look unrelated to their own base. The opening signature I used in the fossil-record notebook is one locus: it says "same family" or not, and nothing more, no ordering of splits, no dating, no tree.

This notebook, on engine **1.32.7**, derives the missing instrument from the replays themselves: a thirty-band signature that behaves like a genome, cheap to compute, deterministic where it matches, robust to adaptation that spares the anchor window (and legible, as a liveness reading, where adaptation reaches it), and validated against 160 real teams before any claim rests on it. The chain of reasoning is kept in the order it happened, because each step forced the next, and it ends with something none of the earlier instruments could draw: a dated family tree of the board. The raw material is the corpus from [the top-two dissection](https://www.kaggle.com/code/destbreso/dissecting-the-top-two) plus a fresh 175-game field sample, and the data behind every figure travels inside the notebook.

### [Markdown Cell 2]
## 1. The observation that started it

Below is the X-ray of the top two: one panel per corpus and seat, one **row per real episode**, green where the episode matches its corpus mode at that turn, amber where only the market channel differs, navy where the plan itself differs. Two of the twelve panels are shown here for the shape; the full set is in the dissection notebook.

Looking at these, a question asks itself: regularly spaced green bands run through even the darkest late game. Divergence does not spread to the bell as one front. It lives in blocks.

### [Markdown Cell 4]
## 2. What the stripes are

Folding every divergence matrix by hour of day locates the band: the anchor is **hour 1**, not hour 0. Hour 0 is the decision hour, the daily sells, the feed purchases, the hire block, and those differ between episodes. By hour 1 the engine has reset every unit to its spawn, dissolved yesterday's hands and rehired, and every episode executes the day-script's first move from the same configuration.

Divergence is sticky inside a day, about 0.95 turn to turn, and only about 0.61 of it survives the night. The night is a damper, not a barrier, because farm state carries over even though positions do not. **The day is the module**: these agents are thirty day-programs chained through a narrow synchronisation bottleneck.

### [Code Cell 5]
```python
hours = (np.arange(1, 719) % 24)
fold = np.zeros(24); cnt = np.zeros(24)
for g in G:
    for seat in ("0", "1"):
        s = g["seats"].get(seat) or {}
        if s.get("thin") or "plan_rows_hex" not in s:
            continue
        div = (unpack(s["plan_rows_hex"]) |
               unpack(s["market_rows_hex"])).astype(bool)
        for h in range(24):
            sel = div[:, hours == h]
            fold[h] += sel.sum(); cnt[h] += sel.size
rate = fold / np.maximum(1, cnt)
fig, ax = plt.subplots(figsize=(10, 2.8))
ax.bar(range(24), rate,
       color=["#2E7D32" if h in (1, 2, 3, 4) else "#0F172A" for h in range(24)])
ax.set_xticks(range(24)); ax.set_xlabel("hour of the in-game day")
ax.set_ylabel("share diverging")
ax.set_title("hours 1-4, in green, are the conserved window", fontsize=9)
plt.tight_layout(); plt.show()
```

### [Markdown Cell 6]
## 3. The leap: hash the conserved window and you have a genome

If hours 1 to 4 of every day are where an agent is most itself, then hashing the plan channel over that window, farmer, hands, structural and provisioning orders, never the sells and never the quantities, gives **one signature per day: thirty bands**. I call it the day barcode, and the biological framing is not decoration, it is the mechanics:

* each day is a **locus**, and the hash at that locus is the allele;
* a band that matches between two streams is **deterministic shared identity** at that day;
* the fraction of matching bands is a graded relatedness;
* and the **first band that differs dates the mutation**: the day a variant forked from its ancestor. One clarification, because the genetic metaphor invites a misreading: this date is an **in-game day, a position in the 30-day season**, not a calendar date. Forking at day 20 means the two plans agree for days 0-19 and part ways from day 20 onward *inside every episode either of them plays*; it says nothing about when the variant was written. And it is the first *observable* divergence, a lower bound: two lineages can re-agree on later loci (the gels below show the full match pattern, not just the first break), and an edit that never touches the anchor window surfaces only on the day it finally reaches it.

The hash is a **semantic key**. It is content-addressed identity for the part of the behaviour that survives resynchronisation, which is exactly the base plan. An agent that puts an adaptive algorithmic layer on top of a known base still collides with that base on the loci the layer does not touch, and diverges precisely where it does. That is what makes it possible to match adaptive agents to a shared base corpus: the adaptation moves the weather, the barcode reads the climate.

Hashing the whole barcode once more gives each sample an **accession number**, an eight-character genome id. It is the searchable form of the identity: figures below carry it beside every label, reports print it for both samples, and looking a stream up in any dataset of barcodes is one string match on the id, or one match per band when the question is partial kinship rather than identity.

Efficiency follows from the construction: thirty hashes against a full order-preserving alignment of 719-step streams. Comparing two agents is thirty string equalities. Comparing a new stream against a library of ancestors is a set lookup per band.

### [Code Cell 7]
```python
# the gel: each corpus consensus barcode as thirty coloured bands
def band_color(h):
    v = int(h[:6], 16)
    return plt.cm.tab20((v % 20) / 20)

import hashlib
def genome_id(bands):
    """The accession number: eight characters of the whole-barcode hash,
    the searchable key for a sample in any dataset of barcodes."""
    return hashlib.sha1("".join(bands).encode()).hexdigest()[:8]

labels = list(DNA["consensus_barcodes"])
fig, ax = plt.subplots(figsize=(11, 0.42 * len(labels) + 1.4))
for y, k in enumerate(labels):
    for d, band in enumerate(DNA["consensus_barcodes"][k]):
        ax.add_patch(plt.Rectangle((d, y), 0.92, 0.8,
                                   color=band_color(band)))
ax.set_xlim(0, 30); ax.set_ylim(0, len(labels))
ax.set_yticks(np.arange(len(labels)) + 0.4)
ax.set_yticklabels([f"{k}  ·  {genome_id(DNA['consensus_barcodes'][k])}"
                    for k in labels], fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("in-game day (locus)")
ax.set_title("the gel: same colour in a column = same allele at that locus",
             fontsize=9)
plt.tight_layout(); plt.show()
```

### [Markdown Cell 8]
## 4. Reading the gel

The relatedness matrix below counts matching bands of thirty for every pair, with the forking day beside it. What it recovers, with no tuning:

* The public build's cow-herd routes are one tight clade: two of them share **all thirty** bands (their herd difference lives at hour 0, outside the window), the third forks at day 11, and the yarn variants fork at days 3 to 8, when yarn shops appear.
* **Utkarsh #2's stream is a descendant of the public legacy layout**: 22 of 30 bands, forking at day 20. A rank-2 agent, and the barcode names its ancestor and dates the split.
* The two current leaders sit at 12 to 20 bands from the public routes, relatives with heavy late mutation, and Tschinkel is measurably closer to the public backbone than カワシギ.
* **One earlier top stream, Mohamed abdelrazik's, matches nothing at all: zero bands against every column.** A separate lineage, one of the few openings outside the monoculture that the census measured.

And the barcode's failure mode is itself a measurement. Within-agent band agreement is 0.72 for Tschinkel but only ~0.37 for カワシギ: the deepest adaptive layer on the board reaches even the anchor hours. **Band agreement per day is a per-day liveness profile**: scripts identify strongly, deep adaptives identify weakly, and the weakness tells you which kind of agent you are looking at.

### [Code Cell 9]
```python
# the liveness profile: per-day self-agreement of each corpus, the
# instrument's validity range drawn as a curve
def day_agreement(episodes):
    out = []
    for d in range(30):
        c = {}
        for bc in episodes:
            c[bc[d]] = c.get(bc[d], 0) + 1
        out.append(max(c.values()) / len(episodes))
    return out

fig, ax = plt.subplots(figsize=(9.5, 3.4))
E = DNA["episode_barcodes"]
for label, key, color in (("tschinkel (12 games)", "tschinkel A", "#0F172A"),
                          ("kawashigi (12 games)", "kawashigi KING", "#B45309")):
    ys = day_agreement(E[key])
    ax.plot(range(30), ys, color=color, lw=2, label=label)
    ax.annotate(label.split(" ")[0], (29, ys[-1]), xytext=(5, 0),
                textcoords="offset points", color=color, fontsize=9,
                va="center")
ax.axhline(0.6, color="#C62828", lw=1, ls="--")
ax.annotate("below this line the kinship test refuses to rule",
            (0.5, 0.575), fontsize=8, color="#C62828", va="top")
ax.set_xlim(0, 33); ax.set_ylim(0, 1.05)
ax.set_xlabel("in-game day (locus)")
ax.set_ylabel("fraction of games on the modal band")
ax.grid(alpha=0.25)
ax.legend(loc="lower left", fontsize=9, frameon=False)
ax.set_title("the liveness profile: where in the season each agent stops "
             "being a script", fontsize=10)
plt.tight_layout(); plt.show()
```

### [Code Cell 10]
```python
labels = list(DNA["consensus_barcodes"])
n = len(labels)
M = np.zeros((n, n), dtype=int)
for i, a in enumerate(labels):
    for j, b in enumerate(labels):
        M[i, j] = sum(x == y for x, y in zip(DNA["consensus_barcodes"][a],
                                             DNA["consensus_barcodes"][b]))
fig, ax = plt.subplots(figsize=(9.5, 7.5))
im = ax.imshow(M, cmap="Greens", vmin=0, vmax=30)
ax.set_xticks(range(n)); ax.set_xticklabels(labels, rotation=90, fontsize=7)
ax.set_yticks(range(n)); ax.set_yticklabels(labels, fontsize=7)
for i in range(n):
    for j in range(n):
        ax.text(j, i, M[i, j], ha="center", va="center", fontsize=6,
                color="white" if M[i, j] > 15 else "#0F172A")
ax.set_title("matching bands of 30", fontsize=9)
plt.colorbar(im, shrink=0.7)
plt.tight_layout(); plt.show()
```

### [Markdown Cell 11]
## 5. The family tree, which nothing before this could draw

Every earlier instrument in this series gave either a pairwise similarity, one number between two streams, or a clade marker at a single locus, the turn-24 opening. Neither can produce a genealogy: similarity does not say who split from whom, and one locus cannot order the splits. Thirty dated loci can. Agglomerative clustering on shared bands, with each join annotated by the day the joined branches stop agreeing, yields a **dated phylogeny**: not just who is related to whom, but the in-game day at which every lineage went its own way. One scope note: this is a similarity tree with each join annotated by the earliest fork observed among its member pairs; it orders splits, it does not claim who descended from whom.

Reading it: the cow-herd routes of the public build form the core clade, splitting internally at day 11; the yarn variants leave at days 3 to 8, exactly when yarn shops appear; Utkarsh #2 hangs off the legacy branch with its day-20 mutation; the two current leaders join the tree as heavy late mutants of the same stock; and one earlier top stream stands alone, sharing no band with anything, a lineage of its own.

### [Markdown Cell 13]
## 6. Could two unrelated agents collide by chance? The engine says no

The claim that a band match means ancestry needs its false-positive rate, and the engine supplies the argument: the anchor actions depend on the farm state the plan has accumulated, money, crops, herd, tiles, so differences INSIDE the plan channel compound and desynchronise, while a difference confined to hour 0 can leave the window untouched, which is why two herd routes above share all thirty bands: an identical barcode certifies an identical anchor plan, not an identical agent. Hashing four hours of the plan channel leaves essentially no room for coincidence. Measured on a fresh 175-stream field sample, 160 distinct real teams:

* streams of the **same team** match at a median of **0.93** (15 within-team pairs; a property of this field's overwhelmingly scripted population, not of all agents, as the liveness profile above shows);
* consensus barcodes of **different teams** match at a median of **0.00**, **not one of 12,720 cross-team pairs shares two or more bands**, and a locus-independence model built from these same allele frequencies would predict 4.81 shared bands per pair on average, so independence OVERSTATES chance matching in this population by a factor of thirty and the match probabilities quoted below are conservative. Three quarters of all 12,720 cross-team pairs match **zero** bands;
* every day offers 26 to 44 distinct alleles across the field, with the most common one, the public backbone's, covering 20 to 33 % of teams.

The cross-team pairs that do match heavily are not noise, they are the monoculture finding its relatives: shared ancestry is the only realistic way onto the same band.

### [Code Cell 14]
```python
w = VAL["within_pairs"]; c = VAL["cross_pairs"]
fig, axes = plt.subplots(1, 2, figsize=(11, 3))
axes[0].hist(c, bins=31, color="#0F172A")
axes[0].axvline(np.median(w), color="#B45309", lw=2,
                label=f"same-team median {np.median(w):.2f}")
axes[0].set_xlabel("fraction of matching bands, cross-team pairs")
axes[0].set_ylabel("pairs"); axes[0].legend(fontsize=8)
axes[0].set_title(f"{len(c):,} cross-team pairs: 75 % match zero bands",
                  fontsize=9)
days = sorted(int(k) for k in VAL["cardinality_by_day"])
axes[1].bar(days, [VAL["cardinality_by_day"][str(d)] for d in days],
            color="#2E7D32")
axes[1].set_xlabel("in-game day"); axes[1].set_ylabel("distinct alleles")
axes[1].set_title(f"locus cardinality across {VAL['teams']} teams", fontsize=9)
plt.tight_layout(); plt.show()
```

### [Markdown Cell 15]
## 7. What it is for, and what it is not for

Applications that follow directly:

1. **Ancestry attribution**: match any stream against a library of known barcodes, per band, in constant time per locus.
2. **Divergence dating**: the first differing band localises the first OBSERVABLE divergence, a lower bound on the true edit day, which turns "these two are 74 % similar" into "these two separated at in-game day 20".
3. **Matching adaptive agents to a base corpus**: an algorithmic layer over a known base collides with the base on untouched loci, so the base is identifiable even under heavy adaptation, as the two current leaders demonstrate.
4. **A per-day liveness profile**: within-agent band agreement by day says where in the season an agent stops being a script.
5. **A dated family tree**: clustering on shared bands with fork-day annotations turns the board into a phylogeny, which no single-locus or global-similarity instrument could draw.
6. **Field monitoring**: the fossil-record notebook tracked clades with opening signatures, which are one locus; thirty loci make the strata legible day by day.

What it is not: a strength measure. The barcode reads identity, not quality, and the deepest adaptive layer on the board is precisely the one it reads most weakly. That weakness is the diagnostic, not a flaw to fix.

Everything here computes from the embedded data, and the corpora are public replays anyone can pull.

### [Markdown Cell 16]
## 8. The test itself, formal and checkable

A DNA test has a protocol: two samples in, a kinship verdict out, and a **probability that the overlap happened by chance**. The chance arithmetic here is the same one forensic genetics uses. Every locus has a population of alleles with measured frequencies, the tables built from 160 real teams in section 6, so the probability that two INDEPENDENT agents share exactly the bands these two samples share is the product of the population frequencies of those shared alleles. Sharing the backbone's common allele is weak evidence, one locus at a time; sharing rare alleles multiplies into astronomical odds fast.

This is also why a naive tail against "pairs of different teams" would mislead: that population is full of true relatives, the monoculture, so real kinship levels look common in it. The random-match probability sidesteps the contamination because commonness is priced per allele.

`dna_test(a, b)` below returns the report: bands matched, the random-match probability computed under locus independence (conservative here, per the validation above), the verdict, and for relatives the first observable divergence. Five real cases follow, as printed reports and as gels, so the eye learns what each verdict looks like. The last two land on the hardest sample on the board and show the test's built-in asymmetry: instability can only DESTROY matches, never fake them, so thirteen shared bands convict at any stability, while a clean NOT-RELATED needs a sample stable enough to be someone, and on one that is not, the test refuses to rule.

### [Markdown Cell 18]
The same five reports as gels: two lanes per case, one band per locus, the green tick where the lanes agree and the red cross where they part. This is the picture a single report deserves.

### [Code Cell 19]
```python
fig, axes = plt.subplots(len(results), 1, figsize=(11, 2.1 * len(results)))
for ax, (title, bc_a, bc_b, r) in zip(np.atleast_1d(axes), results):
    for row, bc in ((1.35, bc_a), (0.0, bc_b)):
        for d, band in enumerate(bc):
            ax.add_patch(plt.Rectangle((d, row), 0.92, 0.8,
                                       color=band_color(band)))
    for d, ok in enumerate(r["match_vector"]):
        ax.text(d + 0.46, 1.08, "|" if ok else "x",
                ha="center", va="center", fontsize=8,
                color="#2E7D32" if ok else "#C62828",
                fontweight="bold")
    ax.set_xlim(0, 30); ax.set_ylim(-0.3, 2.5)
    ax.set_yticks([]); ax.set_xticks(range(0, 31, 5))
    ax.set_title(f"{title}: {r['matched']}/30 bands, {r['verdict']}"
                 + (f", forks day {r['fork_day']}"
                    if r['verdict'] == 'RELATED' else ""),
                 fontsize=9, loc="left")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
axes[-1].set_xlabel("locus (in-game day); green bar = band match, red x = mismatch")
plt.tight_layout(); plt.show()
```

### [Markdown Cell 20]
And one map for all of them together. Every test lands at a point: how many bands matched, and how much those bands weigh. The shaded bands are the verdict zones, the red dashed line is the empirical bar no unrelated pair ever crossed, and the teal wedge is the range of evidence a given number of bands can carry, from the field's most common allele to its rarest. Reports say the verdict; this says how far it sits from the nearest boundary. The map also carries an observation the raw reports only whisper: the two RELATED pairs sit at almost the same evidence, 17.2 against 16.8, though one matched 22 bands and the other 13. Utkarsh shares the popular backbone, its median matched allele lives in about 25 of 160 teams and weighs 0.78 per band; kawashigi's thirteen live in about 5 of 160 and weigh 1.29 each. Rarer alleles, heavier bands: the test weighs evidence, it does not count it.

### [Markdown Cell 22]
## Try it on a submission

Fork this notebook, change one number, and read how a submission stands: its games pulled from the companion dataset, its genome and accession id, its stability, and its nearest relatives on the board. The default id is the current rank 1; `consensus.csv` lists the fourteen submissions available, across four capture days.

### [Code Cell 23]
```python
SUBMISSION_ID = 55540317        # <- change me (see consensus.csv for options)

rows = []
with (DATA / "barcodes.csv").open() as f:
    for r in csv.DictReader(f):
        if int(r["submission"]) == SUBMISSION_ID:
            rows.append(r)
assert rows, f"{SUBMISSION_ID} not in the dataset; consensus.csv lists the 14 available"
eps = [r["dna_bands"].split("-") for r in rows]
team = rows[0]["team"]
cons = []
for d in range(30):
    c = {}
    for bc in eps:
        c[bc[d]] = c.get(bc[d], 0) + 1
    cons.append(max(c, key=c.get))
stab = stability(eps)
print(f"{team}  (submission {SUBMISSION_ID})")
print(f"  games in dataset      {len(eps)}")
print(f"  genome accession      {genome_id(cons)}")
print(f"  self-agreement        {stab:.2f}"
      + ("   (adaptive: negative verdicts will be refused)" if stab < 0.6 else ""))
scored = sorted(((sum(x == y for x, y in zip(cons, bc)), label)
                 for label, bc in consensus_barcodes.items()), reverse=True)
print("  nearest references:")
for k, label in scored[:3]:
    print(f"    {label:<30} {k}/30 bands")
best_label = scored[0][1]
print()
_ = dna_test(cons, consensus_barcodes[best_label], team, best_label,
             stability_a=stab)
```

### [Markdown Cell 24]
## The dataset behind every number

Every barcode above loads from the companion dataset, [kaggriculture-replay-genomes](https://www.kaggle.com/datasets/destbreso/kaggriculture-replay-genomes): the ladder's top across four capture days, raw both-seat streams with recorded seeds (every matchup re-simulable), and one genome row per episode-seat. Its advantage is that nothing here needs my code, my crawler, or the engine: the identity work is precomputed once and the queries are column operations. Three key families do the work:

* **`dna_bands`**, the identity key: fixed-width and day-ordered, so kinship IS a shared prefix, and the file ships sorted by it, so every begins-with query is a contiguous range;
* **`lineage_d5` / `lineage_d10` / `lineage_d20`**, prefix hashes: the class 'agreeing on every locus through day k' as a plain equality join;
* **`sem_bands`**, the semantic key ([construction][provisioning][units] per day): exact partial matches at semantic boundaries, for lookup only, its collision rates are not the tabulated ones.

Three queries the notebook has not shown yet, each one line of pandas:

### [Code Cell 25]
```python
import pandas as pd
bc = pd.read_csv(DATA / "barcodes.csv")
cons = pd.read_csv(DATA / "consensus.csv")

# 1) the monoculture, quantified by a GROUP BY: how much of the elite
#    agrees on every locus through day 10
cls = cons.groupby("lineage_d10").size().sort_values(ascending=False)
print(f"submissions: {len(cons)}   largest day-10 class: "
      f"{cls.iloc[0]} submissions share {cls.index[0]}")

# 2) the same team across calendar days: lineage persistence
multi = cons[cons.team.isin(cons.team.value_counts()[lambda s: s > 1].index)]
print("\none team, several capture days:")
for team, g in multi.groupby("team"):
    tag = "  ".join(f"{r.capture_batch}:{r.genome_id}(sa {r.self_agreement:.2f})"
                    for r in g.itertuples())
    print(f"  {team[:24]:<24} {tag}")

# 3) a prefix range: everyone matching the public legacy route through day 20
legacy = pd.read_csv(DATA / "reference_barcodes.csv")
pref = "-".join(legacy[legacy.label == "route:LEGACY_10C4S_3Q"]
                .dna_bands.iloc[0].split("-")[:20])
family = bc[bc.dna_bands.str.startswith(pref)]
print(f"\nepisode rows sharing the legacy route's first 20 loci: "
      f"{len(family)} across {family.team.nunique()} teams: "
      f"{sorted(family.team.unique())[:6]}")
```

### [Code Cell 26]
```python
# the board, drawn from the same two columns
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.2),
                               gridspec_kw={"width_ratios": [1, 1.5]})

# lineage-class structure: how concentrated is the elite's ancestry?
sizes = cons.groupby("lineage_d10").size().sort_values(ascending=False)
top = sizes.head(8)
ax1.bar(range(len(top)), top.values, color="#0E7490")
ax1.bar(len(top), sizes.iloc[8:].sum(), color="#94A3B8")
ax1.set_xticks(list(range(len(top))) + [len(top)])
ax1.set_xticklabels([i[:6] for i in top.index] + ["rest"],
                    rotation=45, ha="right", fontsize=8)
for i, v in enumerate(top.values):
    ax1.annotate(str(v), (i, v), ha="center", va="bottom", fontsize=9)
ax1.set_ylabel("submissions in the class")
ax1.set_title("day-10 lineage classes: the monoculture,\nquantified",
              fontsize=10)
ax1.grid(alpha=0.2, axis="y")

# the board map: how alive each agent is vs how common its lineage is
csize = cons.lineage_d10.map(sizes)
ax2.scatter(cons.self_agreement, csize, s=55, alpha=0.75, color="#0F172A")
NAME = {"カワシギ": "#B45309", "Thomas Tschinkel": "#0E7490",
        "Kostiantyn Isaienkov": "#166534"}
for team, col in NAME.items():
    g = cons[cons.team == team]
    ax2.scatter(g.self_agreement, g.lineage_d10.map(sizes), s=90,
                color=col, label=team, zorder=3)
ax2.axvline(0.6, color="#C62828", lw=1, ls="--")
ax2.annotate("kinship test refuses\nnegative verdicts", (0.585, 20),
             fontsize=8, color="#C62828", ha="right")
ax2.set_xlabel("self-agreement (script 1.0, alive 0.0)")
ax2.set_ylabel("size of its day-10 lineage class")
ax2.set_title("every submission on the two axes this notebook reads:\n"
              "cached solutions crowd the top right, live solvers stand alone",
              fontsize=10)
ax2.legend(loc="upper left", fontsize=8, frameon=False)
ax2.grid(alpha=0.2)
plt.tight_layout(); plt.show()
```

### [Markdown Cell 27]
## 8. Error rates, stated the way forensics states them

A test is not finished until its error rates are, and the two kinds need
different treatment here.

**The false-match rate ($\alpha$) is boundable without assuming any
distribution.** At the RELATED threshold (two or more matched bands), zero of
the 12,720 unrelated team pairs would be declared related, and the rule of
three (Hanley and Lippman-Hand 1983) turns that zero into a 95 % upper bound of $2.4\times10^{-4}$ per
comparison. Pairs sharing a team are not independent, so the cell below also
prints the most conservative reading, 80 fully independent pairs, and the
bound survives it. What would NOT be honest is a parametric $\alpha$: the
locus-independence model assigns probability 0.965 to two random teams
sharing two bands, the same model the validation already refuted by a factor
of thirty, so the empirical bound is primary and the per-report match
probability plays the role forensic statistics assigns it, case evidence,
not a test-level error rate, the distinction the DNA-evidence literature
settled in the 1990s (National Research Council 1996; Evett and Weir 1998).

**The miss rate ($\beta$) is not one number and pretending otherwise would
be the dishonesty.** It is two curves. Against fork depth it is analytic
from the allele tables: a fork at in-game day 2 or later carries enough
evidence to convict, day 1 reaches only WEAK SIGNAL, and day 0 is invisible
by construction, two lineages that part before the first anchor share no
plan to match. Against instability it is measured, on corpora whose ground
truth is known because every pair is the same agent: the stable leader
misses 0 %, the deep adaptive 11-14 %, and the refusal guard converts part
of that region from silent error into explicit OUT OF RANGE. The blind spots
have shapes, and both are stated.

### [Markdown Cell 29]
## 9. The summary

The chain, end to end: an X-ray of the top two showed green stripes nobody had studied; folding by hour located the conserved window, hours 1 to 4, where the engine's nightly reset makes every agent most itself; hashing that window per day produced a thirty-locus genome; and the genome turned out to carry everything attribution needs. Deterministic identity where bands match. A dated fork where they stop. A family tree the board never had. A per-day liveness profile that says where in the season an agent stops being a script, a test that refuses to rule on samples too unstable to identify, and error rates stated on both sides: a distribution-free false-match bound of 2.4e-4, and a miss rate given as the two curves it really is. And a formal kinship test whose chance probability is computed the way forensics computes it, from measured allele frequencies, so that its three verdicts on real samples read IDENTICAL at 10^-51.6, RELATED at 10^-17.2 with the split dated to day 20, and UNRELATED at 1.0.

The validations are the part I would defend first: same-team streams agree at a median of 0.93 while different-team barcodes agree at a median of 0.00, three quarters of 12,720 cross-team pairs share nothing, and the engine explains why, since the anchor actions feed on accumulated farm state that separates any two histories. In this population, collision is ancestry: not one of 12,720 unrelated pairs shares more than a single band. The accession id makes every sample addressable, one string to find a genome, and the companion dataset [kaggriculture-replay-genomes](https://www.kaggle.com/datasets/destbreso/kaggriculture-replay-genomes) carries every barcode behind this notebook as rows you can look up by that id, fourteen submissions across four capture days, mirrors included in a dataset.

Where this goes next is the series' standing question asked properly: run the test across the whole board, day after leaderboard day, and the fossil record stops being strata read from one locus and becomes a genealogy with dates on every branch. New submissions can be placed on the tree the day they appear. And the agents the test reads weakly, the deep adaptives, are exactly the ones worth watching, because on this board being hard to identify is what being alive looks like.

Two hardenings would carry the test from validated-on-this-field to validated-in-general: synthetic genealogies with known edit days, to prove the divergence dating end to end, and allele frequencies built on a population disjoint from the one being tested. Both are mechanical; neither changes the instrument's shape.

*References. For the error-rate framing: National Research Council (1996), The Evaluation of Forensic DNA Evidence; Evett, I. W., Weir, B. S. (1998), Interpreting DNA Evidence, Sinauer. For the statistics of the bounds: Hanley, J. A., Lippman-Hand, A. (1983), If nothing goes wrong, is everything all right? Interpreting zero numerators, JAMA 249, 1743-1745; Clopper, C. J., Pearson, E. S. (1934), The use of confidence or fiducial limits illustrated in the case of the binomial, Biometrika 26, 404-413.*

