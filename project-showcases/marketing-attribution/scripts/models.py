"""Transparent credit rules and a first-order absorbing Markov chain."""
from collections import Counter
from dataclasses import dataclass
import numpy as np

MODELS = ('First touch', 'Last touch', 'Linear', 'Position based', 'Time decay', 'Markov')

@dataclass
class Journey:
    channels: tuple
    times: tuple
    converted: bool
    value: float
    cookie: str = ''
    start: object = None

def rule_weights(channels, times, model, half_life=7):
    """Return per-event weights; repeated events may give a channel extra credit."""
    n = len(channels)
    if not n:
        return np.zeros(0)
    w = np.zeros(n)
    if model == 'First touch':
        w[0] = 1
    elif model == 'Last touch':
        w[-1] = 1
    elif model == 'Linear':
        w[:] = 1 / n
    elif model == 'Position based':
        if n == 1:
            w[0] = 1
        elif n == 2:
            w[:] = .5
        else:
            w[0] = w[-1] = .4
            w[1:-1] = .2 / (n - 2)
    elif model == 'Time decay':
        age = np.array([(times[-1] - t).total_seconds() / 86400 for t in times])
        w = np.exp2(-age / half_life)
        w /= w.sum()
    else:
        raise ValueError(model)
    return w

def collapse(channels):
    return tuple(c for i, c in enumerate(channels) if i == 0 or c != channels[i-1])

def transition_counts(journeys, channels, collapsed=True):
    """START, channels, CONVERSION, NULL; no converted-only training."""
    n = len(channels)
    counts = np.zeros((n+3, n+3))
    ix = {c: i+1 for i,c in enumerate(channels)}
    for j in journeys:
        seq = collapse(j.channels) if collapsed else j.channels
        path = [0] + [ix[c] for c in seq] + [n+1 if j.converted else n+2]
        for a,b in zip(path, path[1:]):
            counts[a,b] += 1
    return counts

def absorption(matrix, n):
    q = matrix[:n+1, :n+1]
    r = matrix[:n+1, n+1]
    return float(np.linalg.solve(np.eye(n+1)-q, r)[0])

def markov_from_counts(counts, n):
    p = np.zeros_like(counts, dtype=float)
    totals = counts.sum(axis=1)
    np.divide(counts, totals[:,None], out=p, where=totals[:,None] > 0)
    for i in range(n+1):
        if totals[i] == 0:
            p[i,n+2] = 1
    p[n+1,n+1] = p[n+2,n+2] = 1
    base = absorption(p, n)
    effects = []
    for c in range(1,n+1):
        removed = p.copy()
        removed[:,n+2] += removed[:,c]
        removed[:,c] = 0
        removed[c,:] = 0
        removed[c,n+2] = 1
        without = absorption(removed,n)
        effects.append(max(0., 1-without/base) if base > 0 else 0.)
    effects = np.array(effects)
    share = effects/effects.sum() if effects.sum() else np.zeros(n)
    return share, effects, base, p

def allocations(journeys, channels):
    ix = {c:i for i,c in enumerate(channels)}
    count = {m:np.zeros(len(channels)) for m in MODELS}
    value = {m:np.zeros(len(channels)) for m in MODELS[:-1]}
    conversions = sum(j.converted for j in journeys)
    for j in journeys:
        if not j.converted or not j.channels:
            continue
        for m in MODELS[:-1]:
            weights = rule_weights(j.channels,j.times,m)
            for c,w in zip(j.channels,weights):
                count[m][ix[c]] += w
                value[m][ix[c]] += w*j.value
    counts = transition_counts(journeys,channels)
    shares,effects,base,p = markov_from_counts(counts,len(channels))
    count['Markov'] = shares*conversions
    return count, value, {'shares':shares,'effects':effects,'base':base,'matrix':p,'counts':counts}

def bootstrap_markov(journeys, channels, repetitions=300, seed=20261007):
    """Multinomial resampling of path types equals resampling whole cookies."""
    types = Counter((collapse(j.channels), j.converted) for j in journeys)
    keys = list(types)
    n = len(channels)
    size = n+3
    ix = {c:i+1 for i,c in enumerate(channels)}
    features = np.zeros((len(keys), size*size))
    for k,(seq,converted) in enumerate(keys):
        path = [0]+[ix[c] for c in seq]+[n+1 if converted else n+2]
        for a,b in zip(path,path[1:]):
            features[k,a*size+b] += 1
    frequencies = np.array([types[k] for k in keys])
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(repetitions):
        weights = rng.multinomial(len(journeys),frequencies/frequencies.sum())
        counts = (weights@features).reshape(size,size)
        samples.append(markov_from_counts(counts,n)[0])
    return np.quantile(samples,[.025,.975],axis=0).T
