import random

def _lz76_complexity(s: str) -> int:
    n = len(s)
    if n == 0: return 0
    i, k, l = 0, 1, 1
    c, k_max = 1, 1
    while True:
        if i + k - 1 < n and l + k - 1 < n and s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            if k > k_max: k_max = k
            i += 1
            if i == l:
                c += 1
                l += k_max
                if l + 1 > n: break
                i = 0
                k = 1
                k_max = 1
            else:
                k = 1
    return c

print("Testing LZ on large combinations...")
import string
for _ in range(100):
    seq = "".join(random.choice(['M', 'I', 'S']) for _ in range(200))
    _lz76_complexity(seq)

print("Random passed. Testing repeating blocks...")
seq = "M" * 100 + "S" * 100
_lz76_complexity(seq)

seq = "M" * 100 + "I" + "M" * 99
_lz76_complexity(seq)

print("LZ Test finished successfully.")
