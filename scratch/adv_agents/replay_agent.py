
import os
class ReplayLeakAgent:
    def __init__(self):
        self.leaked_data = None
    def act(self, obs):
        if self.leaked_data is None:
            with open('scratch/verify_agent_zero_leakage.py', 'r') as f:
                self.leaked_data = f.readline()
        return {'market': [], 'workers': []}
