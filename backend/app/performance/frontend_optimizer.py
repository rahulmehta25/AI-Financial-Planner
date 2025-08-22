"""
Frontend Performance Optimization Service

Implements frontend optimization strategies:
- Code splitting configuration
- Image optimization
- Service worker generation
- Virtual scrolling helpers
- Bundle analysis
- Critical CSS extraction
"""

import os
import json
import hashlib
import gzip
import brotli
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import asyncio
import aiofiles
from PIL import Image
import io

logger = None  # Will be initialized from main app


@dataclass
class OptimizationConfig:
    """Frontend optimization configuration"""
    enable_code_splitting: bool = True
    enable_image_optimization: bool = True
    enable_service_worker: bool = True
    enable_virtual_scrolling: bool = True
    enable_critical_css: bool = True
    enable_bundle_analysis: bool = True
    
    # Image optimization
    image_quality: int = 85
    webp_quality: int = 80
    avif_quality: int = 75
    max_image_width: int = 2048
    enable_lazy_loading: bool = True
    
    # Code splitting
    chunk_size_limit: int = 244 * 1024  # 244KB
    vendor_chunk_size: int = 500 * 1024  # 500KB
    
    # Caching
    cache_duration: int = 31536000  # 1 year for static assets
    sw_cache_duration: int = 86400  # 1 day for API responses


