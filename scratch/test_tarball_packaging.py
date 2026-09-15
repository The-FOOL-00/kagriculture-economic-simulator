import tempfile
import tarfile
import os
import subprocess
import sys

def test():
    with tempfile.TemporaryDirectory() as td:
        # Build tarball with main.py and candidates/candidate_cl_fert_gated.py
        src_dir = os.path.join(td, 'sub_src')
        os.makedirs(os.path.join(src_dir, 'candidates'), exist_ok=True)
        with open('candidates/candidate_cl_labor_minimal_v1.py', 'rb') as f_in:
            with open(os.path.join(src_dir, 'main.py'), 'wb') as f_out:
                f_out.write(f_in.read())
        with open('candidates/candidate_cl_fert_gated.py', 'rb') as f_in:
            with open(os.path.join(src_dir, 'candidates', 'candidate_cl_fert_gated.py'), 'wb') as f_out:
                f_out.write(f_in.read())

        tar_path = os.path.join(td, 'submission.tar.gz')
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(os.path.join(src_dir, 'main.py'), arcname='main.py')
            tar.add(os.path.join(src_dir, 'candidates'), arcname='candidates')

        test_script = os.path.join(td, 'test_tar.py')
        code = f'''
import sys, kaggle_environments
sys.path = [p for p in sys.path if "kagriculture" not in p.lower()]
env = kaggle_environments.make("kaggriculture", configuration={{"episodeSteps": 20, "seed": 10001}})
res = env.run([r"{tar_path}", "starter"])
print("Tarball status:", res[-1][0]["status"])
print("Reward:", res[-1][0]["reward"])
print("Action step 1:", res[1][0]["action"])
'''
        with open(test_script, 'w') as f:
            f.write(code)
            
        p = subprocess.run([sys.executable, test_script], capture_output=True, text=True)
        print('STDOUT:\n', p.stdout)
        print('STDERR:\n', p.stderr)

if __name__ == '__main__':
    test()
