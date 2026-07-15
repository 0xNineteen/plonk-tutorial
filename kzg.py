import encode
import poly
import quotient
from copy_poly import copy_constraint_poly
from gates_poly import gate_constraint_poly

def commit_trace_columns(circuit, setup) -> dict:
    polys = encode.trace_polynomials(circuit)
    poly_commits = {}
    for k, v in polys.items():
        # C_a, C_b, ...
        poly_commits["C_" + k] = poly.eval_poly(v, setup["tau"])
    return poly_commits

def commit_quotients(circuit, setup) -> dict:
    bundle = quotient.constraint_bundle(circuit)
    quotient_polys = {
        "qg": bundle["gate_quotient"],
        "qc": bundle["copy_quotient"],
    }
    quotient_commits = {}
    for k, v in quotient_polys.items():
        # C_qg, C_qc
        quotient_commits["C_" + k] = poly.eval_poly(v, setup["tau"])
    return quotient_commits

def commit_constraint_polys(circuit, srs) -> dict:
    tau = srs["tau"]
    return {
        "C_g": poly.eval_poly(gate_constraint_poly(circuit), tau),
        "C_cp": poly.eval_poly(copy_constraint_poly(circuit), tau),
    }


def commit_witness_bundle(circuit, setup) -> dict:
    trace_commits = commit_trace_columns(circuit, setup)
    quotient_commits = commit_quotients(circuit, setup)

    witness_bundle = {}
    for k, v in trace_commits.items():
        witness_bundle[k] = v
    for k, v in quotient_commits.items():
        witness_bundle[k] = v
    return witness_bundle


def commit_all(circuit, srs) -> dict:
    """Trace columns, quotients, and constraint polynomials."""
    return {
        **commit_witness_bundle(circuit, srs),
        **commit_constraint_polys(circuit, srs),
    }