class FrontendOptimizer:
    """
    Frontend optimization service
    """
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        
    def generate_next_config(self) -> str:
        """
        Generate optimized Next.js configuration
        
        Returns:
            Next.js config content
        """
        config = """
// next.config.js - Optimized configuration
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer({
  // Performance optimizations
  swcMinify: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Image optimization
  images: {
    domains: ['localhost', 'cdn.example.com'],
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 365, // 1 year
  },
  
  // Code splitting
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Optimize chunks
      config.optimization = {
        ...config.optimization,
        runtimeChunk: 'single',
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            framework: {
              name: 'framework',
              chunks: 'all',
              test: /[\\/]node_modules[\\/](react|react-dom|scheduler|prop-types|use-subscription)[\\/]/,
              priority: 40,
              enforce: true,
            },
            commons: {
              name: 'commons',
              chunks: 'all',
              minChunks: 2,
              priority: 20,
            },
            lib: {
              test(module) {
                return module.size() > 160000 &&
                  /node_modules[\\/]/.test(module.identifier());
              },
              name(module) {
                const hash = crypto.createHash('sha1');
                hash.update(module.identifier());
                return hash.digest('hex').substring(0, 8);
              },
              priority: 30,
              minChunks: 1,
              reuseExistingChunk: true,
            },
          },
          maxAsyncRequests: 25,
          maxInitialRequests: 25,
        },
      };
      
      // Tree shaking
      config.optimization.usedExports = true;
      config.optimization.sideEffects = false;
    }
    
    return config;
  },
  
  // Compression
  compress: true,
  
  // Headers for caching
  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=0, must-revalidate',
          },
        ],
      },
    ];
  },
  
  // Redirects for performance
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ];
  },
  
  // Experimental features
  experimental: {
    optimizeFonts: true,
    optimizeImages: true,
    scrollRestoration: true,
  },
});
"""
        return config
    
    def generate_service_worker(self) -> str:
        """
        Generate optimized service worker for offline caching
        
        Returns:
            Service worker JavaScript code
        """
        sw_code = f"""
// service-worker.js - Optimized PWA service worker
const CACHE_NAME = 'financial-planning-v1';
const RUNTIME_CACHE = 'runtime-cache-v1';
const API_CACHE = 'api-cache-v1';

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/offline',
  '/_next/static/css/styles.css',
  '/_next/static/js/main.js',
  '/favicon.ico',
  '/manifest.json'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {{
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {{
      return cache.addAll(STATIC_ASSETS);
    }})
  );
  self.skipWaiting();
}});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {{
  event.waitUntil(
    caches.keys().then((cacheNames) => {{
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== API_CACHE)
          .map((name) => caches.delete(name))
      );
    }})
  );
  self.clients.claim();
}});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {{
  const {{ request }} = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') return;
  
  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/')) {{
    event.respondWith(
      networkFirstStrategy(request, API_CACHE, {self.config.sw_cache_duration})
    );
    return;
  }}
  
  // Handle static assets with cache-first strategy
  if (url.pathname.startsWith('/_next/static/')) {{
    event.respondWith(
      cacheFirstStrategy(request, CACHE_NAME)
    );
    return;
  }}
  
  // Handle images with stale-while-revalidate
  if (request.destination === 'image') {{
    event.respondWith(
      staleWhileRevalidate(request, RUNTIME_CACHE)
    );
    return;
  }}
  
  // Default to network-first
  event.respondWith(
    networkFirstStrategy(request, RUNTIME_CACHE, 3600)
  );
}});

// Cache strategies
async function cacheFirstStrategy(request, cacheName) {{
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  if (cached) {{
    return cached;
  }}
  
  try {{
    const response = await fetch(request);
    if (response.ok) {{
      cache.put(request, response.clone());
    }}
    return response;
  }} catch (error) {{
    // Return offline page if available
    const offlineResponse = await cache.match('/offline');
    return offlineResponse || new Response('Offline', {{ status: 503 }});
  }}
}}

async function networkFirstStrategy(request, cacheName, maxAge) {{
  try {{
    const response = await fetch(request);
    if (response.ok) {{
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }}
    return response;
  }} catch (error) {{
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {{
      // Check if cache is still valid
      const cachedDate = new Date(cached.headers.get('date'));
      const now = new Date();
      const age = (now - cachedDate) / 1000;
      
      if (age < maxAge) {{
        return cached;
      }}
    }}
    
    return new Response('Network error', {{ status: 503 }});
  }}
}}

async function staleWhileRevalidate(request, cacheName) {{
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  const fetchPromise = fetch(request).then((response) => {{
    if (response.ok) {{
      cache.put(request, response.clone());
    }}
    return response;
  }});
  
  return cached || fetchPromise;
}}

// Background sync for offline actions
self.addEventListener('sync', (event) => {{
  if (event.tag === 'sync-data') {{
    event.waitUntil(syncOfflineData());
  }}
}});

async function syncOfflineData() {{
  // Sync any offline data when connection is restored
  const cache = await caches.open('offline-data');
  const requests = await cache.keys();
  
  for (const request of requests) {{
    try {{
      const response = await fetch(request);
      if (response.ok) {{
        await cache.delete(request);
      }}
    }} catch (error) {{
      console.error('Sync failed for:', request.url);
    }}
  }}
}}

// Push notifications
self.addEventListener('push', (event) => {{
  const options = {{
    body: event.data ? event.data.text() : 'New notification',
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    vibrate: [100, 50, 100],
    data: {{
      dateOfArrival: Date.now(),
      primaryKey: 1
    }}
  }};
  
  event.waitUntil(
    self.registration.showNotification('Financial Planning', options)
  );
}});
"""
        return sw_code
    
    def generate_virtual_scroll_component(self) -> str:
        """
        Generate React component for virtual scrolling
        
        Returns:
            React component code
        """
        component = """
// VirtualScroll.tsx - Optimized virtual scrolling component
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FixedSizeList, VariableSizeList, ListChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { debounce } from 'lodash';

interface VirtualScrollProps<T> {
  items: T[];
  itemHeight?: number | ((index: number) => number);
  renderItem: (item: T, index: number, style: React.CSSProperties) => React.ReactNode;
  overscan?: number;
  onEndReached?: () => void;
  endReachedThreshold?: number;
  loading?: boolean;
  estimatedItemSize?: number;
}

export function VirtualScroll<T>({
  items,
  itemHeight = 50,
  renderItem,
  overscan = 5,
  onEndReached,
  endReachedThreshold = 0.8,
  loading = false,
  estimatedItemSize = 50,
}: VirtualScrollProps<T>) {
  const listRef = useRef<any>(null);
  const [scrollOffset, setScrollOffset] = useState(0);
  const [isNearEnd, setIsNearEnd] = useState(false);
  
  // Determine if using fixed or variable size list
  const isFixedSize = typeof itemHeight === 'number';
  
  // Item renderer wrapper
  const ItemRenderer = useCallback(
    ({ index, style }: ListChildComponentProps) => {
      const item = items[index];
      return renderItem(item, index, style);
    },
    [items, renderItem]
  );
  
  // Handle scroll for infinite loading
  const handleScroll = useCallback(
    debounce(({ scrollOffset, scrollHeight, clientHeight }: any) => {
      setScrollOffset(scrollOffset);
      
      const scrollPercentage = (scrollOffset + clientHeight) / scrollHeight;
      const shouldLoadMore = scrollPercentage > endReachedThreshold;
      
      if (shouldLoadMore && !isNearEnd && !loading && onEndReached) {
        setIsNearEnd(true);
        onEndReached();
      } else if (!shouldLoadMore && isNearEnd) {
        setIsNearEnd(false);
      }
    }, 150),
    [endReachedThreshold, isNearEnd, loading, onEndReached]
  );
  
  // Reset near end when items change
  useEffect(() => {
    setIsNearEnd(false);
  }, [items.length]);
  
  // Scroll to top method
  const scrollToTop = useCallback(() => {
    listRef.current?.scrollToItem(0, 'start');
  }, []);
  
  // Expose scroll methods via ref
  useEffect(() => {
    if (window) {
      (window as any).virtualScrollToTop = scrollToTop;
    }
  }, [scrollToTop]);
  
  return (
    <div className="virtual-scroll-container" style={{ height: '100%', width: '100%' }}>
      <AutoSizer>
        {({ height, width }) => {
          if (isFixedSize) {
            return (
              <FixedSizeList
                ref={listRef}
                height={height}
                width={width}
                itemCount={items.length}
                itemSize={itemHeight as number}
                overscanCount={overscan}
                onScroll={handleScroll}
              >
                {ItemRenderer}
              </FixedSizeList>
            );
          } else {
            return (
              <VariableSizeList
                ref={listRef}
                height={height}
                width={width}
                itemCount={items.length}
                itemSize={itemHeight as (index: number) => number}
                overscanCount={overscan}
                estimatedItemSize={estimatedItemSize}
                onScroll={handleScroll}
              >
                {ItemRenderer}
              </VariableSizeList>
            );
          }
        }}
      </AutoSizer>
      
      {loading && (
        <div className="loading-indicator" style={{
          textAlign: 'center',
          padding: '1rem',
          opacity: 0.7
        }}>
          Loading more...
        </div>
      )}
    </div>
  );
}

// Optimized list item with memo
export const VirtualScrollItem = React.memo<{
  item: any;
  style: React.CSSProperties;
  renderContent: (item: any) => React.ReactNode;
}>(({ item, style, renderContent }) => {
  return (
    <div style={style} className="virtual-scroll-item">
      {renderContent(item)}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for optimization
  return (
    prevProps.item.id === nextProps.item.id &&
    prevProps.style.top === nextProps.style.top
  );
});

// Hook for virtual scroll optimization
export function useVirtualScrollOptimization(
  items: any[],
  options: {
    batchSize?: number;
    preloadImages?: boolean;
    cacheItems?: boolean;
  } = {}
) {
  const {
    batchSize = 20,
    preloadImages = true,
    cacheItems = true
  } = options;
  
  const [optimizedItems, setOptimizedItems] = useState(items.slice(0, batchSize));
  const [loadedBatches, setLoadedBatches] = useState(1);
  const itemCache = useRef(new Map());
  
  // Load more items progressively
  useEffect(() => {
    const totalBatches = Math.ceil(items.length / batchSize);
    
    if (loadedBatches < totalBatches) {
      const timer = setTimeout(() => {
        const nextBatch = items.slice(
          0,
          Math.min((loadedBatches + 1) * batchSize, items.length)
        );
        setOptimizedItems(nextBatch);
        setLoadedBatches(loadedBatches + 1);
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [items, loadedBatches, batchSize]);
  
  // Preload images if enabled
  useEffect(() => {
    if (preloadImages) {
      optimizedItems.forEach(item => {
        if (item.imageUrl && !itemCache.current.has(item.imageUrl)) {
          const img = new Image();
          img.src = item.imageUrl;
          itemCache.current.set(item.imageUrl, true);
        }
      });
    }
  }, [optimizedItems, preloadImages]);
  
  return {
    items: optimizedItems,
    isLoading: loadedBatches * batchSize < items.length,
    progress: (loadedBatches * batchSize) / items.length
  };
}
"""
        return component
    
    async def optimize_image(
        self,
        image_path: str,
        output_formats: List[str] = ['webp', 'avif'],
        sizes: List[int] = [640, 1280, 1920]
    ) -> Dict[str, List[str]]:
        """
        Optimize images for web delivery
        
        Args:
            image_path: Path to source image
            output_formats: List of output formats
            sizes: List of widths to generate
            
        Returns:
            Dictionary of generated image paths by format
        """
        results = {}
        
        try:
            # Open source image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                base_name = Path(image_path).stem
                base_dir = Path(image_path).parent
                
                for format_type in output_formats:
                    format_results = []
                    
                    for width in sizes:
                        # Skip if image is smaller than target width
                        if img.width < width:
                            continue
                        
                        # Calculate height maintaining aspect ratio
                        height = int(img.height * (width / img.width))
                        
                        # Resize image
                        resized = img.resize((width, height), Image.LANCZOS)
                        
                        # Generate output path
                        output_name = f"{base_name}-{width}w.{format_type}"
                        output_path = base_dir / output_name
                        
                        # Save in specified format
                        if format_type == 'webp':
                            resized.save(
                                output_path,
                                'WEBP',
                                quality=self.config.webp_quality,
                                method=6
                            )
                        elif format_type == 'avif':
                            resized.save(
                                output_path,
                                'AVIF',
                                quality=self.config.avif_quality
                            )
                        else:
                            resized.save(
                                output_path,
                                format_type.upper(),
                                quality=self.config.image_quality,
                                optimize=True
                            )
                        
                        format_results.append(str(output_path))
                    
                    results[format_type] = format_results
                
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
        
        return results
    
    def generate_critical_css(self, html_content: str) -> str:
        """
        Extract critical CSS for above-the-fold content
        
        Args:
            html_content: HTML content
            
        Returns:
            Critical CSS
        """
        # This is a simplified version - in production use tools like critical or penthouse
        critical_css = """
/* Critical CSS for above-the-fold content */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  line-height: 1.6;
  color: #333;
  background: #fff;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.header {
  background: #007bff;
  color: white;
  padding: 1rem 0;
  position: fixed;
  width: 100%;
  top: 0;
  z-index: 1000;
}

.main-content {
  margin-top: 60px;
  min-height: calc(100vh - 60px);
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Optimize for Core Web Vitals */
img {
  max-width: 100%;
  height: auto;
  content-visibility: auto;
}

.lazy-load {
  background: #f0f0f0;
  min-height: 200px;
}
"""
        return critical_css
    
    def generate_webpack_config(self) -> str:
        """
        Generate optimized Webpack configuration
        
        Returns:
            Webpack config content
        """
        config = """
// webpack.config.js - Optimized configuration
const path = require('path');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const WorkboxPlugin = require('workbox-webpack-plugin');

module.exports = {
  mode: 'production',
  
  entry: {
    main: './src/index.js',
    vendor: ['react', 'react-dom', 'react-router-dom']
  },
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[contenthash].js',
    chunkFilename: '[name].[contenthash].chunk.js',
    clean: true
  },
  
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true,
            pure_funcs: ['console.log']
          },
          mangle: true,
          format: {
            comments: false
          }
        },
        extractComments: false
      })
    ],
    
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
          reuseExistingChunk: true
        },
        common: {
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true
        }
      }
    },
    
    runtimeChunk: 'single',
    moduleIds: 'deterministic'
  },
  
  plugins: [
    // Compression
    new CompressionPlugin({
      algorithm: 'gzip',
      test: /\.(js|css|html|svg)$/,
      threshold: 8192,
      minRatio: 0.8
    }),
    
    new CompressionPlugin({
      algorithm: 'brotliCompress',
      test: /\.(js|css|html|svg)$/,
      compressionOptions: {
        level: 11
      },
      threshold: 8192,
      minRatio: 0.8,
      filename: '[path][base].br'
    }),
    
    // Bundle analysis
    new BundleAnalyzerPlugin({
      analyzerMode: process.env.ANALYZE ? 'server' : 'disabled'
    }),
    
    // Service Worker
    new WorkboxPlugin.GenerateSW({
      clientsClaim: true,
      skipWaiting: true,
      runtimeCaching: [{
        urlPattern: /^https:\/\/api\./,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'api-cache',
          expiration: {
            maxEntries: 50,
            maxAgeSeconds: 300 // 5 minutes
          }
        }
      }]
    }),
    
    // Define environment variables
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('production')
    })
  ],
  
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
            plugins: ['@babel/plugin-syntax-dynamic-import']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      },
      {
        test: /\.(png|jpg|jpeg|gif|webp|avif)$/i,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 8192 // 8kb
          }
        }
      }
    ]
  },
  
  resolve: {
    extensions: ['.js', '.jsx', '.json'],
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  
  performance: {
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
    hints: 'warning'
  }
};
"""
        return config
    
    def analyze_bundle_size(self, stats_file: str) -> Dict[str, Any]:
        """
        Analyze webpack bundle stats
        
        Args:
            stats_file: Path to webpack stats JSON file
            
        Returns:
            Bundle analysis results
        """
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            analysis = {
                'total_size': 0,
                'chunks': [],
                'largest_modules': [],
                'recommendations': []
            }
            
            # Analyze chunks
            for chunk in stats.get('chunks', []):
                chunk_info = {
                    'name': chunk.get('names', ['unknown'])[0],
                    'size': chunk.get('size', 0),
                    'modules': len(chunk.get('modules', []))
                }
                analysis['chunks'].append(chunk_info)
                analysis['total_size'] += chunk_info['size']
                
                # Check for oversized chunks
                if chunk_info['size'] > self.config.chunk_size_limit:
                    analysis['recommendations'].append(
                        f"Chunk '{chunk_info['name']}' is too large "
                        f"({chunk_info['size'] / 1024:.1f}KB). Consider splitting."
                    )
            
            # Find largest modules
            all_modules = []
            for module in stats.get('modules', []):
                all_modules.append({
                    'name': module.get('name', 'unknown'),
                    'size': module.get('size', 0)
                })
            
            all_modules.sort(key=lambda x: x['size'], reverse=True)
            analysis['largest_modules'] = all_modules[:10]
            
            # General recommendations
            if analysis['total_size'] > 1024 * 1024:  # 1MB
                analysis['recommendations'].append(
                    f"Total bundle size ({analysis['total_size'] / (1024*1024):.2f}MB) "
                    "is large. Consider code splitting and lazy loading."
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Bundle analysis failed: {e}")
            return {}