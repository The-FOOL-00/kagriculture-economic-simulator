import re

with open('candidates/v30_a7_standalone/main.py', 'rb') as f:
    data = f.read()

# find _V3_SRC = b'...'
idx = data.find(b'_V3_SRC = b\'')
if idx != -1:
    start = idx + len(b'_V3_SRC = b\'')
    # read until unescaped quote
    buf = []
    i = start
    while i < len(data):
        if data[i] == ord(b'\\'):
            buf.append(data[i:i+2])
            i += 2
        elif data[i] == ord(b'\''):
            break
        else:
            buf.append(bytes([data[i]]))
            i += 1
    raw_bytes = b"".join(buf)
    # decode python escape sequences
    v3_src = raw_bytes.decode('unicode_escape').encode('latin1').decode('utf-8', errors='ignore')
    print('Found _V3_SRC length:', len(v3_src))
    with open('scratch/v3_source.py', 'w', encoding='utf-8') as out:
        out.write(v3_src)
    print('Wrote scratch/v3_source.py')

    # check if _PARENT_SRC is inside
    pidx = v3_src.find('_PARENT_SRC = b\'')
    if pidx != -1:
        pstart = pidx + len('_PARENT_SRC = b\'')
        pbuf = []
        i = pstart
        while i < len(v3_src):
            if v3_src[i] == '\\':
                pbuf.append(v3_src[i:i+2])
                i += 2
            elif v3_src[i] == '\'':
                break
            else:
                pbuf.append(v3_src[i])
                i += 1
        raw_p = "".join(pbuf).encode('latin1').decode('unicode_escape').encode('latin1').decode('utf-8', errors='ignore')
        print('Found _PARENT_SRC length:', len(raw_p))
        with open('scratch/parent_source.py', 'w', encoding='utf-8') as out:
            out.write(raw_p)
        print('Wrote scratch/parent_source.py')
