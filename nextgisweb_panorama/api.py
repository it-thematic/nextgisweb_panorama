# -*- coding: utf-8 -*-
import json

from io import BytesIO

from PIL import Image
from pyramid.response import Response

from nextgisweb.env import env
from nextgisweb.feature_attachment.exif import EXIF_ORIENTATION_TAG, ORIENTATIONS
from nextgisweb.feature_layer.exception import FeatureNotFound
from nextgisweb.models import DBSession
from nextgisweb.resource import DataScope, resource_factory

from .exception import SceneNotFound
from .model import FeaturePanorama, FeatureScene


def scene_or_not_found(resource_id, feature_id, scene_id):
    """ Return panorama filtered by id or raise AttachmentNotFound exception. """

    obj = FeatureScene.filter_by(
        resource_id=resource_id,
        feature_id=feature_id,
        id=scene_id
    ).one_or_none()

    if obj is None:
        raise SceneNotFound(resource_id, feature_id, scene_id)

    return obj


def normalize_feature_panorama(request, feature):
    """
    Нормализация конфига для отображения панорамы объекта

    * Нормализация url-адресов
    """
    pfiles = {
        pfile.keyname: pfile
        for pfile in FeatureScene.filter_by(resource_id=feature.layer.id, feature_id=feature.id)
    }

    pins = FeaturePanorama.filter_by(resource_id=feature.layer.id, feature_id=feature.id).one_or_none()
    if pins is None:
        return

    panorama = pins.panorama
    for scene in panorama:
        scene["panorama"] = request.route_url('feature_panorama.scene.item.image',
                                              id=feature.layer.id,
                                              fid=feature.id,
                                              sid=pfiles[scene['id']].id
                                              )
        if not scene.setdefault("position", list()):
            scene["position"] = pfiles[scene['id']].panorama
    return panorama


def sc_get(resource, request):
    request.resource_permission(DataScope.read)

    query = FeatureScene.filter_by(
        resource_id=request.matchdict['id'],
        feature_id=request.matchdict['fid']
    )

    result = [itm.serialize() for itm in query]
    for itm in result:
        itm['url'] = request.route_url('feature_panorama.scene.item',
                                       id=request.matchdict['id'],
                                       fid=request.matchdict['fid'],
                                       sid=itm['id']
                                       )
    return Response(json.dumps(result), content_type='application/json', charset='utf-8')


def si_get(resource, request):
    request.resource_permission(DataScope.read)

    scene = scene_or_not_found(request.matchdict['id'], request.matchdict['fid'], request.matchdict['sid'])
    if scene is None:
        result = None
    else:
        result = scene.serialize()
        result['image'] = request.route_url('feature_panorama.scene.item.image',
                                            id=request.matchdict['id'],
                                            fid=request.matchdict['fid'],
                                            sid=request.matchdict['sid']
                                            )
    return Response(json.dumps(result), content_type='application/json', charset='utf-8')


def image(resource, request):
    request.resource_permission(DataScope.read)

    scene = scene_or_not_found(resource.id, request.matchdict['fid'], request.matchdict['sid'])
    image = Image.open(env.file_storage.filename(scene.fileobj))
    ext = image.format

    exif = None
    try:
        exif = image._getexif()
    except Exception:
        pass

    if exif is not None:
        otag = exif.get(EXIF_ORIENTATION_TAG)
        if otag in (3, 6, 8):
            orientation = ORIENTATIONS.get(otag)
            image = image.transpose(orientation.degrees)

    if 'size' in request.GET:
        image.thumbnail(
            list(map(int, request.GET['size'].split('x'))),
            Image.ANTIALIAS)

    buf = BytesIO()
    image.save(buf, ext)
    buf.seek(0)

    return Response(body_file=buf, content_type=scene.mime_type)


def pget(resource, request):
    request.resource_permission(DataScope.read)

    feature_id = int(request.matchdict['fid'])
    query = resource.feature_query()
    query.filter_by(id=feature_id)
    query.limit(1)

    feature = None
    for f in query():
        feature = f

    return Response(
        json.dumps(normalize_feature_panorama(request, feature)),
        content_type='application/json',
        charset='utf-8')


def ppost(resource, request):
    request.resource_permission(DataScope.write)

    feature_id = int(request.matchdict['fid'])
    query = resource.feature_query()
    query.filter_by(id=feature_id)
    query.limit(1)

    feature = None
    for f in query():
        feature = f

    if feature is None:
        raise FeatureNotFound(resource.id, feature_id)

    data = request.json_body

    for feature_panorama_file in data.setdefault('files', []):
        obj = FeatureScene(resource_id=feature.layer.id, feature_id=feature.id)
        obj.deserialize(feature_panorama_file)
        DBSession.add(obj)

    obj = FeaturePanorama(resource_id=feature.layer.id, feature_id=feature.id, panorama=data.get('panorama', None))
    DBSession.add(obj)

    DBSession.flush()

    return Response(
        json.dumps(obj.panorama),
        content_type='application/json',
        charset='utf-8')


def setup_pyramid(comp, config):
    panoramaurl = '/api/resource/{id}/feature/{fid}/panorama/'
    scenecurl = '/api/resource/{id}/feature/{fid}/scene/'
    sceneiurl = '/api/resource/{id}/feature/{fid}/scene/{sid}'

    config.add_route(
        'feature_panorama.scene.collection', scenecurl,
        factory=resource_factory) \
        .add_view(sc_get, request_method='GET')

    config.add_route(
        'feature_panorama.scene.item', sceneiurl,
        factory=resource_factory) \
        .add_view(si_get, request_method='GET')

    config.add_route(
        'feature_panorama.scene.item.image',
        sceneiurl + '/image',
        factory=resource_factory) \
        .add_view(image)

    config.add_route(
        'feature_panorama.item', panoramaurl,
        factory=resource_factory) \
        .add_view(pget, request_method='GET') \
        .add_view(ppost, request_method='POST')
