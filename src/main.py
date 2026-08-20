import os
import sys

# Добавляем корневую директорию в PYTHONPATH для импортов src.* | Add root dir to PYTHONPATH for src.* imports
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.app import Game

Game().run()