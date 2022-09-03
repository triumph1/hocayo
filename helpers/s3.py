import urllib
from urllib.parse import urljoin

from django.conf import settings

from helpers.consts import VMS_FILE_PREFIX


def get_s3_review_image_bucket_url(img):
    if not img:
        return ""
    if img.startswith(VMS_FILE_PREFIX):
        return img.replace(VMS_FILE_PREFIX, settings.VMS_S3_FILE_URL_PREFIX)
    return urljoin(settings.REVIEW_IMAGE_HOST, urllib.parse.quote(img.encode("utf-8")))
