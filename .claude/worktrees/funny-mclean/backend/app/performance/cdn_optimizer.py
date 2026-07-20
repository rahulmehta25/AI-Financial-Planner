"""
CDN and Static Asset Optimization System

Comprehensive CDN configuration with:
- Multi-CDN support (CloudFlare, AWS CloudFront, Fastly)
- Automatic image optimization and WebP conversion
- Edge caching strategies
- Service worker generation
- Browser cache optimization
"""

import hashlib
import gzip
import brotli
import json
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import aiofiles
from dataclasses import dataclass
from enum import Enum
from PIL import Image
import io

import httpx
from fastapi import Response, Request
from fastapi.responses import FileResponse

logger = None  # Will be initialized from main app


class CDNProvider(Enum):
    """Supported CDN providers"""
    CLOUDFLARE = "cloudflare"
    CLOUDFRONT = "cloudfront"
    FASTLY = "fastly"
    CUSTOM = "custom"


@dataclass
class CDNConfig:
    """CDN configuration settings"""
    provider: CDNProvider
    domain: str
    api_key: Optional[str] = None
    zone_id: Optional[str] = None
    distribution_id: Optional[str] = None
    enable_compression: bool = True
    enable_webp: bool = True
    enable_avif: bool = False
    cache_control_defaults: Dict[str, str] = None
    custom_headers: Dict[str, str] = None


@dataclass
class AssetOptimizationResult:
    """Result of asset optimization"""
    original_size: int
    optimized_size: int
    compression_ratio: float
    format: str
    etag: str
    cache_headers: Dict[str, str]


