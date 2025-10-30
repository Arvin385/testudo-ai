"""Helper tools that wrap the JupiterP API for schedule planning workflows.

Importing this package ensures Python treats ``scheduler`` as a package so the
tool modules can reference each other with relative imports (for example,
``from .jupiterp_client import build_client``).  Additional shared exports can
be added here later if you want to expose a simplified public surface.
"""
