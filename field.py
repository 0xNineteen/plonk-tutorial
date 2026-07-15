# Prime with 4 | (p - 1) so a primitive 4th root of unity exists (N = 4 trace).
p = 1000033

def mod(n):
    return n % p

def add(a, b):
    return mod(a + b)

def sub(a, b):
    return mod(a - b)

def mul(a, b):
    return mod(a * b)

def inv(a):
    if mod(a) == 0:
        raise ZeroDivisionError("inv(0)")
    return pow(a, p - 2, p)

def div(a, b):
    return mul(a, inv(b))

def find_omega(n):
    """Return primitive n-th root of unity; requires n | (p - 1)."""
    if (p - 1) % n != 0:
        raise ValueError(f"no order-{n} subgroup in F_p (need n | p-1)")
    for g in range(2, p):
        omega = pow(g, (p - 1) // n, p)
        if omega == 1:
            continue
        if pow(omega, n, p) == 1 and pow(omega, n // 2, p) != 1:
            return omega
    raise ValueError("no primitive root found")