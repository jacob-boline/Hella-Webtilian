#!/bin/bash
# s3_upload_helper.sh
# Helper script to upload pre-generated srcsets to S3
#
# Prerequisites:
# - AWS CLI installed: https://aws.amazon.com/cli/
# - AWS credentials configured: aws configure
#
# Usage:
#   ./s3_upload_helper.sh

set -e

BUCKET_NAME="${AWS_BUCKET_NAME:?AWS_STORAGE_BUCKET_NAME is not set}"
REGION="${AWS_S3_REGION_NAME:?AWS_S3_REGION_NAME is not set}"
MEDIA_PREFIX="${AWS_PUBLIC_MEDIA_LOCATION:?AWS_PUBLIC_MEDIA_LOCATION is not set}"

# Colored Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Hella-Webtilian S3 Upload Helper${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if bucket name is set
if [ "$BUCKET_NAME" = "YOUR_BUCKET_NAME" ]; then
    echo -e "${RED}Error: Please update BUCKET_NAME in this script${NC}"
    exit 1
fi

echo -e "Bucket: ${GREEN}${BUCKET_NAME}${NC}"
echo -e "Region: ${GREEN}${REGION}${NC}"
echo -e "Media prefix: ${GREEN}${MEDIA_PREFIX}${NC}"
echo ""

# Function to upload directory with progress
upload_directory() {
    local source_dir=$1
    local s3_path=$2
    local description=$3

    if [ ! -d "$source_dir" ]; then
        echo -e "${YELLOW}Warning: Directory not found: ${source_dir}${NC}"
        echo "Skipping..."
        echo ""
        return
    fi

    echo -e "${GREEN}Uploading: ${description}${NC}"
    echo "From: $source_dir"
    echo "To: s3://${BUCKET_NAME}/${s3_path}"

    aws s3 sync "$source_dir" "s3://${BUCKET_NAME}/${s3_path}" \
        --region "$REGION" \
        --content-type "image/webp" \
        --cache-control "max-age=31536000" \
        --exclude "*.DS_Store" \
        --exclude "__pycache__/*" \
        --delete

    echo -e "${GREEN}✓ Complete${NC}"
    echo ""
}

# Upload Post Hero Images
echo -e "${YELLOW}=== POST HERO IMAGES ===${NC}"
echo "Expected local structure:"
echo "  posts/hero/<original-images>       (e.g., <hash>.jpg)"
echo "  posts/hero/opt/<variants>          (e.g., <hash>-640w.webp)"
echo ""

# Ask for local media directory
read -p "Enter path to your local media directory (or press Enter to skip): " MEDIA_DIR

if [ ! -z "$MEDIA_DIR" ]; then
    # Upload original hero images
    if [ -d "$MEDIA_DIR/posts/hero" ]; then
        # Upload only image files from posts/hero/, excluding opt subdirectory
        find "$MEDIA_DIR/posts/hero" -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" \) -print0 | while IFS= read -r -d '' file; do
            filename=$(basename "$file")
            aws s3 cp "$file" "s3://${BUCKET_NAME}/${MEDIA_PREFIX}/posts/hero/$filename" \
                --region "$REGION" \
                --cache-control "max-age=31536000"
            echo "✓ Uploaded: posts/hero/$filename"
        done
    fi

    # Upload hero variants
    upload_directory \
        "$MEDIA_DIR/posts/hero/opt" \
        "${MEDIA_PREFIX}/posts/hero/opt" \
        "Post hero variants"
fi

# Upload Carousel Images
echo -e "${YELLOW}=== CAROUSEL IMAGES (About Section) ===${NC}"
echo "Expected local structure:"
echo "  hr_about/<original-images>          (e.g., slide-01.jpg)"
echo "  hr_about/opt_webp/<variants>        (e.g., slide-01-640w.webp)"
echo ""

if [ ! -z "$MEDIA_DIR" ]; then
    # Upload original carousel images
    if [ -d "$MEDIA_DIR/hr_about" ]; then
        find "$MEDIA_DIR/hr_about" -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" \) -print0 | while IFS= read -r -d '' file; do
            filename=$(basename "$file")
            aws s3 cp "$file" "s3://${BUCKET_NAME}/${MEDIA_PREFIX}/hr_about/$filename" \
                --region "$REGION" \
                --cache-control "max-age=31536000"
            echo "✓ Uploaded: hr_about/$filename"
        done
    fi

    # Upload carousel variants
    upload_directory \
        "$MEDIA_DIR/hr_about/opt_webp" \
        "${MEDIA_PREFIX}/hr_about/opt_webp" \
        "Carousel image variants"
fi

# Upload Product Images
echo -e "${YELLOW}=== PRODUCT VARIANT IMAGES ===${NC}"
echo "Expected local structure:"
echo "  variants/<original-images>          (e.g., product-red.jpg)"
echo "  variants/opt_webp/<variants>        (e.g., product-red-256w.webp)"
echo ""

if [ ! -z "$MEDIA_DIR" ]; then
    # Upload original product images
    if [ -d "$MEDIA_DIR/variants" ]; then
        find "$MEDIA_DIR/variants" -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" \) -print0 | while IFS= read -r -d '' file; do
            filename=$(basename "$file")
            aws s3 cp "$file" "s3://${BUCKET_NAME}/${MEDIA_PREFIX}/variants/$filename" \
                --region "$REGION" \
                --cache-control "max-age=31536000"
            echo "✓ Uploaded: variants/$filename"
        done
    fi

    # Upload product variants
    upload_directory \
        "$MEDIA_DIR/variants/opt_webp" \
        "${MEDIA_PREFIX}/variants/opt_webp" \
        "Product image variants"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Upload Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Test URLs (replace with actual filenames):"
echo -e "  Post hero: https://${BUCKET_NAME}.s3.${REGION}.amazonaws.com/${MEDIA_PREFIX}/posts/hero/opt/<filename>-640w.webp"
echo -e "  Carousel: https://${BUCKET_NAME}.s3.${REGION}.amazonaws.com/${MEDIA_PREFIX}/hr_about/opt_webp/<filename>-640w.webp"
echo -e "  Product: https://${BUCKET_NAME}.s3.${REGION}.amazonaws.com/${MEDIA_PREFIX}/variants/opt_webp/<filename>-256w.webp"
echo ""

# List uploaded files
echo -e "${YELLOW}Would you like to list the uploaded files? (y/n)${NC}"
read -p "> " LIST_FILES

if [ "$LIST_FILES" = "y" ] || [ "$LIST_FILES" = "Y" ]; then
    echo ""
    echo -e "${GREEN}Listing S3 contents:${NC}"
    aws s3 ls "s3://${BUCKET_NAME}/${MEDIA_PREFIX}/" --recursive --human-readable --summarize
fi

echo ""
echo -e "${GREEN}Done!${NC}"

