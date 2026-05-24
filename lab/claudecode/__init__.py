"""lab.claudecode — shim: canonical files live in UnseenUniversity.

Python searches TheIgors/lab/claudecode/ first; anything not found here
falls through to ~/dev/src/UnseenUniversity/lab/claudecode/ via __path__
extension.
"""

import os

_adc_cc = os.path.realpath(
    os.path.expanduser("~/dev/src/UnseenUniversity/lab/claudecode")
)
if os.path.isdir(_adc_cc) and _adc_cc not in __path__:
    __path__.append(_adc_cc)
