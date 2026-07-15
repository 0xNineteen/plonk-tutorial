import field as F
from circuit import Circuit


def gate_mul(a, b, c, s):
    return F.mul(s, F.sub(F.mul(a, b), c))


def check_trace(circuit: Circuit):
    for row in circuit.trace:
        if gate_mul(row[1], row[2], row[3], row[0]) != 0:
            return False
    return True