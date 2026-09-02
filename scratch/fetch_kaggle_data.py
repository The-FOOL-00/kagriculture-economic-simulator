import sys
import json
import os
import subprocess

def test_kaggle_api():
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("Kaggle API Authenticated successfully!")
        
        print("\n--- Submissions for kaggriculture ---")
        try:
            subs = api.competition_submissions("kaggriculture")
            for s in subs:
                print(f"Ref: {s.ref}, Date: {s.date}, Description: {s.description}, Status: {s.status}, PublicScore: {s.public_score}, PrivateScore: {s.private_score}")
        except Exception as e:
            print(f"Error fetching submissions: {e}")

        print("\n--- Leaderboard for kaggriculture ---")
        try:
            lb = api.competition_leaderboard_view("kaggriculture")
            print(f"Leaderboard entries: {len(lb) if lb else 0}")
            for entry in (lb[:25] if lb else []):
                print(entry)
        except Exception as e:
            print(f"Error fetching leaderboard: {e}")

        print("\n--- Datasets matching 'kaggriculture' ---")
        try:
            datasets = api.dataset_list(search="kaggriculture")
            print(f"Found {len(datasets)} datasets:")
            for d in datasets:
                print(f"Ref: {d.ref}, Title: {d.title}, Size: {d.size}, LastUpdated: {d.lastUpdated}")
        except Exception as e:
            print(f"Error fetching datasets: {e}")

        print("\n--- Kernels matching 'kaggriculture' ---")
        try:
            kernels = api.kernel_list(search="kaggriculture")
            print(f"Found {len(kernels)} kernels:")
            for k in kernels:
                print(f"Ref: {k.ref}, Title: {k.title}, TotalVotes: {k.totalVotes}, LastRunTime: {k.lastRunTime}")
        except Exception as e:
            print(f"Error fetching kernels: {e}")

    except Exception as e:
        print(f"Kaggle API failed: {e}")

if __name__ == "__main__":
    test_kaggle_api()
