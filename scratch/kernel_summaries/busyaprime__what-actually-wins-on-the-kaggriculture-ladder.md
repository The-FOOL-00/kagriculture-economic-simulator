# Kernel: busyaprime__what-actually-wins-on-the-kaggriculture-ladder

## Notebook: what-actually-wins-on-the-kaggriculture-ladder.ipynb (22 cells)

### [Markdown Cell 0]
# What actually wins on the Kaggriculture ladder, read from the replays

Most reads on this competition explain the crop economics or hand you a baseline agent. This one recomputes
the meta in front of you from the raw episode replays, so every number below comes from parsing the actual
720 turn games, not from the game manual. Each episode is one ranked match between two submitted agents. From
its replay I read what each side actually did, tag each side by its agent name, and read the winner from the
final profit. Aggregate a day of ladder games and you get the real question answered: not which crop pays
most on paper, but what the farms that actually win do differently from the farms that lose.

Fork it, point it at another day, and it recomputes. Every archetype, win rate, and strategy number is
parsed live from the logs, with no pasted figures and no leaderboard claim.

**What changed since the last run of this notebook.** The ladder is no longer climbing. Through the first
part of the season the daily median score rose steeply, and this notebook said the target keeps moving. It
has since peaked and turned down, and the gap between the top agent and the median has compressed several
times over. Section 4 fits both phases and prints the slope, the p value and the confidence interval, so the
turn is visible rather than asserted. That changes what the rest of this notebook is for: copying the current
meta now buys much less than it did, and the archetype tables below are more useful for finding what the
converged field is NOT doing than for imitating what it is.

### [Markdown Cell 3]
## 0. The ladder at a glance

One picture first: the agents with the strongest win rates on this day, sampled from the replays. The rest
of the notebook takes this apart, one falsifiable question per figure, every number recomputed live.

### [Code Cell 4]
```python
def wilson(w, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = w/n; d = 1 + z*z/n; c = (p + z*z/(2*n))/d; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return p, c-h, c+h
MIN_G = 1 if games < 50 else max(6, len(sides)//200)
FEAT = ["plant", "sell", "hire", "harvest", "fert", "buy_animal", "buy_land"]
_gg = sides.groupby("agent"); _hr = []
for a, sub in _gg:
    n = len(sub)
    if n < MIN_G: continue
    p, lo, hi = wilson(int(sub.win.sum()), n); _hr.append((a, p, n))
H = pd.DataFrame(_hr, columns=["agent", "winrate", "games"]).sort_values("winrate").tail(12)
if len(H):
    fig, ax = plt.subplots(figsize=(9, max(3.2, 0.42*len(H))))
    ax.hlines(range(len(H)), 50, H.winrate*100, color=MUT, lw=2)
    ax.plot(H.winrate*100, range(len(H)), "o", color=ACC, ms=9)
    ax.axvline(50, color=INK, lw=1, ls="--")
    ax.set_yticks(range(len(H)), [f"{a[:24]} (n={n})" for a, n in zip(H.agent, H.games)], fontsize=8)
    ax.set_xlabel("win rate (%)")
    ax.set_title(f"Kaggriculture ladder at a glance, {DAY}", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()
else:
    print("too few games in this sample for the at-a-glance view (renders on the full daily dump)")
```

### [Markdown Cell 5]
## 1. The agent tier list

Every game has two sides, each an agent. Here is each agent's win rate across all its games, with a Wilson
interval so you can see which leads are real and which are small sample noise. This is the ladder as the
replays actually played out, not the public leaderboard rating.

