from domain import DOMAIN
import poly


def trace_column_values(circuit, col):
    """col 0 = s_mul, 1 = a, 2 = b, 3 = c"""
    return circuit.column(col)


def trace_column_poly(circuit, col):
    return poly.interpolate(DOMAIN, trace_column_values(circuit, col))


def trace_polynomials(circuit):
    return {
        "s": trace_column_poly(circuit, 0),
        "a": trace_column_poly(circuit, 1),
        "b": trace_column_poly(circuit, 2),
        "c": trace_column_poly(circuit, 3),
    }