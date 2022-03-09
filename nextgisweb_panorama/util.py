# -*- coding: utf-8 -*-
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from nextgisweb.i18n import trstring_factory


COMP_ID = 'panorama'
_ = trstring_factory(COMP_ID)


def _get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0

    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return round(degrees + minutes + seconds, 6)


def get_lat_coord(geotags):
    return _get_decimal_from_dms(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])


def get_lon_coord(geotags):
    return _get_decimal_from_dms(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])


def get_alt_coord(geotags):
    return float(geotags['GPSAltitude'])


def get_exif(filename):
    exif = Image.open(filename)._getexif()
    result = dict()
    if exif is not None:
        for key, value in exif.items():
            name = TAGS.get(key, key)
            result[name] = exif.get(key)

    if 'GPSInfo' in result:
        for key in result['GPSInfo'].keys():
            name = GPSTAGS.get(key, key)
            result[name] = result['GPSInfo'][key]
    return result
