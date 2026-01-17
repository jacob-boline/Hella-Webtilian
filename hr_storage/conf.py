# hr_storage/conf.py

import os

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_DEFAULT_ACL = 'public-read'

AWS_STATIC_LOCATION = "static"
AWS_PUBLIC_MEDIA_LOCATION = 'media'
AWS_PRIVATE_MEDIA_LOCATION = 'private'

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_STATIC_LOCATION}/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_PUBLIC_MEDIA_LOCATION}/'
DEFAULT_FILE_STORAGE = "hr_storage.storage_backends.PublicMediaStorage"
STATICFILES_STORAGE = "hr_storage.storage_backends.StaticStorage"

AWS_S3_REGION_NAME = 'us-east-2'
AWS_S3_ADDRESSING_STYLE = 'virtual'
AWS_QUERYSTRING_AUTH = False

AWS_S3_REGION = 'us-east-2'
