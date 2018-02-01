"""Run doctests on choices.py and helpers.py"""

import doctest
import sys
from . import choices, helpers

failures = 0

failures += doctest.testmod(m=choices, report=True)[0]
failures += doctest.testmod(m=helpers, report=True)[0]

if failures > 0:
    sys.exit(1)
