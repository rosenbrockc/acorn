"""Methods for analyzing the fit and predict methods of regressors and
classifiers, sometimes specific to the algorithm.
"""
from acorn import msg
_classifiers = ['sklearn.svm.classes.SVC']
"""list: fqdn's of classifying machines in `sklearn`.
"""
_regressors = ['sklearn.svm.classes.SVR']
"""list: fqdn's of regressing machines in `sklearn`.
"""

_machines = {}
"""dict: keys are :func:`id` memory addresses of machines for which we have
*already* logged a fit routine. Values are a tuple of (machine, X, y) for the
fitting call. This allows us to access information about the fitting data sets
for prediction scoring later on.
"""
_splits = {}
"""dict: keys are :func:`id` memory addresses of the `X_test` matrix from
calling :func:`~sklearn.cross_validation.train_test_split`. Values are the tuple
returned by that method.
"""
auto_predict = True
"""bool: when True, analysis *will* automatically perform a predict on `Xtrain`
and `ytrain` to see how well it matches the training data.
"""
auto_print = True
"""bool: when True, scores *will* be printed to console for every analysis.
"""

def set_auto_predict(auto_predict_):
    """Sets whether the analysis routine automatically runs a predict on the
    *training* data whenever a fit is performed to score the machine on
    reproducing training data (useful for measuring over-fitting).

    Args:
        auto-predict_ (bool): when True, analysis *will* automatically perform a
          predict on `Xtrain` and `ytrain` to see how well it matches the training
          data.
    """
    global auto_predict
    auto_predict = auto_predict_

def set_auto_print(auto_print_):
    """Sets whether the scores calculated by the analysis routines will be
    automatically printed to the console/notebook. Since analysis performs the
    standard checks against machines, this output can replace some of the normal
    checks a human would perform.

    Args:
        auto_print_ (bool): when True, scores *will* be printed to console for every
          analysis.
    """
    global auto_print
    auto_print = auto_print_
    
def stash_split(fqdn, result, *argl, **argd):
    """Stashes the split between training and testing sets so that it can be
    used later for automatic scoring of the models in the log.
    """
    global _splits
    if fqdn == "sklearn.cross_validation.train_test_split":
        key = id(result[1])
        _splits[key] = result

    #We don't actually want to return anything for the analysis; we are using it
    #as a hook to save pointers to the dataset split so that we can easily
    #analyze performance later on.
    return None

def _machine_fqdn(machine):
    """Returns the FQDN of the given learning machine.
    """
    from acorn.logging.decoration import _fqdn
    if hasattr(machine, "__class__"):
        return _fqdn(machine.__class__, False)
    else: # pragma: no cover
        #See what FQDN can get out of the class instance.
        return _fqdn(machine)    
    
def isclassifier(machine):
    """Returns True if the specified class instance of a learning machine is a
    classifier. This is performed based on a name lookup of the fqdn.
    """
    mfqdn = _machine_fqdn(machine)
    return mfqdn in _classifiers    

def isregressor(machine):
    """Returns True if the specified class instance of a learning machine is a
    regressor. This is performed based on a name lookup of the fqdn.
    """
    mfqdn = _machine_fqdn(machine)
    return mfqdn in _regressors

def fit(fqdn, result, *argl, **argd):
    """Analyzes the result of a generic fit operation performed by `sklearn`.

    Args:
        fqdn (str): full-qualified name of the method that was called.
        result: result of calling the method with `fqdn`.
        argl (tuple): positional arguments passed to the method call.
        argd (dict): keyword arguments passed to the method call.
    """
    #Check the arguments to see what kind of data we are working with, then
    #choose the appropriate function below to return the analysis dictionary.
    #The first positional argument will be the instance of the machine that was
    #used. Check its name against a list.
    global _machines
    out = None
    if len(argl) > 0:
        machine = argl[0]
        #We save pointers to the machine that was just fit so that we can figure
        #out later what training data was used for analysis purposes.
        key = id(machine)
        _machines[key] = (machine, argl[0], argl[1])
        
        if isclassifier(machine):
            out = classify_fit(fqdn, result, *argl, **argd)
        elif isregressor(machine):
            out = regress_fit(fqdn, result, *argl, **argd)
        
    return out

