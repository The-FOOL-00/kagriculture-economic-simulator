# Market Forensics: Mechanisms of Competitive Price Suppression

---

## 1. How Strong Agents Exploit the Shared Market

In the Kaggriculture engine, the town market is a shared pricing pool governed by:
$$\text{price}(item) = f(\text{market["inventory"][item]})$$
Every unit sold by Player 0 or Player 1 increments `market["inventory"][item]`, immediately depressing the market price for all subsequent sales by both players.

### The Front-Running Mechanism (`_V51ResidualConfig`)
V54 and V66 do not wait for fixed calendar intervals to sell. They implement a state-dependent preemption algorithm:
1. **Low Shed Threshold (`front_supply_threshold = 3.0`):** As soon as 3 units of milk, wool, or fertilizer accumulate in the shed, the agent immediately quotes market sales.
2. **Preemptive Lookahead (`preempt_horizon = 3`):** Projects price drops over the next 3 steps. If an opponent is approaching their shed or prices are near local peaks, V54 submits `SELL` orders in batches of 4–12 units to capture peak prices before the opponent can sell.
3. **Price Depression Extraction:**
   * In solo play, Milk sells at **$213.4** on average.
   * Against an active competitor (V54 vs V66), Milk is driven down to **$126.9** (-40.5%).
   * By front-running and selling first, V54 captures the high end of the price curve ($180–$220), leaving the slower opponent to sell into the glutted trough ($80–$110).

---

## 2. Competitive Market Counterfactual Scoreboard

Evaluated across 10 deterministic validation seeds (2000–2009):

| Market Regime | Matchup | Agent 0 Mean | Agent 1 Mean | Margin | Strategic Takeaway |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **A: Normal Shared Market** | V2 vs V54 | $30,378 | $126,406 | -$96,028 | V54 crushes V2 by front-running and flooding market |
| | V54 vs V66 | $75,688 | $83,324 | -$7,636 | Mutual price depression cuts both champions' wealth in half |
| | V66 vs V54 | $83,324 | $75,688 | +$7,636 | V66 holds consistent 90% win rate edge over V54 |
| **B: Capped Opponent Sells**| V2 vs V54 | $38,620 | $60,726 | -$22,106 | Capping V54 sales to 5/turn recovers +$8.2k for V2 |
| | V54 vs V66 | $120,693 | $28,814 | +$91,879 | When V66 is volume-capped, V54 wealth rebounds to $120k+ |
| | V66 vs V54 | $119,229 | $49,072 | +$70,157 | When V54 is volume-capped, V66 wealth rebounds to $119k+ |
| **C: Delayed Opponent Sells**| V2 vs V54 | $30,378 | $126,406 | -$96,028 | A 24-turn opening delay has zero impact on mid-game gluts |
| | V54 vs V66 | $75,688 | $83,324 | -$7,636 | Mid-game market dynamics completely swamp Day 1 delays |
| **E: Frozen Opponent Sells** | V2 vs V54 | **$68,891** | $0 | +$68,891 | **V2 recovers its full solo potential ($68.9k) when V54 cannot sell!** |
| | V54 vs V66 | **$145,135** | $0 | +$145,135 | **V54 recovers from $75.7k to $145.1k (+69.4k gain) under pristine prices!** |
| | V66 vs V54 | **$159,028** | $0 | +$159,028 | **V66 recovers from $83.3k to $159.0k (+75.7k gain) under pristine prices!** |

---

## 3. Separation of Production Edge from Market Edge

$$\text{Total Gap (V2 vs V54: \$96,028)} = \underbrace{\text{Production Edge (\$75,249)}}_{\text{V54 Solo (\$144k) } - \text{ V2 Solo (\$68.9k)}} + \underbrace{\text{Market Interaction Edge (\$38,513)}}_{\text{V2 Solo (\$68.9k) } - \text{ V2 Realized (\$30.4k)}}$$

1. **The Production Edge:** V54 out-produces V2 by **$75,249** because V54 grows 187 wheat and 38 strawberries while maintaining 9 cows and 5 sheep, whereas V2 operates a much smaller crop footprint.
2. **The Market Interaction Edge:** V54 inflicts **$38,513 of pure price suppression damage** on V2 by saturating the market with milk, wool, and fertilizer.
3. **Mutual Destruction in Champion Play:** When two titans (V54 and V66) compete, **each inflicts ~$70,000–$75,000 of price suppression on the other**, compressing total scores from $165k solo down to $75k–$83k.
