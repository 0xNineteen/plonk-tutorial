import field as F
from circuit import Circuit
from layout import NUM_PLACEMENTS, PUBLIC_WIRES, WIRE_IDS, row_col_from_placement


def value_at_placement(circuit: Circuit, placement):
    row, col = row_col_from_placement(placement)
    return circuit.cell(row, col)


def placement_values(circuit: Circuit):
    return [
        value_at_placement(circuit, p) if WIRE_IDS[p] >= 0 else 0
        for p in range(NUM_PLACEMENTS)
    ]


def check_wire_ids(circuit: Circuit):
    for wire_id in set(WIRE_IDS):
        if wire_id < 0:
            continue
        placements = [p for p, wid in enumerate(WIRE_IDS) if wid == wire_id]
        if len(placements) < 2:
            continue
        vals = [value_at_placement(circuit, p) for p in placements]
        if any(v != vals[0] for v in vals):
            return False
    return True


def check_public_inputs(circuit: Circuit, public_inputs):
    for k, wire_id in enumerate(PUBLIC_WIRES):
        placement = WIRE_IDS.index(wire_id)
        if value_at_placement(circuit, placement) != public_inputs[k]:
            return False
    return True