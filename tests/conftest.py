"""Configuração mínima — só prepara o path e força SQLite."""
import os
os.environ["DATABASE_URL"] = ""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