### [Code Cell 6]
```python
def wilson(w, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = w / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return p, c-h, c+h
g = sides.groupby("agent")
rec = []
for a, sub in g:
    w, n = int(sub["win"].sum()), len(sub)
    p, lo, hi = wilson(w, n)
    rec.append(dict(agent=a, games=n, winrate=p, lo=lo, hi=hi, avg_score=sub["score"].mean()))
T = pd.DataFrame(rec)
T = T[T["games"] >= max(8, T["games"].quantile(0.5))].sort_values("winrate")
fig, ax = plt.subplots(figsize=(9, max(4, 0.42*len(T))))
ax.errorbar(T["winrate"]*100, range(len(T)), xerr=[(T.winrate-T.lo)*100, (T.hi-T.winrate)*100],
            fmt="o", color=INK, ecolor=MUT, capsize=3)
ax.axvline(50, color=ACC, lw=1, ls="--")
ax.set_yticks(range(len(T)), [f"{a[:24]} (n={n})" for a, n in zip(T.agent, T.games)], fontsize=8)
ax.set_xlabel("win rate (%)  with 95% Wilson interval")
ax.set_title(f"Kaggriculture agent tier list, {DAY}", color=INK, loc="left", fontweight="bold")
plt.tight_layout(); plt.show()
print(T.sort_values("winrate", ascending=False).round(3).to_string(index=False))
```

### [Markdown Cell 7]
## 2. Do winners just do more? Mostly not

For every side we counted the real moves: how much it planted, sold on the market, hired farm hands, bought
animals and land, and collected fertilizer over the season, then averaged the winning side against the
losing side of the same games. The honest result is the interesting one. The counts almost match: winners
and losers plant, sell, hire, harvest and fertilise about equally, and the winners actually plant slightly
less. So on this day the edge is not raw activity. Both sides stay busy for the full 720 turns; what
separates them is what they plant and how efficiently they run it, which the next two sections get at. Read
these bars as description, not proof that any one action causes the win.

### [Code Cell 8]
```python
feat = ["plant", "sell", "hire", "harvest", "fert", "buy_animal", "buy_land"]
win_mean = sides[sides.win == 1][feat].mean()
los_mean = sides[sides.win == 0][feat].mean()
fig, ax = plt.subplots(figsize=(9, 4.8))
x = np.arange(len(feat)); w = 0.4
ax.bar(x - w/2, win_mean.values, w, label="winning side", color=ACC)
ax.bar(x + w/2, los_mean.values, w, label="losing side", color=MUT)
ax.set_xticks(x, feat, rotation=20, ha="right")
ax.set_ylabel("actions per game (mean)")
ax.set_title("What winning farms do more of (and less of)", color=INK, loc="left", fontweight="bold")
ax.legend(frameon=False)
plt.tight_layout(); plt.show()
cmp = pd.DataFrame({"winning": win_mean, "losing": los_mean})
cmp["ratio"] = (cmp["winning"] / cmp["losing"].replace(0, np.nan)).round(2)
print(cmp.round(1).to_string())
print("\nmean final profit: winners", round(sides[sides.win==1].score.mean()),
      "| losers", round(sides[sides.win==0].score.mean()))
```

### [Markdown Cell 9]
## 3. Which crop the winners lean on

Each side has a most planted crop. This is how often each crop is the primary crop of a winning side versus
a losing side, which tells you what the field currently rewards without you having to submit an agent to find
out.

### [Code Cell 10]
```python
cw = sides[sides.win == 1]["top_crop"].value_counts()
cl = sides[sides.win == 0]["top_crop"].value_counts()
order = [c for c in (CROP_KEYS + ["none"]) if c in set(cw.index) | set(cl.index)]
wv = [cw.get(c, 0) for c in order]; lv = [cl.get(c, 0) for c in order]
fig, ax = plt.subplots(figsize=(8.5, 4))
x = np.arange(len(order)); w = 0.4
ax.bar(x - w/2, wv, w, label="primary crop of winners", color=ACC2)
ax.bar(x + w/2, lv, w, label="primary crop of losers", color=MUT)
ax.set_xticks(x, order, rotation=15); ax.set_ylabel("sides")
ax.set_title("Primary crop, winners vs losers", color=INK, loc="left", fontweight="bold")
ax.legend(frameon=False)
plt.tight_layout(); plt.show()
wr = {c: (cw.get(c,0) / (cw.get(c,0)+cl.get(c,0)) if (cw.get(c,0)+cl.get(c,0)) else 0) for c in order}
print("win rate when a crop is the primary crop:")
for c in order: print(f"  {c:12s} {wr[c]*100:.0f}%  (n={cw.get(c,0)+cl.get(c,0)})")
```

