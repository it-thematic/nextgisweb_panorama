# -*- coding: utf-8 -*-
from nextgisweb.component import Component, require

from .model import Base
from .util import COMP_ID


class PanoramaComponent(Component):
    identity = COMP_ID
    metadata = Base.metadata

    @require('feature_layer')
    def initialize(self):
        from . import extension # NOQA
        from .plugins import PanoramaPlugin

    def setup_pyramid(self, config):
        from . import view, api
        view.setup_pyramid(self, config)
        api.setup_pyramid(self, config)


def pkginfo():
    return dict(components=dict(
        panorama='nextgisweb_panorama'))


def amd_packages():
    return (
        ('ngw-panorama', 'nextgisweb_panorama:amd/ngw-panorama'),
    )
