
import kagsim
class FutureSimAgent:
    def __init__(self):
        self.future_known = False
    def act(self, obs):
        if not self.future_known:
            g_fut = kagsim.Game(50000)
            self.future_known = True
        return {'market': [], 'workers': []}
