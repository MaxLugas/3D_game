import os
import sys

# Добавляем корневую директорию в PYTHONPATH для абсолютных импортов | Add root dir to PYTHONPATH for absolute imports
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import Game

Game().run()