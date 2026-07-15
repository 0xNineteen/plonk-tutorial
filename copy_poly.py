from copy_constraints import placement_values
from domain import PLACEMENT_DOMAIN
from permutation import SIGMA, permute_values
import poly


def witness_poly(circuit):
    return poly.interpolate(PLACEMENT_DOMAIN, placement_values(circuit))


def permuted_witness_poly(circuit):
    w = placement_values(circuit)
    w_sigma = permute_values(w, SIGMA)
    return poly.interpolate(PLACEMENT_DOMAIN, w_sigma)


def copy_constraint_poly(circuit):
    w = placement_values(circuit)
    w_sigma = permute_values(w, SIGMA)
    return poly.trim(
        poly.sub_poly(
            poly.interpolate(PLACEMENT_DOMAIN, w),
            poly.interpolate(PLACEMENT_DOMAIN, w_sigma),
        )
    )


def check_copies_on_domain(circuit):
    return poly.poly_zero_on_domain(copy_constraint_poly(circuit), PLACEMENT_DOMAIN)