# S3 media configuration (production)

Enable durable uploads + generated variants in S3 while leaving static files on WhiteNoise.

## Required environment variables

- `USE_S3_MEDIA=true` (enables S3 media in production settings)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_REGION_NAME` (or `AWS_REGION`)

## Optional environment variables

- `AWS_S3_ENDPOINT_URL` (for non-AWS S3 endpoints)
- `AWS_S3_CUSTOM_DOMAIN` (custom CDN/domain for the bucket)
- `AWS_S3_ADDRESSING_STYLE` (defaults to `virtual`)
- `AWS_PUBLIC_MEDIA_LOCATION` (defaults to `media`)
- `AWS_PRIVATE_MEDIA_LOCATION` (defaults to `private`)

## Notes

- Static files continue to be served by WhiteNoise.
- `MEDIA_URL` is derived from the bucket, region, and/or custom domain when `USE_S3_MEDIA=true`.

## Debounced media batcher (optional)

Enable debounced batching for media uploads (S3 media only) by setting:

- `ENABLE_DEBOUNCED_IMAGE_BATCHER=true`
- `HEROKU_APP_NAME`
- `HEROKU_API_TOKEN`

This uses the `imgbatch` process type and scales it to 1 on upload, then back to 0 after processing.
