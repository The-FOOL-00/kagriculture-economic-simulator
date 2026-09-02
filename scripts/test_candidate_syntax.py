import importlib.util

def check():
    files = [
        'agents/candidate_a_aethel_v1.py',
        'agents/candidate_b_aethel_mc.py',
        'agents/candidate_c_aethel_t712.py',
        'agents/candidate_d_aethel_refined.py'
    ]
    for path in files:
        spec = importlib.util.spec_from_file_location('mod', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert callable(getattr(mod, 'agent', None)), f"{path} missing agent callable"
        print(f"Verified {path}: Valid Python, agent() callable present.")

if __name__ == '__main__':
    check()
