from layout import NUM_PLACEMENTS, WIRE_IDS


def build_sigma():
    """σ[p] = image of placement p under copy permutation."""
    sigma = list(range(NUM_PLACEMENTS))
    for w in set(WIRE_IDS):
        if w < 0:
            continue
        w_idxs = [i for i in range(NUM_PLACEMENTS) if WIRE_IDS[i] == w]
        if len(w_idxs) < 2:
            continue
        for i, w_idx in enumerate(w_idxs):
            sigma[w_idx] = w_idxs[(i + 1) % len(w_idxs)]
    return sigma


def permute_values(values, sigma):
    """out[p] = values[sigma[p]]"""
    return [values[sigma[p]] for p in range(len(values))]


SIGMA = build_sigma()