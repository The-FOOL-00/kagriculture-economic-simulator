# SPDX-License-Identifier: MIT
"""CPython-compatible Mersenne Twister port of sim/pyrandom.hpp.

Bit-exact port: every 32-bit op is masked, op order preserved, including the
optimized init_by_array (keylen 1/2 fast paths + generic path + second pass).
Python ints are unbounded so each assignment mimics uint32_t wrap explicitly.
"""

M32 = 0xFFFFFFFF
N = 624
M = 397
MATRIX_A = 0x9908B0DF
UPPER = 0x80000000
LOWER = 0x7FFFFFFF


def _genrand_base():
    m = [0] * N
    m[0] = 19650218
    for i in range(1, N):
        m[i] = (1812433253 * (m[i - 1] ^ (m[i - 1] >> 30)) + i) & M32
    return m


_GENRAND_BASE = _genrand_base()


class PyRandom:
    def __init__(self, key):
        self.mt = [0] * N
        self.index = N
        self.seed(key)

    def seed(self, key):
        key &= 0xFFFFFFFFFFFFFFFF
        words = []
        if key == 0:
            words = [0]
        else:
            while key:
                words.append(key & M32)
                key >>= 32
        self._init_by_array(words, len(words))

    def genrand_uint32(self):
        if self.index >= N:
            mt = self.mt
            for k in range(0, N - M):
                y = (mt[k] & UPPER) | (mt[k + 1] & LOWER)
                mt[k] = mt[k + M] ^ (y >> 1) ^ (MATRIX_A if (y & 1) else 0)
            for k in range(N - M, N - 1):
                y = (mt[k] & UPPER) | (mt[k + 1] & LOWER)
                mt[k] = mt[k + (M - N)] ^ (y >> 1) ^ (MATRIX_A if (y & 1) else 0)
            y = (mt[N - 1] & UPPER) | (mt[0] & LOWER)
            mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ (MATRIX_A if (y & 1) else 0)
            self.index = 0
        y = self.mt[self.index]
        self.index += 1
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= (y >> 18)
        return y & M32

    def random(self):
        a = self.genrand_uint32() >> 5
        b = self.genrand_uint32() >> 6
        return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)

    def getrandbits(self, k):
        return self.genrand_uint32() >> (32 - k)

    def randbelow(self, n):
        k = n.bit_length()
        r = self.getrandbits(k)
        while r >= n:
            r = self.getrandbits(k)
        return r

    def choice_index(self, length):
        return self.randbelow(length)

    def _init_by_array(self, key, keylen):
        mt = self.mt
        base = _GENRAND_BASE
        for i in range(N):
            mt[i] = base[i]
        self.index = N
        i = 1
        j = 0
        k = N if N > keylen else keylen
        prev = mt[0]
        while k > 0:
            run = N - i
            if run > k:
                run = k
            if keylen == 1:
                kv = key[0]
                for _ in range(run):
                    prev = (mt[i] ^ ((prev ^ (prev >> 30)) * 1664525 & M32)) + kv
                    prev &= M32
                    mt[i] = prev
                    i += 1
            elif keylen == 2:
                for _ in range(run):
                    prev = (mt[i] ^ ((prev ^ (prev >> 30)) * 1664525 & M32)) + key[j] + j
                    prev &= M32
                    mt[i] = prev
                    i += 1
                    j ^= 1
            else:
                for _ in range(run):
                    prev = (mt[i] ^ ((prev ^ (prev >> 30)) * 1664525 & M32)) + key[j] + j
                    prev &= M32
                    mt[i] = prev
                    i += 1
                    j += 1
                    if j >= keylen:
                        j = 0
            k -= run
            if i >= N:
                mt[0] = mt[N - 1]
                prev = mt[0]
                i = 1
        k = N - 1
        while k > 0:
            run = N - i
            if run > k:
                run = k
            for _ in range(run):
                prev = (mt[i] ^ ((prev ^ (prev >> 30)) * 1566083941 & M32)) - i
                prev &= M32
                mt[i] = prev
                i += 1
            k -= run
            if i >= N:
                mt[0] = mt[N - 1]
                prev = mt[0]
                i = 1
        mt[0] = 0x80000000
        self.index = N
