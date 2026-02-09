# hr_storage/storage_backends.py

import os

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", getattr(settings, "AWS_STORAGE_BUCKET_NAME", None))
    default_acl = None
    file_overwrite = False
    location = getattr(settings, "AWS_PUBLIC_MEDIA_LOCATION", "media")

    def get_created_time(self, name):
        raise NotImplementedError

    def get_accessed_time(self, name):
        raise NotImplementedError

    def path(self, name):
        raise NotImplementedError


class StaticStorage(S3StaticStorage):
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", getattr(settings, "AWS_STORAGE_BUCKET_NAME", None))
    default_acl = None
    file_overwrite = True
    location = getattr(settings, "AWS_STATIC_LOCATION", "static")

    def get_created_time(self, name):
        raise NotImplementedError

    def get_accessed_time(self, name):
        raise NotImplementedError

    def path(self, name):
        raise NotImplementedError


class PrivateMediaStorage(S3Boto3Storage):
    location = getattr(settings, "AWS_PRIVATE_MEDIA_LOCATION", "private")
    default_acl = "private"

    def get_created_time(self, name):
        raise NotImplementedError

    def get_accessed_time(self, name):
        raise NotImplementedError

    def path(self, name):
        raise NotImplementedError
