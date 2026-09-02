# Kernel: georgymamarin__kaggriculture-daily-replays-the-live-meta-report

## Notebook: kaggriculture-daily-replays-the-live-meta-report.ipynb (37 cells)

### [Markdown Cell 0]
# Kaggriculture Daily Replays: The Live Meta Report

*By [Georgy Mamarin](https://www.kaggle.com/georgymamarin)*

Every finished game on the [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)
ladder leaves a full public replay: 720 turns, both players, every observation and every action.
I collect them into the
[Kaggriculture Episodes](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes)
dataset, and this notebook is the live look inside: what the data holds today, and what the
leading farms measurably do differently.

### [Markdown Cell 2]
**A live report, not a snapshot.** It re-runs on a schedule with the dataset, so every number in
the text below is computed at run time. Come back tomorrow and the ladder you see will be the
ladder as it is tomorrow.

<div class="alert alert-info" style="border-left: 5px solid #2196f3; padding: 12px 16px; border-radius: 4px;">
<b>Two companions, two jobs.</b> This one is about the data and the state of the ladder. My guide
<a href="https://www.kaggle.com/code/georgymamarin/kaggriculture-visualized-what-every-crop-pays">Kaggriculture, Visualized</a>
is about the game itself, with every rule and price curve drawn out plus a starter bot. Read that
one first if the mechanics are new to you.
</div>

**Built on this data, by the community:** a [replayable benchmark](https://www.kaggle.com/datasets/destbreso/kaggriculture-benchmark-matchups) of 45k matchups with resolved seeds (CC0), an [agent-testing harness](https://www.kaggle.com/code/destbreso/kaggriculture-measure-your-agent), a [no-OOM replay reader](https://www.kaggle.com/code/lucashmateo/kaggriculture-replays-no-oom-3-dataframes), and a [research series on openings, lineages and noise](https://www.kaggle.com/code/destbreso/everyone-is-playing-the-same-opening) — by destbreso and Lucas Mateo. The dataset stopped being a solo project; this page stays its daily pulse.

### In this notebook

**Part I — the data.** Know what you are standing on before you quote it.
- [1. What is in the dataset today](#s1) — size, coverage, and how fast the corpus grows

**Part II — the ladder.** Nine views of the same 30-day season, from every recorded win down to pure luck.
- [2. The ladder right now](#s2) — every recorded win on one chart
- [3. The shape of a big game](#s3) — top coin curves against a median game
- [4. Strategy fingerprints](#s4) — crew, land and crops: leaders vs the mid-ladder
- [5. What separates a big bank from a small one](#s5) — measured across every replayed game
- [6. The market they create together](#s6) — every episode's price swings, then one game up close
- [7. How fast the bar is moving](#s7) — the meta clock, and who moved this week
- [8. Who beats whom](#s8) — head-to-head win rates the ratings hide
- [9. How much of this is luck](#s9) — same bot, different games
- [10. The openings they share](#s10) — byte-identical lines, measured by stream hashes

**Part III — make it yours.**
- [11. Your submission against the ladder](#s11) — a personal report; edit one line

Plus [the honest caveats](#s12) behind every chart, and the [takeaways](#s13).

**Want this for your own bot?** Fork, put your submission id in one line of
[section 11](#s11), and you get your own report: where your best game lands in the whole field,
and how your strategy compares with the record holder's.

### [Markdown Cell 3]
# Part I — the data

### [Markdown Cell 4]
<a id="s1"></a>
## 1. What is in the dataset today

Before the strategy talk, the shape of the data itself: how much of the ladder is captured, how
deep the replay coverage goes, and how fast the corpus grows. Column-level docs live on the
[dataset page](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes).

### [Code Cell 6]
```python
# Copy-paste loaders — the three safe ways into this dataset, smallest first.
# (1) Most questions never need the replays: episode_features.csv is one row
#     per seat with the behavior already parsed out.
# (2) One game out of the multi-GB corpus, without loading the rest. The glob
#     matches both layouts: the single replays.parquet and the monthly shards
#     (replays_2026-08.parquet, ...) that replace it.
demo_id = int(ladder_r.episode_id.iloc[-1])
demo_row = pads.dataset(sorted(glob.glob(f"{BASE}/replays*.parquet"))).scanner(
    filter=pads.field("episode_id") == demo_id,
    columns=["replay_json"], batch_size=1).head(1)
demo = json.loads(demo_row.column("replay_json")[0].as_py())
print(f"episode {demo_id}: {len(demo['steps'])} steps, "
      f"{len(demo_row.column('replay_json')[0].as_py()) / 1e6:.0f} MB of JSON, "
      f"loaded alone in a fraction of a second")
del demo, demo_row; gc.collect()
# (3) A whole month as a plain DataFrame, once the monthly shards land:
#     pd.read_parquet(f"{BASE}/replays_2026-08.parquet")
```

### [Markdown Cell 7]
# Part II — the ladder

### [Markdown Cell 8]
<a id="s2"></a>
## 2. The ladder right now

Winners' final banks across the recorded ladder games, one dot per episode. The spread is the
story of this competition: the same board and the same rules produce farms that differ by an
order of magnitude.

### [Code Cell 9]
```python
fig, ax = plt.subplots(figsize=(8.2, 3.6))
ax.scatter(ladder.end, ladder.winner_bank, s=22, alpha=.55, color=C_ACC, edgecolors="white", lw=.4)
rec = ladder.loc[ladder.winner_bank.idxmax()]
ax.annotate(f"record: {fmt(rec.winner_bank)}", xy=(rec.end, rec.winner_bank),
            xytext=(10, 6), textcoords="offset points", fontsize=10, weight="bold", color=C_TOP)
ax.set_yscale("log")
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1000:g}k" if v >= 1000 else f"{v:g}")
ax.set_ylabel("winner's final bank (log)"); ax.set_xlabel("episode end time (UTC)")
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %d\n%H:%M"))
ax.tick_params(axis="x", labelsize=8.5)
ax.set_title(f"Same rules, {ladder.winner_bank.max() / ladder.winner_bank.median():.0f}x spread "
             "between median and record")
plt.tight_layout(); plt.show()

q = ladder.winner_bank.quantile([.25, .5, .9])
display(Markdown(
    f"The winner's bank across recorded games: **{fmt(q[.25])}** at p25, **{fmt(q[.5])}** median, "
    f"**{fmt(q[.9])}** at p90. The record of **{fmt(rec.winner_bank)}** is "
    f"**{rec.winner_bank / q[.5]:.1f}×** the median win; section 6 tracks how fast that gap moves."))
```

### [Markdown Cell 10]
<a id="s3"></a>
## 3. The shape of a big game

Coin curves of the biggest wins on record against a median game. Top games share a silhouette:
the bank stays near zero deep into the season while everything is reinvested, then compounding
takes over once the farm is built.

### [Markdown Cell 12]
<a id="s4"></a>
## 4. Strategy fingerprints

Replays store actions, not just scores, so you can compare bots by what they do. Those
fingerprints already sit in `episode_features.csv`, one row per seat for every episode that has
a replay, and section 1 prints how deep that coverage runs, so you rarely need to open a replay
yourself. The cell below is the method behind the crew, land and crop columns; bank shape and
prices get measured in sections 3 and 6. It stays open on purpose: it defines exactly what
`peak_crew` or `first_land_day` mean, and it is where to start if you want to measure something
I did not. Leaders against the middle of the ladder:

### [Code Cell 13]
```python
def fingerprint(episode_id, seat):
    # Hires are read from the farm state (hires_today), not from submitted HIRE
    # orders — bots keep sending orders the engine rejects once money runs short.
    crops, first_land, peak_crew, hires_by_day = {}, None, 0, {}
    for t, step in enumerate(load_replay(episode_id)["steps"]):
        farm = step[0]["observation"]["farms"][seat]
        day = t // 24
        hires_by_day[day] = max(hires_by_day.get(day, 0), farm["hires_today"])
        peak_crew = max(peak_crew, len(farm["hands"]))
        a = step[seat].get("action") or {}
        for order in (a.get("market") or []):
            if isinstance(order, list) and order and order[0] == "BUY_LAND" and first_land is None:
                first_land = day
        for unit in [a.get("farmer") or []] + list(a.get("hands") or []):
            if isinstance(unit, list) and unit and unit[0] == "PLANT" and len(unit) > 1:
                crops[unit[1]] = crops.get(unit[1], 0) + 1
    return {"hires / day": sum(hires_by_day.values()) / max(1, len(hires_by_day)),  # CSV: total_hires
            "peak crew": peak_crew,
            "first land (day)": first_land, "plants": crops}
```

### [Markdown Cell 15]
<a id="s5"></a>
## 5. What actually separates a big bank from a small one

The fingerprints above describe single games. With `episode_features.csv` we can ask the blunter
question across every replayed episode at once: which measurable choices track a large final
bank, and which ones only feel important?

One column is deliberately missing from this chart. `elbow_day` correlates with the bank at 0.8,
but it is derived from the bank itself (the day a farm crosses a tenth of its own final total),
so a weak farm crosses its small tenth early and a strong one crosses late. That is arithmetic,
not strategy, and including it would be the most confident wrong claim in this notebook.

### [Markdown Cell 17]
<a id="s6"></a>
## 6. The market they create together

Prices are shared between the two players of an episode, and `episode_features.csv` records
every episode's low and high for all nine goods. First the whole corpus, so you can see which
markets actually move; then one game up close, where you can watch them being moved.

### [Code Cell 19]
```python
rec_r = ladder_r.loc[ladder_r.winner_bank.idxmax()]
replay = load_replay(rec_r.episode_id)
prices = {p: [s[0]["observation"]["market"]["prices"][p] for s in replay["steps"]]
          for p in ("MELON", "WHEAT")}
base_price = {p: prices[p][0] for p in prices}

fig, ax = plt.subplots(figsize=(8.2, 3.4))
for p, c in (("MELON", C_TOP), ("WHEAT", C_MID)):
    ax.plot(prices[p], lw=2.2, color=c, label=f"{p.title()} price")
    ax.axhline(base_price[p], color=c, lw=.9, ls=":")
ax.set_xlabel("turn"); ax.set_ylabel("market price")
ax.set_title(f"Prices inside the biggest replayed game (episode {rec_r.episode_id})")
ax.legend(fontsize=9.5, frameon=False); plt.tight_layout(); plt.show()

mel, whe = prices["MELON"], prices["WHEAT"]
wheat_note = (" Wheat climbing that far above base usually means animal farms buying feed faster "
              "than the town supplies it." if max(whe) > base_price["WHEAT"] * 1.4 else "")
display(Markdown(
    f"In this game melon starts at **{base_price['MELON']}**, bottoms at **{min(mel)}** and peaks "
    f"at **{max(mel)}**, a swing of {(max(mel) - min(mel)) / base_price['MELON']:.0%} of its base "
    f"price. Wheat runs **{min(whe)}–{max(whe)}** against a base of **{base_price['WHEAT']}**."
    f"{wheat_note} Both lines are a strategy log: you can see when a farm dumps and when it "
    f"trickles."))
```

### [Markdown Cell 21]
<a id="s7"></a>
## 7. How fast the bar is moving

The number every competitor wants: how much the ladder improves while you sleep. Median
winning bank per time slice, against the record so far. Skip a few days and this is the gap you
come back to. Below the clock: the movers, teams whose rating travelled furthest over the last
seven days of recorded games.

### [Markdown Cell 24]
<a id="s8"></a>
## 8. Who beats whom

Ratings compress everything into one number, and that hides the interesting part: matchups don't
have to be transitive. Head-to-head win rates between the busiest teams; read a row as the row
team's share of wins against the column team.

### [Markdown Cell 26]
<a id="s9"></a>
## 9. How much of this is luck

Same bot, different games: how wide is its spread? This decides how many submissions you need
before believing a result, and whether that one great game was skill or a lucky matchup.
A useful floor for reading the chart: in
[destbreso's weed-spawn ablation](https://www.kaggle.com/code/destbreso/kaggriculture-the-free-experiment-you-already-ran)
the environment alone moves a bank by a few hundred coins, while the spreads below run in the
tens of thousands. Nearly everything you see here is matchup, not dice.

### [Markdown Cell 28]
<a id="s10"></a>
## 10. The openings they share

Two seats with the same stream hash at turn N played byte-identical actions for N straight
turns: a shared opening is an observation, not a similarity threshold. Two honest limits, both
measured by destbreso: nothing observable differs before turn 48, so early agreement is partly
the engine's determinism rather than evidence of copying, and the full-game hash identifies the
episode rather than the agent, so lineage lives in the prefixes, never in `stream_h719` alone.
The hashes ship in the dataset's `stream_hashes.csv`, proposed by
[destbreso in the dataset discussion](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes/discussion/734833).
This section computes itself only when stream-hash coverage clears its 95% gate: on a partial,
time-ordered slice these rates would measure the nightly hash backfill, not the meta.

### [Markdown Cell 30]
# Part III — make it yours

### [Markdown Cell 31]
<a id="s11"></a>
## 11. Your submission against the ladder

The part worth forking. Put your own submission id in the cell below and you get a personal
report: where your best game lands in the whole field, and how your strategy fingerprint
compares with the record holder's. Find your id in `episodes.csv`, or leave the default to see
the record holder's own report.

Before spending a real submission slot, dry-run the agent: destbreso's
[benchmark](https://www.kaggle.com/datasets/destbreso/kaggriculture-benchmark-matchups) replays
45k recorded pairings seed for seed, and his
[Measure Your Agent](https://www.kaggle.com/code/destbreso/kaggriculture-measure-your-agent)
harness tells you what a local score can and cannot promise about the ladder.

### [Code Cell 32]
```python
SUBMISSION_ID = int(top_subs.index[0])   # TWEAK THIS: your submission id from episodes.csv
```

### [Markdown Cell 35]
<a id="s12"></a>
## Before you quote these numbers

The honest edges of this snapshot, so the charts above don't overclaim:

- Fingerprints read one best game per submission: a sketch of a strategy at its peak, not its
  average behavior.
- The corpus is a crawl, not a census. Episodes are discovered through pairings, so a brand-new
  submission can lag behind the ladder by a few hours; section 1 prints the exact replay
  coverage.
- Head-to-head cells stand on a handful of games. The count is printed inside every cell; a 100%
  built on two games is an anecdote, not a verdict.
- Spread estimates use submissions with four or more games each, a modest per-bot sample even
  on a mature ladder; treat them as order-of-magnitude.
- Daily time series mix real change with crawler drift: which submissions the crawl services
  shifts over time, so day-over-day movement partly reflects the lens, not the ladder
  (destbreso measures the split with a fixed panel of teams).
- The two banks of one episode share its market and weather and correlate at +0.73, so
  cross-episode comparisons of raw banks carry shared-world variance; within-episode margins
  are the cleaner ruler ([measured here](https://www.kaggle.com/code/destbreso/kaggriculture-what-kind-of-game-is-this)).
- A submission's consecutive games are serially correlated (matchmaking chains opponents), so
  win-rate confidence intervals built on "n independent games" are narrower than the truth;
  [Know Your Noise](https://www.kaggle.com/code/destbreso/kaggriculture-know-your-noise)
  measures by how much.
- Validation (self-play) episodes are excluded from every strength comparison; section 1 shows
  their share of the raw data.

