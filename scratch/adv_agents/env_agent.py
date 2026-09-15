
import os
class EnvAgent:
    def act(self, obs):
        x = os.environ.get('PATH')
        return {'market': [], 'workers': []}