### [Markdown Cell 11]
## 4. The ladder stopped climbing

This is the part that changed since the previous run of this notebook, and it is the reason to re-read it.

For the first stretch of the season the daily median score rose steeply, and every earlier read of this
competition, including my own, described a target that keeps moving. It no longer does. The daily index the
organisers publish shows the median peaking and then drifting DOWN, and the drift is large enough to separate
from zero. The cell below fits both phases in front of you and prints the slope, the p value and the
confidence interval, so you can see the turn rather than take my word for it.

If that holds, the practical reading flips. During the climb, a strategy that won last week was stale. After
the turn, the field has converged: the gap between the top agent and the median has compressed several times
over, which means copying the current meta buys much less than it did, and the remaining edge has to come
from somewhere the field is not already looking.

### [Markdown Cell 13]
## 5. The winning action fingerprint

Averaging every action a side takes over the season and ordering agents by win rate turns the ladder into a
fingerprint. Each row is an agent, each column an action type, the cell is that agent's mean count. The point
is which behaviours travel with a high win rate, read down the sorted rows.

### [Code Cell 14]
```python
prof_all = sides.groupby("agent")[FEAT]
counts = sides.groupby("agent").size()
keep = counts[counts >= MIN_G].index
prof = prof_all.mean().loc[keep]
wr_by = sides.groupby("agent")["win"].mean().loc[keep]
prof = prof.loc[wr_by.sort_values(ascending=False).index].head(12)
if len(prof) >= 2:
    pn = (prof - prof.min()) / (prof.max() - prof.min() + 1e-9)
    fig, ax = plt.subplots(figsize=(9, max(4, 0.5*len(prof))))
    im = ax.imshow(pn.values, cmap="magma", aspect="auto")
    ax.set_xticks(range(len(FEAT)), FEAT, rotation=25, ha="right")
    ax.set_yticks(range(len(prof)), [a[:22] for a in prof.index], fontsize=8)
    for i in range(len(prof)):
        for j in range(len(FEAT)):
            ax.text(j, i, f"{prof.values[i,j]:.0f}", ha="center", va="center", color="w", fontsize=6)
    fig.colorbar(im, ax=ax, label="normalized per column")
    ax.set_title(f"Action profile of the top agents by win rate, {DAY}", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()
else:
    print("too few qualifying agents for the fingerprint (renders on the full daily dump)")
```

### [Markdown Cell 15]
## 6. Winning profit versus losing profit

The final season profit of every winning side against every losing side. If the distributions barely
separate, the game is close and the ladder is decided at the margin, not by blowouts.

### [Code Cell 16]
```python
ws = sides[sides.win == 1].score; los = sides[sides.win == 0].score
if len(ws) and len(los):
    bins = np.linspace(min(ws.min(), los.min()), max(ws.max(), los.max()), 40)
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.hist(los, bins=bins, alpha=0.6, label="losing side", color=MUT)
    ax.hist(ws, bins=bins, alpha=0.6, label="winning side", color=ACC)
    ax.axvline(ws.median(), color=ACC, ls="--"); ax.axvline(los.median(), color=MUT, ls="--")
    ax.set_xlabel("final season profit"); ax.set_ylabel("sides"); ax.legend(frameon=False)
    ax.set_title("Final profit, winners vs losers", color=INK, loc="left", fontweight="bold")
    plt.tight_layout(); plt.show()
    print("median profit  winners", round(ws.median()), " losers", round(los.median()),
          " gap", round(ws.median()-los.median()))
```

### [Markdown Cell 17]
## 7. What actually correlates with winning

The linear correlation between each action count, final profit, and the win flag, plus the selling versus
profit scatter behind it. Correlation is not cause, both sides play all 720 turns, but it shows which levers
move together on this day.

