import os
import subprocess
import json

repos = [
    {
        "name": "destbreso/kaggriculture-cppsim",
        "dir": r"c:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-cppsim",
        "claimed_sha": "da15925dcf2357d750cbae4bf35712011b4733c8"
    },
    {
        "name": "destbreso/kaggriculture-island-ga",
        "dir": r"c:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-island-ga",
        "claimed_sha": "be23b55a63d6376057097cb2d07e92e0ddbeb2c3"
    },
    {
        "name": "mohui666/kaggriculture-v66-agent",
        "dir": r"c:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent",
        "claimed_sha": "cb4a8157fae6baab6a118c7f922a05ca0a4455b4"
    },
    {
        "name": "okami001/Kaggriculture",
        "dir": r"c:\Users\Sundareswaran\Kagriculture\external_repos\okami001-Kaggriculture",
        "claimed_sha": "aabe1a0ef5118af738c00dca82c017abb807855d"
    },
    {
        "name": "lixingtao123/Kaggriculture",
        "dir": r"c:\Users\Sundareswaran\Kagriculture\external_repos\lixingtao123-Kaggriculture",
        "claimed_sha": "95e818edee0f62831375a624d45f569dd75ffe7c"
    }
]

command_log = []

def run_cmd(cmd, cwd):
    cmd_str = f"cd {cwd} && {' '.join(cmd)}"
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    command_log.append({
        "cmd": " ".join(cmd),
        "cwd": cwd,
        "stdout": res.stdout.strip(),
        "stderr": res.stderr.strip(),
        "returncode": res.returncode
    })
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def get_dir_size(path, exclude_git=False):
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(path):
        if exclude_git and '.git' in dirs:
            dirs.remove('.git')
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
                file_count += 1
            except OSError:
                pass
    return total_size, file_count

manifest = {}

for repo in repos:
    r_dir = repo["dir"]
    r_name = repo["name"]
    claimed = repo["claimed_sha"]
    print(f"=== Verifying {r_name} ===")
    
    is_git, _, _ = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], r_dir)
    head_sha, _, _ = run_cmd(["git", "rev-parse", "HEAD"], r_dir)
    status, _, _ = run_cmd(["git", "status", "--short"], r_dir)
    remotes, _, _ = run_cmd(["git", "remote", "-v"], r_dir)
    log_1, _, _ = run_cmd(["git", "log", "-1", "--oneline"], r_dir)
    toplevel, _, _ = run_cmd(["git", "rev-parse", "--show-toplevel"], r_dir)
    tracked_files_raw, _, _ = run_cmd(["git", "ls-files"], r_dir)
    tracked_files = [f for f in tracked_files_raw.splitlines() if f.strip()]
    
    size_excl, count_excl = get_dir_size(r_dir, exclude_git=True)
    size_incl, count_incl = get_dir_size(r_dir, exclude_git=False)
    
    sha_match = (head_sha.lower() == claimed.lower())
    has_uncommitted = len(status.strip()) > 0
    
    manifest[r_name] = {
        "repo_name": r_name,
        "absolute_path": os.path.abspath(r_dir),
        "claimed_sha": claimed,
        "verified_head_sha": head_sha,
        "sha_match": sha_match,
        "is_inside_work_tree": is_git == "true",
        "top_level": toplevel,
        "git_status_short": status,
        "has_uncommitted_modifications": has_uncommitted,
        "git_remote": remotes.splitlines(),
        "git_log_last": log_1,
        "size_bytes_excluding_git": size_excl,
        "size_bytes_including_git": size_incl,
        "file_count_excluding_git": count_excl,
        "file_count_including_git": count_incl,
        "tracked_file_count": len(tracked_files),
        "tracked_files": tracked_files
    }
    print(f"Path: {toplevel}")
    print(f"HEAD SHA: {head_sha} (Match claimed: {sha_match})")
    print(f"Log: {log_1}")
    print(f"Status: '{status}' (Uncommitted: {has_uncommitted})")
    print(f"Size excl .git: {size_excl} bytes, files: {count_excl}; Tracked: {len(tracked_files)}")

# Write manifest
with open(r"forensic_verification\repo_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

# Append commands to command_log.txt
with open(r"forensic_verification\command_log.txt", "a", encoding="utf-8") as f:
    for entry in command_log:
        f.write(f"[{entry['cwd']}] $ {entry['cmd']}\n")
        if entry['stdout']:
            f.write(f"STDOUT:\n{entry['stdout']}\n")
        if entry['stderr']:
            f.write(f"STDERR:\n{entry['stderr']}\n")
        f.write(f"EXIT CODE: {entry['returncode']}\n\n")

print("\nWrote forensic_verification/repo_manifest.json and updated command_log.txt")
