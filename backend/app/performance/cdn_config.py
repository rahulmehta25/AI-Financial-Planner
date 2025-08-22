"""
CDN Configuration and Static Asset Optimization

Implements CDN integration with CloudFlare/AWS CloudFront including:
- Asset versioning and cache busting
- Image optimization and responsive serving
- Compression and minification
- Geographic distribution
- Edge caching strategies
"""

import hashlib
import gzip
import brotli
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import mimetypes
import logging

from PIL import Image
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CDNConfig:
    """CDN configuration for different providers"""
    
    # CloudFlare configuration
    CLOUDFLARE = {
        "api_url": "https://api.cloudflare.com/client/v4",
        "cache_levels": {
            "aggressive": {"browser_ttl": 31536000, "edge_ttl": 2678400},
            "standard": {"browser_ttl": 14400, "edge_ttl": 86400},
            "simplified": {"browser_ttl": 1800, "edge_ttl": 7200}
        },
        "polish": "lossy",  # Image optimization
        "minify": {
            "css": True,
            "html": True,
            "js": True
        },
        "rocket_loader": True,  # Async JS loading
        "mirage": True,  # Lazy loading for images
        "webp": True  # Auto WebP conversion
    }
    
    # AWS CloudFront configuration
    CLOUDFRONT = {
        "price_class": "PriceClass_100",  # Use all edge locations
        "compress": True,
        "cache_behaviors": {
            "images": {
                "path_pattern": "/images/*",
                "target_origin_id": "S3-images",
                "viewer_protocol_policy": "redirect-to-https",
                "cache_policy_id": "658327ea-f89e-4fab-a63d-7e88639e58f6",  # Managed-CachingOptimized
                "response_headers_policy_id": "67f7725c-6f97-4210-82d7-5512b31e9d03"  # SecurityHeadersPolicy
            },
            "api": {
                "path_pattern": "/api/*",
                "target_origin_id": "API-Backend",
                "viewer_protocol_policy": "https-only",
                "cache_policy_id": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",  # Managed-CachingDisabled
                "origin_request_policy_id": "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"  # Managed-CORS-S3Origin
            },
            "static": {
                "path_pattern": "/static/*",
                "target_origin_id": "S3-static",
                "viewer_protocol_policy": "redirect-to-https",
                "cache_policy_id": "658327ea-f89e-4fab-a63d-7e88639e58f6",
                "compress": True
            }
        },
        "custom_error_responses": [
            {
                "error_code": 404,
                "response_code": 404,
                "response_page_path": "/404.html",
                "error_caching_min_ttl": 300
            },
            {
                "error_code": 503,
                "response_code": 503,
                "response_page_path": "/maintenance.html",
                "error_caching_min_ttl": 0
            }
        ]
    }


