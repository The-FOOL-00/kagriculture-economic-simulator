import json
from collections import defaultdict

def analyze_tape0():
    tapes = json.load(open("extracted_agents/dmitrii_lb2800/actions.json"))
    tape0 = tapes[0]
    
    hire_counts = []
    order_lengths = []
    
    for s in range(len(tape0)):
        m = tape0[s].get("market", [])
        order_lengths.append(len(m))
        hires = sum(1 for o in m if o and o[0] == "HIRE")
        if hires > 0:
            hire_counts.append((s, s//24, s%24, hires, len(m), m))
            
    print(f"Total steps with HIRE: {len(hire_counts)}")
    print(f"Max orders in any step: {max(order_lengths)}")
    print("\nSample of steps with HIRE:")
    for s, d, h, nh, tot, m in hire_counts[:15]:
        print(f"Step {s:3d} (D{d:02d} h{h:02d}): Hires={nh}, TotalOrders={tot}, Orders={m}")

if __name__ == "__main__":
    analyze_tape0()
