import field as F
from circuit import N_TRACE_LENGTH
from layout import NUM_PLACEMENTS

OMEGA = F.find_omega(N_TRACE_LENGTH)
DOMAIN = [pow(OMEGA, i, F.p) for i in range(N_TRACE_LENGTH)]

OMEGA_PL = F.find_omega(NUM_PLACEMENTS)
PLACEMENT_DOMAIN = [pow(OMEGA_PL, i, F.p) for i in range(NUM_PLACEMENTS)]

def placement_vanishing_eval(x):
    """Z_{H_pl}(x) = x^12 - 1"""
    return F.sub(pow(x, NUM_PLACEMENTS, F.p), 1)

def lagrange_basis(j, x):
    """L_j(x) — j-th Lagrange basis polynomial evaluated at x."""
    # L_j(X) = Π_{m≠j} (X - x_m) / (x_j - x_m)
    result = 1
    for m in range(N_TRACE_LENGTH):
        if m != j:
            num = F.sub(x, DOMAIN[m])
            denom = F.sub(DOMAIN[j], DOMAIN[m])
            result = F.mul(result, F.div(num, denom))
    return result

def vanishing_eval(x):
    """Z_H(x) = x^N - 1 (mod p)."""
    return F.sub(pow(x, N_TRACE_LENGTH, F.p), 1)
