"""Shared loader and paths for the Brokkr 3D font families.

Every tool is run as   python -I tools/<tool>.py <family> [tool arguments ...]
for example            python -I tools/build_ttf.py sans
<family> is a folder in families/ (sans = Brokkr Sans 3D; serif = Brokkr Serif 3D later). It is taken off the
argument list here, so each tool sees only its own arguments. Without it, "sans" is used.
"""
import importlib.util, os, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
FAMILIES = sorted(d for d in os.listdir(os.path.join(ROOT, "families"))
                  if os.path.exists(os.path.join(ROOT, "families", d, "glyphs.py")))
SLUG = sys.argv.pop(1) if len(sys.argv) > 1 and sys.argv[1] in FAMILIES else "sans"


def load(path, name):
    """Load a module from a file once per run (shared between tools)."""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return sys.modules[name]


def tool(name):
    return load(os.path.join(TOOLS, name + ".py"), "b3dtool_" + name)


def family(slug=None):
    """The family's main module (families/<slug>/glyphs.py): metrics, names, build(), layout(), kerning."""
    slug = slug or SLUG
    return load(os.path.join(ROOT, "families", slug, "glyphs.py"), "b3dfamily_" + slug)


def out(*parts):
    """A folder inside the repo, created if needed."""
    p = os.path.join(ROOT, *parts); os.makedirs(p, exist_ok=True)
    return p
