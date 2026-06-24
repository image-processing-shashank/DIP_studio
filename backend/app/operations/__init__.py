"""Importing this package registers every project's operations.

To add a new project (7..20): create p7_xxx.py with @operation-decorated
functions, then add one import line below. No other change is required;
the frontend renders it automatically from the catalog.
"""
from . import p1_explorer      # noqa: F401
from . import p2_enhancement   # noqa: F401
from . import p3_noise         # noqa: F401
from . import p4_edges         # noqa: F401
from . import p5_fourier       # noqa: F401
from . import p6_morphology    # noqa: F401
