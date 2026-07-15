import field as F
import random
import poly

MAX_DEGREE = 32

def trusted_setup(max_degree=MAX_DEGREE):
    """Return {tau, powers} with powers[i] = τ^i."""
    tau = random.randint(1, F.p - 1)
    powers = [pow(tau, i, F.p) for i in range(MAX_DEGREE)]
    return {"tau": tau, "powers": powers}

def commit(coeffs, setup):
    """C = f(τ)."""
    return poly.eval_poly(coeffs, setup["tau"])

# so we want to prove we know an f s.t f(z) = y without revealing f,
# you commit to f with tau, then verifier sends a z to evaulate,
# and the prover must supply a valid quotient (with no remainder) for f(x) - y / (x - z)
# (which is f(X) - y with the root at z factored out ... we know its a root because
# f(z) = y == f(z) - y = 0 ... so we know a valid quotient without remainder exists due to the
# factor theorem)
# ... which they would only be able to compute if they know f(x), the verifier then checks
# f(tau) - y = q(tau) (x - z) [verify_open]
def prove_open(coeffs, z, setup):
    """Return (y, pi) with y = f(z), pi = q(τ). where q(X) = (f(X) - y) / (X - z)"""
    y = poly.eval_poly(coeffs, z)

    divisor = [F.mod(-z), 1]          # X - z
    dividend = poly.sub_poly(coeffs, [y])  # f(X) - y
    q, r = poly.div_poly(dividend, divisor)
    assert r == [0]                   # y must equal f(z)
    pi = poly.eval_poly(q, setup["tau"])

    return y, pi

def verify_open(commitment, z, y, pi, setup):
    """Check C - y == pi * (tau - z)."""
    lhs = F.sub(commitment, y)
    rhs = F.mul(pi, F.sub(setup["tau"], z))
    return lhs == rhs
