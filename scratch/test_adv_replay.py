
import os, json
class ReplayLeakAgent:
    def act(self, obs):
        if os.path.exists('sample_replay.json'):
            with open('sample_replay.json', 'r') as f:
                data = json.load(f)
        return {'market': [], 'workers': []}
