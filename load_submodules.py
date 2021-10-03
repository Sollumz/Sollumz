# Development: Reload submodules
from types import ModuleType
import importlib
from . import codewalker_xml
from . import game_objects
import Sollumz
packages = [Sollumz, codewalker_xml, game_objects]

def load_submodules():
    # print("Reloading submodules...")
    for package in packages:
        importlib.reload(package)
        # print(f"Reloaded module: '{package}'")

