from domain import DOMAIN
from encode import trace_polynomials
import poly


def gate_constraint_poly(circuit):
    trace = trace_polynomials(circuit)
    return poly.mul_poly(
        trace["s"],
        poly.sub_poly(poly.mul_poly(trace["a"], trace["b"]), trace["c"]),
    )


def eval_gate_constraint_at(circuit, x, g_poly=None):
    if g_poly is None:
        g_poly = gate_constraint_poly(circuit)
    return poly.eval_poly(g_poly, x)


def check_gates_on_domain(circuit):
    return poly.poly_zero_on_domain(gate_constraint_poly(circuit), DOMAIN)