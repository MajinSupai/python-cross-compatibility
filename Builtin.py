import Cross

if Cross.PRE_CHECKED[Cross.PY2]:
    import itertools
    

@Cross.chooseOS
def keys(adict):
    if PY3:
        return adict.keys()

    else:
        return adict.iterkeys()

@Cross.chooseOS
def values(adict):
    if PY3:
        return adict.values()

    else:
        return adict.itervalues()

@Cross.chooseOS
def items(adict):
    if PY3:
        return adict.items()

    else:
        return adict.iteritems()


ORIG_ZIP = zip

@Cross.chooseOS

def zip(*args):
    if PY3:
        return ORIG_ZIP(*args)

    else:
        return itertools.izip(*args)
