import numpy as np

import field as F

N_TRACE_LENGTH = 4
NUM_DATA_COLS = 3


class Circuit:
    trace: np.ndarray

    def __init__(self):
        self.trace = np.zeros((N_TRACE_LENGTH, NUM_DATA_COLS + 1))

    def cell(self, row, col):
        """Field element at trace[row, col]; col 0 = selector, 1..3 = data."""
        return F.mod(int(self.trace[row, col]))

    def column(self, col):
        return [self.cell(i, col) for i in range(N_TRACE_LENGTH)]

    def set_row(self, i, x, y):
        """Lesson 01 helper: active mul row with a = b = x."""
        self.trace[i] = [1, x, x, y]

    def set_selector(self, row, s_mul):
        self.trace[row][0] = s_mul

    def set_data_cell(self, row, col, value):
        assert 1 <= col <= NUM_DATA_COLS
        self.trace[row][col] = value