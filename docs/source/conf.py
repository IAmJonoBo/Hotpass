"""
Sphinx configuration file for the Hotpass documentation.

This file sets up paths, project metadata, and Sphinx extensions.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

PROJECT = "Hotpass"
AUTHOR = "Hotpass Team"
RELEASE = "0.1.0"
copyright_notice = f"{datetime.now():%Y}, {AUTHOR}"
globals()["copyright"] = copyright_notice

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

AUTOSUMMARY_GENERATE = True
NAPOLEON_GOOGLE_DOCSTRING = True
NAPOLEON_NUMPY_DOCSTRING = True

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
]

MYST_HEADING_ANCHORS = 2

templates_path = ["_templates"]
exclude_patterns = ["_build"]

HTML_THEME = "furo"
html_static_path = ["_static"]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
