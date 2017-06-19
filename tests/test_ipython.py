"""Tests ipython-specific notebook wrapping/logging behavior.
"""
import pytest
def test_loops():
    """Tests detection of loops in code that may be defined in an ipython
    notebook.
    """
    import ast
    from acorn.ipython import findloop
    #Test an explicit, top-level for loop.
    acode = """for i in range(1000):
    print(i)
"""
    assert findloop(ast.parse(acode))
    #Tests a top-level list comprehension
    listcomp = """
sequence = [e["c"] for e in taskdb.entities[pkey]]
"""
    assert findloop(ast.parse(listcomp))
    #Makes sure a regular assignment does *not* trigger.
    regassign = """state = ''.join(cascade(sequence))
matcher = SequenceMatcher(a=state, b=text)
"""
    assert not findloop(ast.parse(regassign))
    #Nested list comprehension in ternary IfExpr
    ternary = """[i for i in range(10)] if True else 0"""
    assert findloop(ast.parse(ternary))
    #Regular if statement with dict comprehension in the else.
    ifstate = """if True:
    print('cow')
else:
    {a: True for i in b}
"""
    assert findloop(ast.parse(ifstate))
    #Complex, multi-level code with nested loop.
    compcode="""global _cellid_map
if cellid not in _cellid_map:
    if ekey not in taskdb.entities:
        #Compute a new ekey if possible with the most similar markdown cell
        #in the database.
        possible = [k for k in taskdb.entities if k[0:3] == "nb-"]
        maxkey, maxvalue = None, 0.
        for pkey in possible:
            if ratio > maxvalue and ratio > 0.5:
                maxkey, maxvalue = pkey, ratio

        #We expect the similarity to be at least 0.5; otherwise we decide
        #that it is a new cell.
        if maxkey is not None:
            ekey = pkey
                            
    _cellid_map[cellid] = ekey
"""
    assert findloop(ast.parse(compcode))
    #Top-level while loop.
    wcode = """while True:
    if 1 > 2:
        print(3)
"""
    assert findloop(ast.parse(wcode))
    #Doesn't trigger for regular expressions without loops.
    noncode = """ekey = _cellid_map[cellid]        
entry = {
    "m": "md",
    "a": None,
    "s": time(),
    "r": None,
    "c": text,
}
record(ekey, entry, diff=True)
"""
    assert not findloop(ast.parse(noncode))
    #Does not trigger for function definitions.
    defcode = """def noloop():
    for i in range(10):
        print(2)
    else:
        print(3)
"""
    assert not findloop(ast.parse(defcode))
    #Does not trigger class definitions with nested loops.
    classcode = """class Cat(object):
    def __init__(self):
        while True:
            print(False)
"""
    assert not findloop(ast.parse(classcode))
