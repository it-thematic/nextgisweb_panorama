# -*- coding: utf-8 -*-
import magic

from collections import OrderedDict
from shutil import copyfileobj

from nextgisweb import db
from nextgisweb.core.exception import ValidationError
from nextgisweb.env import env
from nextgisweb.file_storage import FileObj
from nextgisweb.resource import Resource
from nextgisweb.models import declarative_base

from .util import _, get_exif, get_lat_coord, get_lon_coord, get_alt_coord

Base = declarative_base(dependencies=('resource', 'feature_layer'))

mime_valid = [
    'image/jpeg'
]


def validate_mime(filename, buf):
    mime = magic.from_buffer(buf, mime=True)
    if mime not in mime_valid:
        raise ValidationError(_("File type \"%s\" not in valid mimes. %s.") % (filename, mime_valid))
    return mime


class FeatureScene(Base):
    __tablename__ = 'feature_panorama_scene'

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.ForeignKey(Resource.id), nullable=False)
    feature_id = db.Column(db.Integer, nullable=False)
    fileobj_id = db.Column(db.ForeignKey(FileObj.id), nullable=False)

    keyname = db.Column(db.Unicode, nullable=False)
    display_name = db.Column(db.Unicode, nullable=False)
    mime_type = db.Column(db.Unicode, nullable=False)

    position = db.Column(db.JSON, nullable=False)

    fileobj = db.relationship(FileObj, lazy='joined')

    resource = db.relationship(Resource, backref=db.backref(
        '__feature_panorama_files', cascade='all'))

    __table_args__ = (
        db.UniqueConstraint(resource_id, feature_id, keyname),
        db.UniqueConstraint(resource_id, feature_id, display_name),
    )

    def serialize(self):
        return OrderedDict((
            ('id', self.id),
            ('keyname', self.keyname),
            ('display_name', self.display_name),
            ('position', self.position)
        ))

    def deserialize(self, data):
        file_upload = data.get('file_upload')
        if file_upload is not None:
            srcfile, meta = env.file_upload.get_filename(file_upload['id'])
            with open(srcfile, 'rb') as fs:
                self.mime_type = validate_mime(file_upload['name'], fs.read(1024))
                fs.seek(0)
                self.fileobj = env.file_storage.fileobj(component='feature_panorama')
                dstfile = env.file_storage.filename(self.fileobj, makedirs=True)
                with open(dstfile, 'wb') as fd:
                    copyfileobj(fs, fd)

                exif = get_exif(srcfile)
                self.position = [get_lon_coord(exif), get_lat_coord(exif), get_alt_coord(exif)]
        self.keyname = data.get('keyname')
        self.display_name = data.get('display_name')


class FeaturePanorama(Base):
    __tablename__ = 'feature_panorama_panorama'

    resource_id = db.Column(db.ForeignKey(Resource.id), primary_key=True)
    feature_id = db.Column(db.Integer, primary_key=True)

    panorama = db.Column(db.JSON, nullable=False)

    resource = db.relationship(Resource, backref=db.backref(
        '__feature_panorama', cascade='all'))
