# coding: utf-8

from nextgisweb.webmap.plugin.base import WebmapLayerPlugin

@WebmapLayerPlugin.registry.register
class PanoramaPlugin(WebmapLayerPlugin):

    @classmethod
    def is_layer_supported(cls, layer, webmap):
        return ("ngw-panorama/plugins/Panorama", dict())
