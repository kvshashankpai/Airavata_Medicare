import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{ROOT / "medcare.db"}')
MODEL_PROVIDER = os.getenv('MODEL_PROVIDER', 'local')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
