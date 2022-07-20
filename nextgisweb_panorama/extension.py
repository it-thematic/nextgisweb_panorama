# -*- coding: utf-8 -*-
from json import loads
from math import atan2, pi

from nextgisweb.feature_layer.extension import FeatureExtension
from nextgisweb.models import DBSession

from .model import FeatureScene, FeaturePanorama


def _add_sphere_correction(scene, next_scene, reverse=False):
    # latitude = x, longitude = y
    dy = next_scene["position"][0] - scene["position"][0]
    dx = next_scene["position"][1] - scene["position"][1]
    pan = atan2(dy, dx)
    if reverse:
        pan -= pi
    scene.setdefault("sphereCorrection", dict())["pan"] = -pan


def calculate_panorama_data(pano_data, scene_instance_dict, reverse=False):
    """Перевод входных данных в экземпляры модели"""
    # Если пришёл пустой список (может руками удалили или через API
    if not pano_data:
        pano_data = [
            {
                "id": scene.keyname,
                "name": scene.display_name,
                "position": scene.position
            } for k, scene in scene_instance_dict.items()
        ]
        for idx, scene in enumerate(pano_data):
            if idx == 0:
                scene["links"] = [{"nodeId": pano_data[idx + 1]["id"]}]
            elif idx == len(pano_data) - 1:
                scene["links"] = [{"nodeId": pano_data[idx - 1]["id"]}]
            else:
                scene["links"] = [{"nodeId": pano_data[idx - 1]["id"]}, {"nodeId": pano_data[idx + 1]["id"]}]
            next_scene = scene_instance_dict[scene["links"][int(len(scene["links"]) != 1)]["nodeId"]].serialize()
            _add_sphere_correction(scene, next_scene, reverse)

    else:
        # Если данные пришли
        for idx, scene in enumerate(pano_data):
            if not scene.get("position"):
                scene["position"] = scene_instance_dict[scene["id"]].position

            if len(scene["links"]) == 0:
                continue

            if scene.setdefault("sphereCorrection", dict()):
                continue

            if idx == len(pano_data) - 1:
                # Т.к. в последней сцене нет перехода на следующую точку,
                # то значение угла корректировки берётся из предыдущей сцены (читается продолжение прямой)
                scene["sphereCorrection"]["pan"] = pano_data[-2].setdefault("sphereCorrection", dict()).get("pan")
            else:
                next_scene = scene_instance_dict[scene["links"][int(len(scene["links"]) != 1)]["nodeId"]].serialize()
                _add_sphere_correction(scene, next_scene, reverse)
    return pano_data


def deserialize_pano_data(feature, data):
    if data is None:
        data = dict()

    rest = {fs.id: fs for fs in FeatureScene.filter_by(resource_id=feature.layer.id, feature_id=feature.id)}
    scenes = dict()
    for scene in data.get("scenes", list()):
        if "id" in scene:
            obj = rest[scene["id"]]
            del rest[scene["id"]]
        else:
            obj = FeatureScene(
                resource_id=feature.layer.id,
                feature_id=feature.id
            ).persist()
        obj.deserialize(scene)
        scenes[obj.keyname] = obj

    for fa in rest.values():
        DBSession.delete(fa)

    pano_data = calculate_panorama_data(data.get("panorama"), scenes, data.get("reverse", False))
    pano_instance = FeaturePanorama.filter_by(
        resource_id=feature.layer.id,
        feature_id=feature.id
    ).one_or_none()
    if pano_data:
        if pano_instance is None:
            FeaturePanorama(resource_id=feature.layer.id,
                            feature_id=feature.id,
                            panorama=pano_data
                            ).persist()
        else:
            pano_instance.panorama = pano_data
            pano_instance.persist()
    else:
        if pano_instance:
            DBSession.delete(pano_instance)


@FeatureExtension.registry.register
class FeaturePanoramaExtension(FeatureExtension):
    identity = "panorama"

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
        scenes = [itm.serialize() for itm in scene_instances]
        result["scenes"] = scenes

        panorama_instance = FeaturePanorama.filter_by(
            resource_id=self.layer.id,
            feature_id=feature.id
        ).one_or_none()
        if not panorama_instance:
            return result

        panorama = panorama_instance.panorama
        result["panorama"] = panorama

        return result

    def deserialize(self, feature, data):
        deserialize_pano_data(feature, data)
