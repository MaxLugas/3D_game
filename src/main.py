import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH для импортов src.* | Add root dir to PYTHONPATH for src.* imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.app import Game

Game().run()