# hr_storage/storage_backends.py

import os

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
    default_acl = "public-read"
    file_overwrite = True
    location = settings.MEDIA_URL

    def get_created_time(self, name):
        pass

    def get_accessed_time(self, name):
        pass

    def path(self, name):
        pass


class StaticStorage(S3StaticStorage):
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
    default_acl = "public-read"
    file_overwrite = True
    location = settings.STATIC_URL

    def get_created_time(self, name):
        pass

    def get_accessed_time(self, name):
        pass

    def path(self, name):
        pass


class PrivateMediaStorage(S3Boto3Storage):
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = "private"

    def get_created_time(self, name):
        pass

    def get_accessed_time(self, name):
        pass

    def path(self, name):
        pass
