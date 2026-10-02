#!/usr/bin/env python3
"""Unpack base85/zlib compressed submissions in live_meta into clean readable files."""

import os
import re
import zlib
import base64
import tarfile
import io

META_DIR = os.path.dirname(os.path.abspath(__file__))

def try_unpack(filepath):
    dirname = os.path.dirname(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # Look for b85decode or b64decode
    b85_matches = re.findall(r"base64\.b85decode\(['\"]([^'\"]+)['\"]\)", text)
    if b85_matches:
        for idx, payload in enumerate(b85_matches):
            try:
                raw = base64.b85decode(payload)
                decomp = zlib.decompress(raw)
                out_path = os.path.join(dirname, f"unpacked_b85_{idx}.py")
                with open(out_path, 'wb') as out_f:
                    out_f.write(decomp)
                print(f"Successfully unpacked b85 payload {idx} in {os.path.basename(dirname)} ({len(decomp)} bytes)")
            except Exception as e:
                # Might be a tar.gz archive
                try:
                    raw = base64.b85decode(payload)
                    decomp = zlib.decompress(raw)
                    tar = tarfile.open(fileobj=io.BytesIO(decomp))
                    tar_dir = os.path.join(dirname, f"unpacked_tar_{idx}")
                    os.makedirs(tar_dir, exist_ok=True)
                    tar.extractall(tar_dir)
                    print(f"Successfully extracted tar.gz payload {idx} in {os.path.basename(dirname)}")
                except Exception as e2:
                    print(f"Failed unpacking payload {idx} in {os.path.basename(dirname)}: {e} / {e2}")

    b64_matches = re.findall(r"base64\.b64decode\(['\"]([^'\"]+)['\"]\)", text)
    if b64_matches:
        for idx, payload in enumerate(b64_matches):
            try:
                raw = base64.b64decode(payload)
                try:
                    decomp = zlib.decompress(raw)
                except Exception:
                    decomp = raw
                out_path = os.path.join(dirname, f"unpacked_b64_{idx}.py")
                with open(out_path, 'wb') as out_f:
                    out_f.write(decomp)
                print(f"Successfully unpacked b64 payload {idx} in {os.path.basename(dirname)} ({len(decomp)} bytes)")
            except Exception as e:
                print(f"Failed b64 payload {idx} in {os.path.basename(dirname)}: {e}")

def main():
    for root, dirs, files in os.walk(META_DIR):
        for f in files:
            if f.endswith('_extracted.py') or f.endswith('.py'):
                if not f.startswith('unpack_') and not f.startswith('analyze_') and not f.startswith('extract_'):
                    try_unpack(os.path.join(root, f))

if __name__ == '__main__':
    main()
