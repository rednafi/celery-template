from pathlib import Path
from konfik import Konfik

BASE_DIR = Path('__file__').parent
ENV_PATH = BASE_DIR / '.env'

config = Konfik(ENV_PATH).config

