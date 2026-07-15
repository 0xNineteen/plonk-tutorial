from copy_constraints import check_public_inputs
from copy_poly import check_copies_on_domain
from gates_poly import check_gates_on_domain
from quotient import (
    all_constraints,
    check_constraint_quotients,
    constraint_bundle,
    constraint_polys,
    constraint_quotients,
)


def check_witness(circuit, public_inputs, *, use_quotient=True):
    if use_quotient:
        bundle = constraint_bundle(circuit)
        constraints_ok = check_constraint_quotients(bundle)
    else:
        constraints_ok = check_gates_on_domain(circuit) and check_copies_on_domain(circuit)
    return constraints_ok and check_public_inputs(circuit, public_inputs)