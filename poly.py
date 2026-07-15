import field as F

# Coefficients are low degree first: [c0, c1, c2] = c0 + c1*X + c2*X^2


def eval_poly(coeffs, x):
    result = 0
    for c in reversed(coeffs):
        result = F.add(c, F.mul(result, x))
    return result


def add_poly(c1s, c2s):
    if len(c1s) < len(c2s):
        c1s, c2s = c2s, c1s
    c3 = c1s.copy()
    for i, c2 in enumerate(c2s):
        c3[i] = F.add(c3[i], c2)
    return c3


def sub_poly(c1s, c2s):
    if len(c1s) < len(c2s):
        c1s, c2s = c2s, c1s
    c3 = c1s.copy()
    for i, c2 in enumerate(c2s):
        c3[i] = F.sub(c3[i], c2)
    return c3


def mul_poly(c1s, c2s):
    c3 = [0] * (len(c1s) + len(c2s) - 1)
    for i1, c1 in enumerate(c1s):
        for i2, c2 in enumerate(c2s):
            c3[i1 + i2] = F.add(c3[i1 + i2], F.mul(c1, c2))
    return c3


def trim(coeffs):
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    return coeffs

def eql(c1, c2):
    return trim(list(c1)) == trim(list(c2))

def interpolate(xs, ys):
    """Lagrange interpolation: unique poly f with deg(f) < n and f(x_i) = y_i."""
    assert len(xs) == len(ys)
    n = len(xs)
    result = [0]

    for i in range(n):
        li = [1]
        denom = 1
        for j in range(n):
            if j != i:
                li = mul_poly(li, [F.mod(-xs[j]), 1])
                denom = F.mul(denom, F.sub(xs[i], xs[j]))

        scale = F.div(ys[i], denom)
        li = [F.mul(c, scale) for c in li]
        result = add_poly(result, li)

    return trim(result)


def poly_zero_on_domain(coeffs, domain):
    return all(eval_poly(coeffs, x) == 0 for x in domain)

def vanishing_poly(n):
    """coeffs for X^n - 1"""
    coeffs = [0] * (n + 1)
    coeffs[0] = F.mod(-1)
    coeffs[n] = 1
    return coeffs

def div_poly(dividend, divisor):
    """Polynomial long division in F_p[X]; coeffs low-degree first.

    Returns (quotient, remainder) with
        dividend = divisor * quotient + remainder
    and deg(remainder) < deg(divisor) (or remainder = 0).
    """
    dividend = trim(list(dividend))
    divisor = trim(list(divisor))

    if len(divisor) == 1 and divisor[0] == 0:
        raise ZeroDivisionError("division by zero polynomial")

    if len(dividend) == 1 and dividend[0] == 0:
        return [0], [0]

    if len(dividend) < len(divisor):
        return [0], dividend

    if len(divisor) == 1:
        c = divisor[0]
        return trim([F.div(a, c) for a in dividend]), [0]

    quotient = [0] * (len(dividend) - len(divisor) + 1)

    while len(dividend) >= len(divisor) and not (len(dividend) == 1 and dividend[0] == 0):
        deg_diff = len(dividend) - len(divisor)
        lead_q = F.div(dividend[-1], divisor[-1])
        quotient[deg_diff] = F.add(quotient[deg_diff], lead_q)

        for i in range(len(divisor)):
            dividend[i + deg_diff] = F.sub(
                dividend[i + deg_diff], F.mul(lead_q, divisor[i])
            )

        dividend = trim(dividend)

    remainder = dividend if dividend else [0]
    return trim(quotient), remainder


def quotient_by_vanishing(f_coeffs, n):
    Z = vanishing_poly(n)
    Q, R = div_poly(f_coeffs, Z)
    if any(c != 0 for c in R):
        raise ValueError("constraint does not vanish on domain")
    return trim(Q)
