import field as F
from circuit import Circuit
from layout import WIRE_IDS, row_col_from_placement


def build_witness(x, y):
    gx = F.mod(x)
    gy = F.mod(y)

    if F.mul(gx, gx) != gy:
        raise ValueError("invalid witness values")

    wire_values = {0: gx, 1: gy}
    circuit = Circuit()

    for placement, wire_id in enumerate(WIRE_IDS):
        if wire_id >= 0:
            row, col = row_col_from_placement(placement)
            circuit.set_data_cell(row, col, wire_values[wire_id])

    circuit.set_selector(0, 1)
    return circuit, gy