from __future__ import (absolute_import, division, print_function)

from functools import partial
from logging import getLogger
import numpy as np


def sanity_checks(config):
    pass


def _do_special(d1, d2, operation=None):
    return operation(np.asarray([d1, d2]), axis=0)


_available_operators = {
    'sum': partial(_do_special, operation=np.sum),
    '+': partial(_do_special, operation=np.sum),
    'mean': partial(_do_special, operation=np.mean),
    'avg': partial(_do_special, operation=np.mean),
    # http://www.rapidtables.com/math/symbols/Basic_Math_Symbols.htm has a x with a - on top, but nobody likes UTF-8
    'x': partial(_do_special, operation=np.mean),
    'sub': np.subtract,
    '-': np.subtract,
    'subtract': np.subtract,
    'mul': np.multiply,
    '*': np.multiply,
    'multiply': np.multiply,
    'div': np.true_divide,
    '/': np.true_divide,
    'divide': np.true_divide
}


def get_available_operators():
    return _available_operators.keys()


def execute(sample, flat, dark, config, indices):
    opr = config.func.imopr[-1]

    from mantidimaging.core.imopr import helper
    getLogger(__name__).info("Running IMOPR with operation {0}".format(opr))

    i1, i2 = helper.handle_indices(indices)

    res = _available_operators[opr](sample[i1], sample[i2])

    from mantidimaging.core.imopr import visualiser as vis
    vis.show_image(res, block=True)

    return res
