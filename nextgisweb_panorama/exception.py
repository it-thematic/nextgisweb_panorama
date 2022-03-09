from nextgisweb.core.exception import UserException

from .util import _


__all__ = [
    'SceneNotFound',
]


class SceneNotFound(UserException):
    title = _("Panorama not found")
    message = _("Panorama with id = %d was not found in feature with id = %d.")
    detail = _("The panorama may have been deleted or an error in the address.")
    http_status_code = 404

    def __init__(self, resource_id, feature_id, panorama_id):
        super().__init__(
            message=self.__class__.message % (panorama_id, feature_id),
            data=dict(resource_id=resource_id, feature_id=feature_id, attachment_id=panorama_id))
