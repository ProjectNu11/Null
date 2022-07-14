from pathlib import Path
from .. import config

if not Path(config.path.data, "library").is_dir():
    Path(config.path.data, "library").mkdir(exist_ok=True)

from .blacklist import blacklist
from .interval import interval