class StaticAssetOptimizer:
    """
    Static asset optimization for CDN delivery
    """
    
    def __init__(
        self,
        cdn_provider: str = "cloudfront",
        s3_bucket: str = None,
        cloudfront_distribution_id: str = None,
        enable_compression: bool = True,
        enable_image_optimization: bool = True
    ):
        self.cdn_provider = cdn_provider
        self.s3_bucket = s3_bucket
        self.cloudfront_distribution_id = cloudfront_distribution_id
        self.enable_compression = enable_compression
        self.enable_image_optimization = enable_image_optimization
        
        # Initialize AWS clients if using CloudFront
        if cdn_provider == "cloudfront":
            self.s3_client = boto3.client('s3')
            self.cloudfront_client = boto3.client('cloudfront')
        
        # Asset versioning cache
        self.asset_versions: Dict[str, str] = {}
    
    def calculate_asset_hash(self, file_path: Path) -> str:
        """Calculate hash for asset versioning"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()[:8]
    
    def version_asset(self, file_path: Path) -> str:
        """
        Generate versioned asset URL
        
        Args:
            file_path: Path to asset file
            
        Returns:
            Versioned URL with cache-busting hash
        """
        # Calculate or retrieve hash
        if str(file_path) not in self.asset_versions:
            self.asset_versions[str(file_path)] = self.calculate_asset_hash(file_path)
        
        hash_value = self.asset_versions[str(file_path)]
        
        # Generate versioned filename
        stem = file_path.stem
        suffix = file_path.suffix
        versioned_name = f"{stem}.{hash_value}{suffix}"
        
        return versioned_name
    
    def compress_asset(
        self,
        file_path: Path,
        compression: str = "gzip"
    ) -> Tuple[bytes, str]:
        """
        Compress asset for CDN delivery
        
        Args:
            file_path: Path to asset file
            compression: Compression type (gzip, brotli)
            
        Returns:
            Compressed content and encoding type
        """
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if compression == "brotli":
            compressed = brotli.compress(content, quality=11)
            encoding = "br"
        else:  # gzip
            compressed = gzip.compress(content, compresslevel=9)
            encoding = "gzip"
        
        # Only use compression if it reduces size
        if len(compressed) < len(content):
            return compressed, encoding
        return content, None
    
    def optimize_image(
        self,
        image_path: Path,
        sizes: List[int] = [320, 640, 768, 1024, 1366, 1920],
        formats: List[str] = ["webp", "jpeg"],
        quality: int = 85
    ) -> Dict[str, Dict[str, Path]]:
        """
        Optimize images for responsive delivery
        
        Args:
            image_path: Path to original image
            sizes: List of widths to generate
            formats: Image formats to generate
            quality: Compression quality
            
        Returns:
            Dictionary of generated images by size and format
        """
        img = Image.open(image_path)
        optimized = {}
        
        for size in sizes:
            if size > img.width:
                continue
            
            # Calculate proportional height
            ratio = size / img.width
            height = int(img.height * ratio)
            
            # Resize image
            resized = img.resize((size, height), Image.Resampling.LANCZOS)
            
            optimized[size] = {}
            
            for fmt in formats:
                # Generate filename
                output_name = f"{image_path.stem}_{size}w.{fmt}"
                output_path = image_path.parent / output_name
                
                # Save optimized image
                save_kwargs = {"quality": quality, "optimize": True}
                
                if fmt == "webp":
                    save_kwargs["method"] = 6  # Slowest/best compression
                    resized.save(output_path, "WEBP", **save_kwargs)
                elif fmt == "jpeg":
                    save_kwargs["progressive"] = True
                    resized.save(output_path, "JPEG", **save_kwargs)
                
                optimized[size][fmt] = output_path
        
        return optimized
    
    async def upload_to_cdn(
        self,
        file_path: Path,
        cdn_path: str,
        cache_control: str = "public, max-age=31536000",
        content_type: str = None
    ) -> str:
        """
        Upload file to CDN
        
        Args:
            file_path: Local file path
            cdn_path: CDN destination path
            cache_control: Cache control header
            content_type: MIME type
            
        Returns:
            CDN URL
        """
        if self.cdn_provider == "cloudfront":
            return await self._upload_to_s3(file_path, cdn_path, cache_control, content_type)
        else:
            # Implement other CDN providers
            raise NotImplementedError(f"CDN provider {self.cdn_provider} not implemented")
    
    async def _upload_to_s3(
        self,
        file_path: Path,
        s3_key: str,
        cache_control: str,
        content_type: str = None
    ) -> str:
        """Upload file to S3 for CloudFront"""
        # Determine content type
        if not content_type:
            content_type, _ = mimetypes.guess_type(str(file_path))
        
        # Prepare metadata
        metadata = {
            'CacheControl': cache_control,
            'ContentType': content_type or 'application/octet-stream'
        }
        
        # Compress if applicable
        if self.enable_compression and file_path.suffix in ['.js', '.css', '.html', '.json']:
            content, encoding = self.compress_asset(file_path)
            if encoding:
                metadata['ContentEncoding'] = encoding
        else:
            with open(file_path, 'rb') as f:
                content = f.read()
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=content,
                **metadata
            )
            
            # Return CloudFront URL
            return f"https://d{self.cloudfront_distribution_id}.cloudfront.net/{s3_key}"
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    async def invalidate_cdn_cache(self, paths: List[str]):
        """
        Invalidate CDN cache for specific paths
        
        Args:
            paths: List of paths to invalidate
        """
        if self.cdn_provider == "cloudfront":
            try:
                response = self.cloudfront_client.create_invalidation(
                    DistributionId=self.cloudfront_distribution_id,
                    InvalidationBatch={
                        'Paths': {
                            'Quantity': len(paths),
                            'Items': paths
                        },
                        'CallerReference': str(datetime.now().timestamp())
                    }
                )
                logger.info(f"CloudFront invalidation created: {response['Invalidation']['Id']}")
            except ClientError as e:
                logger.error(f"Failed to create invalidation: {e}")
                raise
    
    def generate_srcset(
        self,
        image_optimized: Dict[str, Dict[str, Path]],
        cdn_base_url: str
    ) -> str:
        """
        Generate srcset attribute for responsive images
        
        Args:
            image_optimized: Dictionary of optimized images
            cdn_base_url: Base CDN URL
            
        Returns:
            srcset string for HTML
        """
        srcset_parts = []
        
        for size, formats in image_optimized.items():
            if 'webp' in formats:
                path = formats['webp']
            elif 'jpeg' in formats:
                path = formats['jpeg']
            else:
                continue
            
            cdn_url = f"{cdn_base_url}/{path.name}"
            srcset_parts.append(f"{cdn_url} {size}w")
        
        return ", ".join(srcset_parts)
    
    def generate_picture_element(
        self,
        image_optimized: Dict[str, Dict[str, Path]],
        cdn_base_url: str,
        alt_text: str = "",
        lazy: bool = True
    ) -> str:
        """
        Generate picture element for optimal image delivery
        
        Args:
            image_optimized: Dictionary of optimized images
            cdn_base_url: Base CDN URL
            alt_text: Alt text for image
            lazy: Enable lazy loading
            
        Returns:
            HTML picture element
        """
        picture_html = '<picture>\n'
        
        # WebP sources
        webp_srcset = []
        for size, formats in image_optimized.items():
            if 'webp' in formats:
                cdn_url = f"{cdn_base_url}/{formats['webp'].name}"
                webp_srcset.append(f"{cdn_url} {size}w")
        
        if webp_srcset:
            picture_html += f'  <source type="image/webp" srcset="{", ".join(webp_srcset)}">\n'
        
        # JPEG fallback
        jpeg_srcset = []
        default_src = None
        for size, formats in image_optimized.items():
            if 'jpeg' in formats:
                cdn_url = f"{cdn_base_url}/{formats['jpeg'].name}"
                jpeg_srcset.append(f"{cdn_url} {size}w")
                if not default_src:
                    default_src = cdn_url
        
        loading_attr = 'loading="lazy"' if lazy else ''
        picture_html += f'  <img src="{default_src}" srcset="{", ".join(jpeg_srcset)}" alt="{alt_text}" {loading_attr}>\n'
        picture_html += '</picture>'
        
        return picture_html


class EdgeCacheStrategy:
    """
    Edge caching strategies for CDN
    """
    
    @staticmethod
    def get_cache_headers(
        content_type: str,
        is_authenticated: bool = False,
        is_personalized: bool = False
    ) -> Dict[str, str]:
        """
        Get optimal cache headers based on content type
        
        Args:
            content_type: MIME type of content
            is_authenticated: Whether content requires authentication
            is_personalized: Whether content is personalized
            
        Returns:
            Dictionary of cache headers
        """
        headers = {}
        
        # Static assets - long cache
        if content_type.startswith(('image/', 'font/')):
            headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            headers['Vary'] = 'Accept-Encoding'
        
        # CSS/JS - versioned cache
        elif content_type in ['text/css', 'application/javascript']:
            headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            headers['Vary'] = 'Accept-Encoding'
        
        # HTML - shorter cache
        elif content_type == 'text/html':
            if is_authenticated:
                headers['Cache-Control'] = 'private, no-cache, must-revalidate'
                headers['Vary'] = 'Cookie, Accept-Encoding'
            else:
                headers['Cache-Control'] = 'public, max-age=3600, s-maxage=86400'
                headers['Vary'] = 'Accept-Encoding'
        
        # API responses
        elif content_type == 'application/json':
            if is_personalized:
                headers['Cache-Control'] = 'private, no-cache'
                headers['Vary'] = 'Authorization, Accept-Encoding'
            else:
                headers['Cache-Control'] = 'public, max-age=60, s-maxage=300'
                headers['Vary'] = 'Accept, Accept-Encoding'
        
        # Add security headers
        headers['X-Content-Type-Options'] = 'nosniff'
        headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        return headers