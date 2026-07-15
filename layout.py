from circuit import N_TRACE_LENGTH, NUM_DATA_COLS

NUM_PLACEMENTS = N_TRACE_LENGTH * NUM_DATA_COLS

ACTIVE_WIRE_IDS = [0, 0, 1]
WIRE_IDS = ACTIVE_WIRE_IDS + [-1] * (NUM_PLACEMENTS - len(ACTIVE_WIRE_IDS))

PUBLIC_WIRES = (1,)


def placement_index(row, col):
    return row * NUM_DATA_COLS + (col - 1)


def row_col_from_placement(i):
    return i // NUM_DATA_COLS, i % NUM_DATA_COLS + 1