def predict(fqdn, result, *argl, **argd):
    """Analyzes the result of a generic predict operation performed by
    `sklearn`.

    Args:
        fqdn (str): full-qualified name of the method that was called.
        result: result of calling the method with `fqdn`.
        argl (tuple): positional arguments passed to the method call.
        argd (dict): keyword arguments passed to the method call.
    """
    #Check the arguments to see what kind of data we are working with, then
    #choose the appropriate function below to return the analysis dictionary.
    out = None
    if len(argl) > 0:
        machine = argl[0]
        if isclassifier(machine):
            out = classify_predict(fqdn, result, None, *argl, **argd)
        elif isregressor(machine):
            out = regress_predict(fqdn, result, None, *argl, **argd)
    return out

def _do_auto_predict(machine, X, *args):
    """Performs an automatic prediction for the specified machine and returns
    the predicted values.
    """
    if auto_predict and hasattr(machine, "predict"):
        return machine.predict(X)

def _generic_fit(fqdn, result, scorer, yP=None, *argl, **argd):
    """Performs the generic fit tests that are common to both classifier and
    regressor; uses `scorer` to score the predicted values given by the machine
    when tested against its training set.

    Args:
    scorer (function): called on the result of `machine.predict(Xtrain,
      ytrain)`.
    """
    out = None
    if len(argl) > 0:
        machine = argl[0]
        out = {}
        if hasattr(machine, "best_score_"):
            out["score"] = machine.best_score_
            
        #With fitting it is often useful to know how well the fitting set was
        #matched (by trying to predict a score on it). We can do this
        #automatically and show the result to the user.
        yL = _do_auto_predict(*argl[0:2])
        yscore = scorer(fqdn, yL, yP, *argl, **argd)
        if yscore is not None:
            out.update(yscore)

    return out
    
def classify_fit(fqdn, result, *argl, **argd):
    """Analyzes the result of a classification algorithm's fitting. See also
    :func:`fit` for explanation of arguments.
    """
    if len(argl) > 2:
        #Usually fit is called with fit(machine, Xtrain, ytrain).
        yP = argl[2]
    out = _generic_fit(fqdn, result, classify_predict, yP, *argl, **argd)
    return out

def _percent_match(result, out, yP=None, *argl):
    """Returns the percent match for the specified prediction call; requires
    that the data was split before using an analyzed method.

    Args:
        out (dict): output dictionary to save the result to.
    """
    if len(argl) > 1:
        if yP is None:
            Xt = argl[1]
            key = id(Xt)
            if key in _splits:
                yP = _splits[key][3]
                
        if yP is not None:
            import math
            out["%"] = round(1.-sum(abs(yP - result))/float(len(result)), 3)

def classify_predict(fqdn, result, yP=None, *argl, **argd):
    """Analyzes the result of a classification algorithm's prediction. See also
    :func:`predict` for explanation of arguments.

    .. todo: update the metric to be useful.

    """
    #For now, just to make sure the machinery works correctly, let's return the
    #percentage correct. This is a terrible metric in practice.
    out = {}
    _percent_match(result, out, yP, *argl)

    if auto_print:
        msg.okay(out, -1)

    return out

def regress_fit(fqdn, result, *argl, **argd):
    """Analyzes the result of a regression algorithm's fitting. See also
    :func:`fit` for explanation of arguments.
    """
    if len(argl) > 2:
        yP = argl[2]
    out = _generic_fit(fqdn, result, regress_predict, yP, *argl, **argd)
    return out

def regress_predict(fqdn, result, yP=None, *argl, **argd):
    """Analyzes the result of a regression algorithm's prediction. See also
    :func:`predict` for explanation of arguments.

    .. todo: update the metric to be useful.

    """
    #For now, just to make sure the machinery works correctly, let's return the
    #percentage correct. This is a terrible metric in practice.
    out = {}
    _percent_match(result, out, yP, *argl)

    if auto_print:
        msg.okay(out, -1)

    return out
