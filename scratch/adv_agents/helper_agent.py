
import helper_leak
class HelperAgent:
    def act(self, obs):
        s = helper_leak.reflect()
        return {'market': [], 'workers': []}
