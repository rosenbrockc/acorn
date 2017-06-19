"""Functions for implementing diff cascades for re-definitions of function calls
and markdown cells.
"""
from six import string_types
def cascade(sequence, full=False):
    """Restores a sequence of string definitions using the first entry as the
    original and then applying a series of :func:`~acorn.logging.diff.restore`
    calls.

    Args:
        sequence (list): of results returned by
          :func:`~acorn.logging.diff.compress`, except that the first entry should
          be a list of string entries for the very first instance.
        full (bool): when True, return all the intermediate entries as well;
          otherwise they are not stored in memory and only the final entry in
          the list is returned.
    """
    if len(sequence) == 1:
        return sequence[0]
    
    left = sequence[0]
    if full:
        intermed = []
    for cdiff in sequence[1:]:
        right = restore(cdiff, left)
        if full:
            intermed.append(right)
        left = right

    return left

def restore(cdiff, a):
    """Restores the full text of either the edited text using the
    compressed diff.

    Args:
        cdiff (dict): compressed diff returned by
          :func:`~acorn.logging.diff.compress`. 
        a (str or list): *original* string or list of strings to use as a
          reference to restore the edited version.
    """
    left = a.splitlines(1) if isinstance(a, string_types) else a
    lrest = []
    iline = 0
    
    for i, line in enumerate(left):
        if iline not in cdiff:
            lrest.append("  " + line)
            iline += 1
        else:
            cs = [l[0] for l in cdiff[iline]]
            add = cs.count('+') - cs.count('-')
            lrest.extend(cdiff[iline])
            iline += add + 1
            
    for i in sorted(cdiff.keys()):
        if i >= len(left):
            lrest.extend(cdiff[i])

    from difflib import restore
    return list(restore(lrest, 2))
    
def compress(a, b):
    """Performs the *compressed* diff of `a` and `b` such that the original
    contents of the :func:`difflib.ndiff` call can be reconstructed using
    :func:`~acorn.logging.diff.restore`.

    Args:
        a (str or list): *original* string or list of strings to diff.
        b (str or list): *edited* string or list of strings to diff.
    """
    from difflib import ndiff
    left = a.splitlines(1) if isinstance(a, string_types) else a
    right = b.splitlines(1) if isinstance(b, string_types) else b
    ldiff = list(ndiff(left, right))
    
    result = {}
    latest = None   
    combo = None
    icombo = 0
    iorig = 0
    
    for i, line in enumerate(ldiff):
        cs = [l[0] for l in ldiff[i:min((i+4, len(ldiff)))]]
        if cs[0] != ' ':
            #Initialize a new entry in the diff list.
            if latest is None:
                latest = iorig
                result[latest] = []
                
            #We have to be careful. At a minimum, there may be a '-' or a '+' when the lines are 
            #completely added or deleted. When they are *altered*, then we also expect one or
            #more '?' lines showing the differences.
            if combo is None:
                if cs[0] == '-':
                    #Check whether the next lines have one of these combinations:
                    if (len(cs) >=3 and cs[1] == '+' and cs[2] == '?'):
                        combo = 3
                    elif (len(cs) >= 4 and cs[1] == '?' and cs[2] == '+'
                          and cs[3] == '?'):
                        combo = 4
                    else:
                        #This is a stand-alone deletion.
                        combo = 1
                elif cs[0] == '+':
                    #This is for the stand-alone addition.
                    combo = 1
                
            if icombo < combo:
                result[latest].append(line)
                icombo += 1
            
            if icombo == combo:
                if combo > 1:
                    latest = None
                combo = None
                icombo = 0
                if cs[0] != '+':
                    iorig += 1
        else:
            latest = None
            iorig += 1

    return result
    
