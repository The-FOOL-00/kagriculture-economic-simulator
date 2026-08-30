import sys
sys.path.insert(0, r"c:\Users\Sundareswaran\Kagriculture")
from agents.apex_grandmaster_v4 import ApexGrandmasterV4

_instance = ApexGrandmasterV4(**{'sell_batch': 18})
def agent(obs, cfg=None):
    return _instance(obs, cfg)
