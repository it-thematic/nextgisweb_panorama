# coding: utf-8
from nextgisweb.webmap.plugin import __all__ as base_plugins

from .panorama import PanoramaPlugin

__all__ = base_plugins + ['PanoramaPlugin']
