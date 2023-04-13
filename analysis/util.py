
def load_metric(filename):
    """ Load plan text counts into a Counter object."""
    metric = {}
    with open(filename) as f:
        for line in f.readlines():
            w,v = line.rstrip('\n').split()
            metric[w] = float(v)
    return metric 

def read_util(file_path):
    with open(file_path, "r") as f:
        terms = [line.strip("\n").split("#")[0] for line in f.readlines()]
    terms = [term for term in terms if term != ""]
    return terms

