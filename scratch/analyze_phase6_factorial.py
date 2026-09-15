import json
import numpy as np

def bootstrap_ci(arr, n_boot=10000):
    means = []
    n = len(arr)
    rng = np.random.default_rng(42)
    for _ in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        means.append(np.mean(sample))
    return np.percentile(means, [2.5, 97.5])

def analyze():
    with open("scratch/phase6_factorial_results.json") as f:
        data = json.load(f)

    n = len(data)
    print(f"=== PHASE 6: 2x2 FACTORIAL DECOMPOSITION (N={n} SEEDS: 1050-1149) ===")

    # Arms:
    # X: Q50 cow timing, No reservation (Raw Q50)
    # W: M1 cow timing, No reservation (Cap Day 6 cow buy at 1)
    # Z: Q50 cow timing, Slot reservation (Mechanism A)
    # Y: M1 cow timing, Slot reservation

    rew_X = np.array([d["X"]["reward"] for d in data])
    rew_W = np.array([d["W"]["reward"] for d in data])
    rew_Z = np.array([d["Z"]["reward"] for d in data])
    rew_Y = np.array([d["Y"]["reward"] for d in data])

    wool_X = np.array([d["X"]["sold"]["WOOL"] for d in data])
    wool_W = np.array([d["W"]["sold"]["WOOL"] for d in data])
    wool_Z = np.array([d["Z"]["sold"]["WOOL"] for d in data])
    wool_Y = np.array([d["Y"]["sold"]["WOOL"] for d in data])

    print("\nCell Means (Terminal Reward):")
    print(f"{'':<25} | {'No Slot Reservation':<22} | {'Slot Reservation':<22}")
    print("-" * 75)
    print(f"{'M1 Cow Timing':<25} | W: ${np.mean(rew_W):10,.1f} (Wool {np.mean(wool_W):.1f}) | Y: ${np.mean(rew_Y):10,.1f} (Wool {np.mean(wool_Y):.1f})")
    print(f"{'Q50 Cow Timing':<25} | X: ${np.mean(rew_X):10,.1f} (Wool {np.mean(wool_X):.1f}) | Z: ${np.mean(rew_Z):10,.1f} (Wool {np.mean(wool_Z):.1f})")

    # Factorial Main Effects:
    # 1. Main effect of Slot Reservation:
    # Average difference: 0.5 * ((Z - X) + (Y - W))
    eff_res = 0.5 * ((rew_Z - rew_X) + (rew_Y - rew_W))
    ci_res = bootstrap_ci(eff_res)
    
    # 2. Main effect of Cow Timing (Q50 timing vs M1 timing):
    # Average difference: 0.5 * ((X - W) + (Z - Y))
    eff_time = 0.5 * ((rew_X - rew_W) + (rew_Z - rew_Y))
    ci_time = bootstrap_ci(eff_time)

    # 3. Interaction effect:
    # ((Z - X) - (Y - W))
    eff_int = (rew_Z - rew_X) - (rew_Y - rew_W)
    ci_int = bootstrap_ci(eff_int)

    # Wool effects
    eff_wool_res = 0.5 * ((wool_Z - wool_X) + (wool_Y - wool_W))
    eff_wool_time = 0.5 * ((wool_X - wool_W) + (wool_Z - wool_Y))

    print("\nFactorial Decomposition:")
    print(f"Main Effect of Slot Reservation: ${np.mean(eff_res):+10,.1f} | 95% Bootstrap CI: [${ci_res[0]:+,.1f}, ${ci_res[1]:+,.1f}] | Wool Effect: {np.mean(eff_wool_res):+.2f} units")
    print(f"Main Effect of Cow Timing:       ${np.mean(eff_time):+10,.1f} | 95% Bootstrap CI: [${ci_time[0]:+,.1f}, ${ci_time[1]:+,.1f}] | Wool Effect: {np.mean(eff_wool_time):+.2f} units")
    print(f"Interaction Effect:              ${np.mean(eff_int):+10,.1f} | 95% Bootstrap CI: [${ci_int[0]:+,.1f}, ${ci_int[1]:+,.1f}]")

if __name__ == "__main__":
    analyze()
