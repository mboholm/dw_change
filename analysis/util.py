
def load_metric(filename):
    """ Load plan text counts into a Counter object."""
    metric = {}
    with open(filename) as f:
        for line in f.readlines():
            w,v = line.rstrip('\n').split()
            metric[w] = float(v)
    return metric 