### [Code Cell 18]
```python
C = sides[FEAT + ["score", "win"]].corr()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.2))
im = a1.imshow(C.values, cmap="coolwarm", vmin=-1, vmax=1)
a1.set_xticks(range(len(C)), C.columns, rotation=45, ha="right", fontsize=8)
a1.set_yticks(range(len(C)), C.columns, fontsize=8)
for i in range(len(C)):
    for j in range(len(C)):
        a1.text(j, i, f"{C.values[i,j]:.2f}", ha="center", va="center", fontsize=6,
                color="w" if abs(C.values[i,j]) > 0.5 else "k")
fig.colorbar(im, ax=a1, label="correlation")
a1.set_title("Action, profit, win correlation", color=INK, loc="left", fontweight="bold")
a2.scatter(sides.sell, sides.score, c=sides.win, cmap="coolwarm", s=12, alpha=0.6, edgecolor="none")
a2.set_xlabel("sell actions"); a2.set_ylabel("final profit")
a2.set_title("Selling vs profit (color = win)", color=INK, loc="left", fontweight="bold")
plt.tight_layout(); plt.show()
```

### [Markdown Cell 19]
## 8. The top three agents, side by side

The action fingerprint of the three highest win rate agents on a shared radar, each axis normalized to the
field maximum. This is the closest a static read gets to seeing distinct playstyles.

### [Code Cell 20]
```python
keep = counts[counts >= MIN_G].index
wr3 = sides[sides.agent.isin(keep)].groupby("agent")["win"].mean().sort_values(ascending=False)
top3 = wr3.head(3).index.tolist()
prof2 = sides.groupby("agent")[FEAT].mean()
mx = prof2.max() + 1e-9
if len(top3) >= 1:
    ang = np.linspace(0, 2*np.pi, len(FEAT), endpoint=False).tolist(); ang += ang[:1]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    cols = [ACC, ACC2, GD]
    for k, a in enumerate(top3):
        v = (prof2.loc[a] / mx).values.tolist(); v += v[:1]
        ax.plot(ang, v, color=cols[k % 3], label=a[:20]); ax.fill(ang, v, color=cols[k % 3], alpha=0.12)
    ax.set_xticks(ang[:-1], FEAT, fontsize=8); ax.set_yticklabels([])
    ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.1), frameon=False, fontsize=8)
    ax.set_title(f"Top agents action fingerprint, {DAY}", color=INK)
    plt.tight_layout(); plt.show()
    print("top 3 by win rate:", top3)
```

### [Markdown Cell 21]
## Honest scope, and how to use it

This is one day of ladder replays, so read it as a snapshot, not a law; fork it onto another day to see what
moves. Each replay is about 25MB, so I read a seeded random sample of at most 300 games of the day, not the
full dump; the parse cell prints exactly how many went in. The winner is the side with the higher final
profit, straight from the replay rewards. Ties and unfinished games are dropped. The strategy counts are the
raw action tallies over the 720 turn season, a faithful count of what each side did, not a judgement of why.
Everything is recomputed from the logs when you run the notebook, with no pasted numbers and no leaderboard
claim, so you can trust it as far as the parse, which is all shown above.

Two companion notebooks read this same competition from the other end, off the engine
and the reference tables instead of the replays.
[The best thing to farm has a market of 59 units](https://www.kaggle.com/code/busyaprime/the-best-thing-to-farm-has-a-market-of-59-units)
shows why the published coins per tile per day is a ceiling almost nobody reaches, and
how shallow each good's market really is: sheep lead the rate table and the sheep market
absorbs 59 units before the price hits its floor.
[One town in three has no yarn store at all](https://www.kaggle.com/code/busyaprime/one-town-in-three-has-no-yarn-store-at-all)
works out the shop draw exactly, all 6435 towns of it, and what that does to the risk of
planting a good that nobody in your town buys.

If you want the same live-from-raw-logs read for a different competition, the companion tracker
[What actually wins on the ladder](https://www.kaggle.com/code/busyaprime/what-actually-wins-on-the-ladder)
does this for the Pokemon TCG battle meta, and
[Which open Kaggle competition still has room](https://www.kaggle.com/code/busyaprime/which-open-kaggle-competition-still-has-room)
tracks every open competition worth entering.

