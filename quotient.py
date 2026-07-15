from circuit import N_TRACE_LENGTH
from layout import NUM_PLACEMENTS
from gates_poly import gate_constraint_poly
from copy_poly import copy_constraint_poly
import poly


def _quotient_ok(constraint, quotient, remainder, n):
    if any(c != 0 for c in remainder):
        return False
    Z = poly.vanishing_poly(n)
    return poly.eql(poly.mul_poly(Z, quotient), constraint)


def constraint_bundle(circuit):
    """Compute gate/copy constraints and quotients in one pass."""
    G = gate_constraint_poly(circuit)
    C = copy_constraint_poly(circuit)
    Zg = poly.vanishing_poly(N_TRACE_LENGTH)
    Zc = poly.vanishing_poly(NUM_PLACEMENTS)
    Qg, Rg = poly.div_poly(G, Zg)
    Qc, Rc = poly.div_poly(C, Zc)
    return {
        "gate": G,
        "copy": poly.trim(C),
        "gate_quotient": poly.trim(Qg),
        "copy_quotient": poly.trim(Qc),
        "gate_remainder": Rg,
        "copy_remainder": Rc,
    }


def check_constraint_quotients(bundle):
    return (
        _quotient_ok(
            bundle["gate"], bundle["gate_quotient"], bundle["gate_remainder"], N_TRACE_LENGTH
        )
        and _quotient_ok(
            bundle["copy"], bundle["copy_quotient"], bundle["copy_remainder"], NUM_PLACEMENTS
        )
    )


def gate_quotient_poly(circuit):
    bundle = constraint_bundle(circuit)
    if any(c != 0 for c in bundle["gate_remainder"]):
        raise ValueError("constraint does not vanish on domain")
    return bundle["gate_quotient"]


def copy_quotient_poly(circuit):
    bundle = constraint_bundle(circuit)
    if any(c != 0 for c in bundle["copy_remainder"]):
        raise ValueError("constraint does not vanish on domain")
    return bundle["copy_quotient"]


def check_gate_quotient(circuit) -> bool:
    bundle = constraint_bundle(circuit)
    return _quotient_ok(
        bundle["gate"], bundle["gate_quotient"], bundle["gate_remainder"], N_TRACE_LENGTH
    )


def check_copy_quotient(circuit) -> bool:
    bundle = constraint_bundle(circuit)
    return _quotient_ok(
        bundle["copy"], bundle["copy_quotient"], bundle["copy_remainder"], NUM_PLACEMENTS
    )


def constraint_polys(circuit):
    bundle = constraint_bundle(circuit)
    return {"gate": bundle["gate"], "copy": bundle["copy"]}


def constraint_quotients(circuit):
    bundle = constraint_bundle(circuit)
    return {"gate": bundle["gate_quotient"], "copy": bundle["copy_quotient"]}


def all_constraints(circuit):
    return constraint_bundle(circuit)