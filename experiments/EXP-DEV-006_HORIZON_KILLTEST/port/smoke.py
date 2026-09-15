import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kagsim_py'))
sys.path.insert(0, os.path.dirname(__file__))
import kagsim_py as kagsim

t0 = time.time()
g = kagsim.Game(247000)
o = g.observe(0)
print('step0 shops:', o['town'], 'money:', o['farms'][0]['money'], 'day/hr:', o['day'], o['hour'])
n = 0
while not g.done:
    o0 = g.observe(0)
    o1 = g.observe(1)
    a0 = {"farmer": ["PASS"], "hands": [], "market": []}
    a1 = {"farmer": ["PASS"], "hands": [], "market": []}
    g.step(a0, a1)
    n += 1
print('steps:', n, 'done:', g.done, 'rewards:', g.reward(0), g.reward(1))
print('shops:', g.observe(0)['town'])
print('elapsed: %.2fs' % (time.time() - t0))
