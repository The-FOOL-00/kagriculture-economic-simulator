# SPDX-License-Identifier: MIT
"""V33 Route Clustering Pipeline.

Loads all available replays, extracts fingerprints, performs clustering across
k in {2, 3, 4, 5, 6, 8, 10, 12}, measures silhouette scores, and outputs
route_fingerprints.json and route_clusters.json.
"""

from __future__ import annotations
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from candidates.v33_meta_strategy.replay_loader import ReplayLoader
from candidates.v33_meta_strategy.replay_normalizer import ReplayNormalizer
from candidates.v33_meta_strategy.route_extractor import RouteExtractor


def main():
    loader = ReplayLoader()
    replays = loader.list_all_replays()
    normalizer = ReplayNormalizer()
    extractor = RouteExtractor()

    print(f"Loading and extracting fingerprints from {len(replays)} replays...")
    all_fingerprints = []
    feature_matrix = []

    for p in replays:
        try:
            data = loader.load_replay(p)
            trajs = normalizer.normalize_replay(data, p)
            for t in trajs:
                fp = extractor.extract_fingerprint(t)
                all_fingerprints.append(fp)
                feature_matrix.append(fp.to_feature_vector())
        except Exception as e:
            print(f"Error processing {p}: {e}")

    X = np.array(feature_matrix)
    print(f"Extracted {len(all_fingerprints)} fingerprints. Feature matrix shape: {X.shape}")

    # Save route_fingerprints.json
    with open("route_fingerprints.json", "w", encoding="utf-8") as f:
        json.dump([fp.to_dict() for fp in all_fingerprints], f, indent=2)
    print("Saved route_fingerprints.json")

    # Evaluate k in {2, 3, 4, 5, 6, 8, 10, 12}
    k_values = [2, 3, 4, 5, 6, 8, 10, 12]
    cluster_metrics = {}

    for k in k_values:
        if k >= len(X):
            continue
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        sil = float(silhouette_score(X, labels)) if len(set(labels)) > 1 else 0.0
        inertia = float(km.inertia_)
        cluster_metrics[k] = {"k": k, "silhouette": sil, "inertia": inertia}
        print(f"k={k:2d} | Silhouette: {sil:.4f} | Inertia: {inertia:.1f}")

    best_k = max(cluster_metrics.keys(), key=lambda k: cluster_metrics[k]["silhouette"])
    print(f"Best k by silhouette: {best_k} (score: {cluster_metrics[best_k]['silhouette']:.4f})")

    # Also cluster at k=6 (standard tournament taxonomy)
    chosen_k = 6 if 6 in cluster_metrics else best_k
    final_km = KMeans(n_clusters=chosen_k, random_state=42, n_init=10)
    final_labels = final_km.fit_predict(X)

    clusters_data = {}
    for i in range(chosen_k):
        cluster_fps = [all_fingerprints[idx] for idx, l in enumerate(final_labels) if l == i]
        mean_cash = float(np.mean([fp.terminal_cash for fp in cluster_fps])) if cluster_fps else 0.0
        mean_workers = float(np.mean([fp.worker_trajectory[-1] for fp in cluster_fps])) if cluster_fps else 0.0
        mean_land = float(np.mean([fp.land_trajectory[-1] for fp in cluster_fps])) if cluster_fps else 0.0
        clusters_data[f"cluster_{i}"] = {
            "cluster_id": i,
            "size": len(cluster_fps),
            "mean_terminal_cash": mean_cash,
            "mean_final_workers": mean_workers,
            "mean_final_land": mean_land,
            "sample_routes": [fp.route_id for fp in cluster_fps[:5]]
        }

    with open("route_clusters.json", "w", encoding="utf-8") as f:
        json.dump({"metrics": cluster_metrics, "best_k": best_k, "chosen_k": chosen_k, "clusters": clusters_data}, f, indent=2)
    print("Saved route_clusters.json")


if __name__ == "__main__":
    main()
