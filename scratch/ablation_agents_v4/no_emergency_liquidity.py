import sys
sys.path.insert(0, r"c:\Users\Sundareswaran\Kagriculture")
from agents.apex_grandmaster_v4 import ApexGrandmasterV4

_instance = ApexGrandmasterV4(**{'emergency_liquidity': False})
def agent(obs, cfg=None):
    return _instance(obs, cfg)