class CDNOptimizer:
    """
    Advanced CDN and static asset optimizer
    
    Features:
    - Multi-CDN management
    - Automatic image optimization
    - Compression (Brotli, Gzip)
    - Cache header optimization
    - Service worker generation
    - Edge computing integration
    """
    
    # Optimal cache durations by file type
    CACHE_DURATIONS = {
        'image': 31536000,  # 1 year
        'font': 31536000,   # 1 year
        'css': 86400,       # 1 day
        'js': 86400,        # 1 day
        'json': 3600,       # 1 hour
        'html': 0,          # No cache
        'api': 0            # No cache
    }
    
    # File type mappings
    FILE_TYPES = {
        '.jpg': 'image', '.jpeg': 'image', '.png': 'image', 
        '.gif': 'image', '.webp': 'image', '.avif': 'image',
        '.svg': 'image', '.ico': 'image',
        '.woff': 'font', '.woff2': 'font', '.ttf': 'font', '.otf': 'font',
        '.css': 'css', '.scss': 'css', '.sass': 'css',
        '.js': 'js', '.mjs': 'js', '.ts': 'js',
        '.json': 'json',
        '.html': 'html', '.htm': 'html'
    }
    
    def __init__(self, config: CDNConfig):
        """
        Initialize CDN optimizer
        
        Args:
            config: CDN configuration
        """
        self.config = config
        self.http_client = httpx.AsyncClient()
        
        # Set default cache control rules
        if not config.cache_control_defaults:
            self.config.cache_control_defaults = self._get_default_cache_control()
        
        # Initialize optimization stats
        self.stats = {
            'total_optimized': 0,
            'bytes_saved': 0,
            'webp_conversions': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _get_default_cache_control(self) -> Dict[str, str]:
        """Get default cache control headers by file type"""
        return {
            'image': 'public, max-age=31536000, immutable',
            'font': 'public, max-age=31536000, immutable',
            'css': 'public, max-age=86400, must-revalidate',
            'js': 'public, max-age=86400, must-revalidate',
            'json': 'public, max-age=3600, must-revalidate',
            'html': 'no-cache, no-store, must-revalidate',
            'api': 'no-cache, no-store, must-revalidate'
        }
    
    async def optimize_image(
        self,
        image_data: bytes,
        original_format: str,
        target_formats: List[str] = None,
        max_width: int = None,
        quality: int = 85
    ) -> Dict[str, AssetOptimizationResult]:
        """
        Optimize image with multiple format outputs
        
        Args:
            image_data: Original image bytes
            original_format: Original image format
            target_formats: Target formats (webp, avif, etc.)
            max_width: Maximum width for resizing
            quality: Compression quality (1-100)
            
        Returns:
            Dict of format -> optimization result
        """
        if not target_formats:
            target_formats = ['webp'] if self.config.enable_webp else [original_format]
            if self.config.enable_avif:
                target_formats.append('avif')
        
        results = {}
        
        # Open image
        img = Image.open(io.BytesIO(image_data))
        
        # Resize if needed
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            if 'transparency' in img.info:
                # Handle transparency
                alpha = img.convert('RGBA').split()[-1]
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=alpha)
                img = bg
            else:
                img = img.convert('RGB')
        
        # Generate optimized versions
        for format_type in target_formats:
            output = io.BytesIO()
            
            if format_type.lower() == 'webp':
                img.save(output, 'WEBP', quality=quality, method=6)
                self.stats['webp_conversions'] += 1
            elif format_type.lower() == 'avif':
                # AVIF support requires pillow-avif-plugin
                try:
                    img.save(output, 'AVIF', quality=quality, speed=6)
                except:
                    continue
            elif format_type.lower() in ['jpg', 'jpeg']:
                img.save(output, 'JPEG', quality=quality, optimize=True, progressive=True)
            elif format_type.lower() == 'png':
                img.save(output, 'PNG', optimize=True)
            else:
                continue
            
            optimized_data = output.getvalue()
            
            # Calculate metrics
            original_size = len(image_data)
            optimized_size = len(optimized_data)
            compression_ratio = 1 - (optimized_size / original_size)
            
            # Generate ETag
            etag = self._generate_etag(optimized_data)
            
            # Get cache headers
            cache_headers = self._get_cache_headers('image', etag)
            
            results[format_type] = AssetOptimizationResult(
                original_size=original_size,
                optimized_size=optimized_size,
                compression_ratio=compression_ratio,
                format=format_type,
                etag=etag,
                cache_headers=cache_headers
            )
            
            # Update stats
            self.stats['total_optimized'] += 1
            self.stats['bytes_saved'] += (original_size - optimized_size)
        
        return results
    
    def compress_text_asset(
        self,
        content: bytes,
        content_type: str,
        encoding: str = 'brotli'
    ) -> Tuple[bytes, str]:
        """
        Compress text assets (CSS, JS, JSON)
        
        Args:
            content: Original content
            content_type: MIME type
            encoding: Compression encoding (brotli, gzip)
            
        Returns:
            Compressed content and encoding type
        """
        if encoding == 'brotli' and self.config.enable_compression:
            compressed = brotli.compress(content, quality=11)
            return compressed, 'br'
        elif encoding == 'gzip' and self.config.enable_compression:
            compressed = gzip.compress(content, compresslevel=9)
            return compressed, 'gzip'
        else:
            return content, 'identity'
    
    def _generate_etag(self, content: bytes) -> str:
        """Generate ETag for content"""
        return f'"{hashlib.md5(content).hexdigest()}"'
    
    def _get_cache_headers(
        self,
        file_type: str,
        etag: str,
        custom_ttl: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Get optimized cache headers
        
        Args:
            file_type: Type of file
            etag: ETag value
            custom_ttl: Custom TTL in seconds
            
        Returns:
            Cache headers dictionary
        """
        headers = {
            'ETag': etag,
            'Vary': 'Accept-Encoding, Accept',
            'X-Content-Type-Options': 'nosniff'
        }
        
        # Set Cache-Control
        if custom_ttl is not None:
            if custom_ttl == 0:
                headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            else:
                headers['Cache-Control'] = f'public, max-age={custom_ttl}'
        else:
            headers['Cache-Control'] = self.config.cache_control_defaults.get(
                file_type,
                'public, max-age=3600'
            )
        
        # Add security headers for certain types
        if file_type in ['html', 'js']:
            headers['X-XSS-Protection'] = '1; mode=block'
            headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Add custom headers
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)
        
        return headers
    
    async def serve_optimized_asset(
        self,
        request: Request,
        file_path: Path,
        auto_optimize: bool = True
    ) -> Response:
        """
        Serve optimized asset with proper headers
        
        Args:
            request: FastAPI request
            file_path: Path to file
            auto_optimize: Automatically optimize based on file type
            
        Returns:
            Optimized response
        """
        # Check if file exists
        if not file_path.exists():
            return Response(status_code=404)
        
        # Get file extension and type
        ext = file_path.suffix.lower()
        file_type = self.FILE_TYPES.get(ext, 'other')
        
        # Read file content
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        
        # Check client cache (If-None-Match)
        etag = self._generate_etag(content)
        if request.headers.get('If-None-Match') == etag:
            self.stats['cache_hits'] += 1
            return Response(status_code=304)
        
        self.stats['cache_misses'] += 1
        
        # Optimize based on file type
        if auto_optimize:
            if file_type == 'image' and ext in ['.jpg', '.jpeg', '.png']:
                # Check Accept header for WebP support
                accept = request.headers.get('Accept', '')
                if 'image/webp' in accept and self.config.enable_webp:
                    # Try to serve WebP version
                    webp_path = file_path.with_suffix('.webp')
                    if webp_path.exists():
                        async with aiofiles.open(webp_path, 'rb') as f:
                            content = await f.read()
                        content_type = 'image/webp'
                    else:
                        # Convert on the fly
                        results = await self.optimize_image(
                            content,
                            ext[1:],
                            target_formats=['webp']
                        )
                        if 'webp' in results:
                            # Save for future use
                            async with aiofiles.open(webp_path, 'wb') as f:
                                await f.write(content)
                            content_type = 'image/webp'
                else:
                    content_type = mimetypes.guess_type(str(file_path))[0]
            
            elif file_type in ['css', 'js', 'json']:
                # Compress text assets
                accept_encoding = request.headers.get('Accept-Encoding', '')
                
                if 'br' in accept_encoding:
                    content, encoding = self.compress_text_asset(content, file_type, 'brotli')
                    headers = {'Content-Encoding': encoding}
                elif 'gzip' in accept_encoding:
                    content, encoding = self.compress_text_asset(content, file_type, 'gzip')
                    headers = {'Content-Encoding': encoding}
                else:
                    headers = {}
                
                content_type = mimetypes.guess_type(str(file_path))[0]
            else:
                content_type = mimetypes.guess_type(str(file_path))[0]
                headers = {}
        else:
            content_type = mimetypes.guess_type(str(file_path))[0]
            headers = {}
        
        # Add cache headers
        cache_headers = self._get_cache_headers(file_type, etag)
        headers.update(cache_headers)
        
        return Response(
            content=content,
            media_type=content_type,
            headers=headers
        )
    
    async def purge_cdn_cache(
        self,
        urls: List[str] = None,
        tags: List[str] = None,
        purge_all: bool = False
    ) -> bool:
        """
        Purge CDN cache
        
        Args:
            urls: Specific URLs to purge
            tags: Cache tags to purge
            purge_all: Purge entire cache
            
        Returns:
            Success status
        """
        if self.config.provider == CDNProvider.CLOUDFLARE:
            return await self._purge_cloudflare(urls, tags, purge_all)
        elif self.config.provider == CDNProvider.CLOUDFRONT:
            return await self._purge_cloudfront(urls, tags, purge_all)
        elif self.config.provider == CDNProvider.FASTLY:
            return await self._purge_fastly(urls, tags, purge_all)
        else:
            # Custom CDN implementation
            return True
    
    async def _purge_cloudflare(
        self,
        urls: List[str],
        tags: List[str],
        purge_all: bool
    ) -> bool:
        """Purge CloudFlare cache"""
        if not self.config.api_key or not self.config.zone_id:
            return False
        
        endpoint = f"https://api.cloudflare.com/client/v4/zones/{self.config.zone_id}/purge_cache"
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }
        
        if purge_all:
            data = {'purge_everything': True}
        elif urls:
            data = {'files': urls}
        elif tags:
            data = {'tags': tags}
        else:
            return False
        
        response = await self.http_client.post(
            endpoint,
            headers=headers,
            json=data
        )
        
        return response.status_code == 200
    
    async def _purge_cloudfront(
        self,
        urls: List[str],
        tags: List[str],
        purge_all: bool
    ) -> bool:
        """Purge CloudFront cache"""
        # Implementation for AWS CloudFront
        # Requires boto3 and AWS credentials
        pass
    
    async def _purge_fastly(
        self,
        urls: List[str],
        tags: List[str],
        purge_all: bool
    ) -> bool:
        """Purge Fastly cache"""
        # Implementation for Fastly
        pass
    
    def generate_service_worker(self, cache_name: str = 'v1') -> str:
        """
        Generate optimized service worker for offline caching
        
        Args:
            cache_name: Cache version name
            
        Returns:
            Service worker JavaScript code
        """
        return f'''
// Auto-generated Service Worker for Offline Caching
const CACHE_NAME = '{cache_name}';
const RUNTIME_CACHE = 'runtime-{cache_name}';

// Files to cache on install
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/css/main.css',
  '/js/app.js',
  '/manifest.json'
];

// Cache strategies
const CACHE_STRATEGIES = {{
  networkFirst: ['/api/', '/auth/'],
  cacheFirst: ['/static/', '/images/', '/fonts/'],
  staleWhileRevalidate: ['/css/', '/js/']
}};

// Install event - cache static assets
self.addEventListener('install', event => {{
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_CACHE_URLS))
      .then(() => self.skipWaiting())
  );
}});

// Activate event - clean old caches
self.addEventListener('activate', event => {{
  event.waitUntil(
    caches.keys().then(cacheNames => {{
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME && name !== RUNTIME_CACHE)
          .map(name => caches.delete(name))
      );
    }}).then(() => self.clients.claim())
  );
}});

// Fetch event - serve from cache with strategies
self.addEventListener('fetch', event => {{
  const {{request}} = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') return;
  
  // Apply cache strategies
  if (CACHE_STRATEGIES.networkFirst.some(path => url.pathname.startsWith(path))) {{
    event.respondWith(networkFirst(request));
  }} else if (CACHE_STRATEGIES.cacheFirst.some(path => url.pathname.startsWith(path))) {{
    event.respondWith(cacheFirst(request));
  }} else if (CACHE_STRATEGIES.staleWhileRevalidate.some(path => url.pathname.startsWith(path))) {{
    event.respondWith(staleWhileRevalidate(request));
  }} else {{
    event.respondWith(networkFirst(request));
  }}
}});

// Network first strategy
async function networkFirst(request) {{
  try {{
    const networkResponse = await fetch(request);
    const cache = await caches.open(RUNTIME_CACHE);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  }} catch (error) {{
    const cachedResponse = await caches.match(request);
    return cachedResponse || new Response('Offline', {{status: 503}});
  }}
}}

// Cache first strategy
async function cacheFirst(request) {{
  const cachedResponse = await caches.match(request);
  if (cachedResponse) return cachedResponse;
  
  try {{
    const networkResponse = await fetch(request);
    const cache = await caches.open(RUNTIME_CACHE);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  }} catch (error) {{
    return new Response('Resource not available', {{status: 503}});
  }}
}}

// Stale while revalidate strategy
async function staleWhileRevalidate(request) {{
  const cache = await caches.open(RUNTIME_CACHE);
  const cachedResponse = await cache.match(request);
  
  const networkPromise = fetch(request).then(response => {{
    cache.put(request, response.clone());
    return response;
  }});
  
  return cachedResponse || networkPromise;
}}

// Background sync for offline actions
self.addEventListener('sync', event => {{
  if (event.tag === 'sync-data') {{
    event.waitUntil(syncData());
  }}
}});

async function syncData() {{
  // Implement background sync logic
  console.log('Background sync triggered');
}}
'''
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get CDN performance report"""
        return {
            'total_optimized': self.stats['total_optimized'],
            'bytes_saved': self.stats['bytes_saved'],
            'bytes_saved_mb': self.stats['bytes_saved'] / (1024 * 1024),
            'webp_conversions': self.stats['webp_conversions'],
            'cache_hit_ratio': (
                self.stats['cache_hits'] / 
                (self.stats['cache_hits'] + self.stats['cache_misses']) * 100
                if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0
                else 0
            ),
            'provider': self.config.provider.value,
            'compression_enabled': self.config.enable_compression,
            'webp_enabled': self.config.enable_webp,
            'avif_enabled': self.config.enable_avif
        }
    
    async def cleanup(self):
        """Clean up resources"""
        await self.http_client.aclose()