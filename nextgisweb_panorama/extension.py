# -*- coding: utf-8 -*-
from json import dumps, loads
from math import atan2

from nextgisweb.feature_layer.extension import FeatureExtension
from nextgisweb.models import DBSession

from .model import FeatureScene, FeaturePanorama


@FeatureExtension.registry.register
class FeaturePanoramaExtension(FeatureExtension):
    identity = 'panorama'

    editor_widget = "ngw-panorama/EditorWidget"

    def serialize(self, feature):
        result = dict(
            scenes=[],
            panorama=[]
        )

        scene_instances = FeatureScene.filter_by(
            resource_id=self.layer.id,
            feature_id=feature.id
        )
        scene_dict = {scene.keyname: scene for scene in scene_instances}
        scenes = [itm.serialize() for itm in scene_instances]
        result['scenes'] = scenes

        panorama_instance = FeaturePanorama.filter_by(
            resource_id=self.layer.id,
            feature_id=feature.id
        ).one_or_none()
        if not panorama_instance:
            return result

        panorama = panorama_instance.panorama
        if panorama:
            for scene in panorama:
                if not scene.get('position'):
                    scene['position'] = scene_dict[scene['id']].position
        else:
            panorama = [
                {
                    'id': scene.keyname,
                    'name': scene.display_name,
                    'position': scene.position
                } for scene in scene_instances
            ]
            for i in range(len(panorama)):
                if i == 0:
                    panorama[i]['links'] = [{'nodeId': panorama[i+1]['id']}]
                elif i == len(panorama)-1:
                    panorama[i]['links'] = [{'nodeId': panorama[i-1]['id']}]
                else:
                    panorama[i]['links'] = [{'nodeId': panorama[i-1]['id']}, {'nodeId': panorama[i+1]['id']}]

        for scene in panorama:
            if len(scene.setdefault("links", [])) == 0:
                continue
            next_point = scene_dict[scene["links"][int(len(scene["links"]) != 1)]["nodeId"]].serialize()
            # latitude = x, longitude = y
            dy = next_point["position"][0] - scene["position"][0]
            dx = next_point["position"][1] - scene["position"][1]
            pan = atan2(dy, dx)
            scene.setdefault("sphereCorrection", dict())["pan"] = -pan

        result['panorama'] = panorama

        return result

    def deserialize(self, feature, data):
        if data is None:
            data = dict()

        rest = dict()
        for fp in FeatureScene.filter_by(
            resource_id=feature.layer.id,
            feature_id=feature.id
        ):
            rest[fp.id] = fp

        for itm in data['scenes']:
            if 'id' in itm:
                obj = rest[itm['id']]
                del rest[itm['id']]
            else:
                obj = FeatureScene(
                    resource_id=feature.layer.id,
                    feature_id=feature.id
                ).persist()

            obj.deserialize(itm)

        for fa in rest.values():
            DBSession.delete(fa)

        panorama_instance = FeaturePanorama.filter_by(
            resource_id=feature.layer.id,
            feature_id=feature.id
        ).one_or_none()

        if data.get('panorama', None):
            panorama = loads(data['panorama'])

            if panorama:
                if panorama_instance is None:
                    FeaturePanorama(resource_id=feature.layer.id,
                                    feature_id=feature.id,
                                    panorama=panorama
                                    ).persist()
                else:
                    panorama_instance.panorama = panorama
            else:
                if panorama_instance:
                    DBSession.delete(panorama_instance)
