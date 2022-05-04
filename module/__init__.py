"""
module
模块文件夹，可在该文件夹下放置支持的 Saya 插件，将在启动时自动加载
"""
import os
import pathlib

__all__ = []

for path in pathlib.Path(os.path.dirname(__file__)).iterdir():
    if (path.is_dir() or path.name.endswith(".py")) and not path.name.startswith("_"):
        __all__.append(path.stem)
