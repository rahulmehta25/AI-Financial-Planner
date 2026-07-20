"""
Self-Service Analytics Portal for Financial Planning Platform
Provides drag-and-drop analytics capabilities with automated insights
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# ML and statistics
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuration
class ChartType(Enum):
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    HEATMAP = "heatmap"
    BOX = "box"
    HISTOGRAM = "histogram"
    AREA = "area"
    FUNNEL = "funnel"
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    WATERFALL = "waterfall"

class AggregationType(Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD = "std"
    DISTINCT_COUNT = "distinct_count"

@dataclass
class DataSource:
    name: str
    type: str  # postgres, mongodb, csv, api
    connection_string: str
    schema: str = None
    table: str = None
    query: str = None
    refresh_rate: int = 3600  # seconds

@dataclass
class ChartConfig:
    chart_type: ChartType
    title: str
    data_source: str
    x_axis: str
    y_axis: Union[str, List[str]]
    group_by: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    aggregations: Optional[Dict[str, AggregationType]] = None
    color_scheme: Optional[str] = None
    width: int = 600
    height: int = 400

class SelfServiceAnalytics:
    """
    Self-service analytics engine with drag-and-drop capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database connections
        self.engines = {}
        for ds_name, ds_config in config.get('data_sources', {}).items():
            self.engines[ds_name] = create_engine(ds_config['connection_string'])
        
        # Cache for query results
        self.query_cache = {}
        self.metadata_cache = {}
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configure caching
        self.cache = Cache(self.app, config={
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': config.get('redis_url', 'redis://localhost:6379')
        })
        
        # Rate limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["1000 per hour"]
        )
        
        self.setup_routes()
        
        self.logger.info("Self-Service Analytics Portal initialized")
    
    def setup_routes(self):
        """
        Set up Flask routes for the analytics portal
        """
        
        @self.app.route('/')
        def index():
            return render_template('analytics_portal.html')
        
        @self.app.route('/api/data-sources')
        @self.cache.cached(timeout=3600)
        def get_data_sources():
            """Get available data sources and their metadata"""
            try:
                sources = []
                for ds_name, engine in self.engines.items():
                    metadata = self.get_data_source_metadata(ds_name)
                    sources.append({
                        'name': ds_name,
                        'tables': metadata.get('tables', []),
                        'columns': metadata.get('columns', {})
                    })
                
                return jsonify({
                    'status': 'success',
                    'data_sources': sources
                })
            except Exception as e:
                self.logger.error(f"Error getting data sources: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/query', methods=['POST'])
        @self.limiter.limit("100 per minute")
        def execute_query():
            """Execute a custom SQL query"""
            try:
                data = request.json
                query = data.get('query')
                data_source = data.get('data_source')
                limit = min(data.get('limit', 1000), 10000)  # Cap at 10k rows
                
                if not query or not data_source:
                    return jsonify({
                        'status': 'error',
                        'message': 'Query and data_source are required'
                    }), 400
                
                # Security: Basic SQL injection prevention
                if self.is_unsafe_query(query):
                    return jsonify({
                        'status': 'error',
                        'message': 'Query contains unsafe operations'
                    }), 400
                
                # Execute query
                engine = self.engines.get(data_source)
                if not engine:
                    return jsonify({
                        'status': 'error',
                        'message': f'Data source {data_source} not found'
                    }), 404
                
                # Add LIMIT to query if not present
                if 'LIMIT' not in query.upper():
                    query += f' LIMIT {limit}'
                
                df = pd.read_sql(query, engine)
                
                # Convert to JSON-serializable format
                result = {
                    'columns': df.columns.tolist(),
                    'data': df.to_dict('records'),
                    'row_count': len(df),
                    'data_types': df.dtypes.astype(str).to_dict()
                }
                
                return jsonify({
                    'status': 'success',
                    'result': result
                })
                
            except Exception as e:
                self.logger.error(f"Error executing query: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/chart', methods=['POST'])
        def create_chart():
            """Create a chart based on configuration"""
            try:
                chart_config = request.json
                chart = self.generate_chart(chart_config)
                
                return jsonify({
                    'status': 'success',
                    'chart': chart
                })
                
            except Exception as e:
                self.logger.error(f"Error creating chart: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/insights', methods=['POST'])
        def generate_insights():
            """Generate automated insights from data"""
            try:
                data = request.json
                table_name = data.get('table')
                data_source = data.get('data_source')
                
                insights = self.generate_automated_insights(data_source, table_name)
                
                return jsonify({
                    'status': 'success',
                    'insights': insights
                })
                
            except Exception as e:
                self.logger.error(f"Error generating insights: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/dashboard', methods=['POST'])
        def save_dashboard():
            """Save a custom dashboard configuration"""
            try:
                dashboard_config = request.json
                dashboard_id = self.save_dashboard_config(dashboard_config)
                
                return jsonify({
                    'status': 'success',
                    'dashboard_id': dashboard_id
                })
                
            except Exception as e:
                self.logger.error(f"Error saving dashboard: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/dashboard/<dashboard_id>')
        def load_dashboard(dashboard_id):
            """Load a saved dashboard configuration"""
            try:
                dashboard_config = self.load_dashboard_config(dashboard_id)
                
                return jsonify({
                    'status': 'success',
                    'dashboard': dashboard_config
                })
                
            except Exception as e:
                self.logger.error(f"Error loading dashboard: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/export', methods=['POST'])
        def export_data():
            """Export data or charts in various formats"""
            try:
                export_config = request.json
                export_type = export_config.get('type', 'csv')
                
                file_path = self.export_data_or_chart(export_config)
                
                return send_file(file_path, as_attachment=True)
                
            except Exception as e:
                self.logger.error(f"Error exporting data: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def get_data_source_metadata(self, data_source: str) -> Dict[str, Any]:
        """
        Get metadata for a data source including tables and columns
        """
        if data_source in self.metadata_cache:
            return self.metadata_cache[data_source]
        
        try:
            engine = self.engines[data_source]
            
            # Get all tables
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY table_name
            """
            
            tables_df = pd.read_sql(tables_query, engine)
            tables = tables_df['table_name'].tolist()
            
            # Get columns for each table
            columns = {}
            for table in tables:
                columns_query = f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """
                
                cols_df = pd.read_sql(columns_query, engine)
                columns[table] = cols_df.to_dict('records')
            
            metadata = {
                'tables': tables,
                'columns': columns
            }
            
            # Cache metadata
            self.metadata_cache[data_source] = metadata
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error getting metadata for {data_source}: {str(e)}")
            return {'tables': [], 'columns': {}}
    
    def is_unsafe_query(self, query: str) -> bool:
        """
        Basic SQL injection prevention
        """
        unsafe_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'EXEC', 'EXECUTE', '--', ';', 'xp_'
        ]
        
        query_upper = query.upper()
        return any(keyword in query_upper for keyword in unsafe_keywords)
    
    def generate_chart(self, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a chart based on configuration
        """
        try:
            # Get data
            data_source = chart_config.get('data_source')
            query = chart_config.get('query')
            table = chart_config.get('table')
            
            if query:
                df = pd.read_sql(query, self.engines[data_source])
            elif table:
                df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", self.engines[data_source])
            else:
                raise ValueError("Either query or table must be provided")
            
            # Apply filters
            filters = chart_config.get('filters', {})
            for column, filter_config in filters.items():
                if column in df.columns:
                    filter_type = filter_config.get('type')
                    value = filter_config.get('value')
                    
                    if filter_type == 'equals':
                        df = df[df[column] == value]
                    elif filter_type == 'greater_than':
                        df = df[df[column] > value]
                    elif filter_type == 'less_than':
                        df = df[df[column] < value]
                    elif filter_type == 'contains':
                        df = df[df[column].str.contains(value, na=False)]
            
            # Apply aggregations
            group_by = chart_config.get('group_by')
            aggregations = chart_config.get('aggregations', {})
            
            if group_by and aggregations:
                agg_dict = {}
                for column, agg_type in aggregations.items():
                    if agg_type == 'sum':
                        agg_dict[column] = 'sum'
                    elif agg_type == 'avg':
                        agg_dict[column] = 'mean'
                    elif agg_type == 'count':
                        agg_dict[column] = 'count'
                    elif agg_type == 'min':
                        agg_dict[column] = 'min'
                    elif agg_type == 'max':
                        agg_dict[column] = 'max'
                
                df = df.groupby(group_by).agg(agg_dict).reset_index()
            
            # Generate chart
            chart_type = chart_config.get('chart_type', 'bar')
            x_axis = chart_config.get('x_axis')
            y_axis = chart_config.get('y_axis')
            title = chart_config.get('title', 'Chart')
            
            if chart_type == 'bar':
                fig = px.bar(df, x=x_axis, y=y_axis, title=title)
            elif chart_type == 'line':
                fig = px.line(df, x=x_axis, y=y_axis, title=title)
            elif chart_type == 'scatter':
                fig = px.scatter(df, x=x_axis, y=y_axis, title=title)
            elif chart_type == 'pie':
                fig = px.pie(df, values=y_axis, names=x_axis, title=title)
            elif chart_type == 'histogram':
                fig = px.histogram(df, x=x_axis, title=title)
            elif chart_type == 'box':
                fig = px.box(df, x=x_axis, y=y_axis, title=title)
            elif chart_type == 'heatmap':
                # Create pivot table for heatmap
                if len(df.columns) >= 3:
                    pivot_df = df.pivot_table(
                        index=df.columns[0], 
                        columns=df.columns[1], 
                        values=df.columns[2], 
                        aggfunc='mean'
                    )
                    fig = px.imshow(pivot_df, title=title)
                else:
                    fig = px.bar(df, x=x_axis, y=y_axis, title=title)  # Fallback
            else:
                fig = px.bar(df, x=x_axis, y=y_axis, title=title)  # Default
            
            # Customize appearance
            fig.update_layout(
                width=chart_config.get('width', 600),
                height=chart_config.get('height', 400),
                template='plotly_white'
            )
            
            # Convert to JSON
            chart_json = fig.to_json()
            
            return {
                'chart_data': json.loads(chart_json),
                'data_summary': {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_types': df.dtypes.astype(str).to_dict()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating chart: {str(e)}")
            raise
    
    def generate_automated_insights(self, data_source: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Generate automated insights from data using statistical analysis
        """
        try:
            insights = []
            
            # Load data sample
            query = f"SELECT * FROM {table_name} LIMIT 5000"
            df = pd.read_sql(query, self.engines[data_source])
            
            if df.empty:
                return [{"type": "info", "message": "No data available for analysis"}]
            
            # Basic statistics insights
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            categorical_columns = df.select_dtypes(include=['object', 'category']).columns
            
            # Data overview
            insights.append({
                "type": "overview",
                "title": "Data Overview",
                "message": f"Dataset contains {len(df)} rows and {len(df.columns)} columns",
                "details": {
                    "numeric_columns": len(numeric_columns),
                    "categorical_columns": len(categorical_columns),
                    "missing_values": df.isnull().sum().sum()
                }
            })
            
            # Outlier detection for numeric columns
            for column in numeric_columns:
                if df[column].nunique() > 10:  # Skip boolean-like columns
                    Q1 = df[column].quantile(0.25)
                    Q3 = df[column].quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = df[(df[column] < Q1 - 1.5 * IQR) | (df[column] > Q3 + 1.5 * IQR)]
                    
                    if len(outliers) > 0:
                        outlier_pct = (len(outliers) / len(df)) * 100
                        insights.append({
                            "type": "outlier",
                            "title": f"Outliers Detected in {column}",
                            "message": f"{len(outliers)} outliers found ({outlier_pct:.1f}% of data)",
                            "column": column,
                            "severity": "high" if outlier_pct > 10 else "medium" if outlier_pct > 5 else "low"
                        })
            
            # Correlation insights
            if len(numeric_columns) >= 2:
                corr_matrix = df[numeric_columns].corr()
                
                # Find strong correlations
                strong_corrs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:  # Strong correlation threshold
                            strong_corrs.append({
                                "col1": corr_matrix.columns[i],
                                "col2": corr_matrix.columns[j],
                                "correlation": corr_val
                            })
                
                if strong_corrs:
                    insights.append({
                        "type": "correlation",
                        "title": "Strong Correlations Found",
                        "message": f"Found {len(strong_corrs)} pairs with strong correlation",
                        "details": strong_corrs[:5]  # Top 5
                    })
            
            # Distribution insights
            for column in numeric_columns:
                if df[column].nunique() > 10:
                    # Check for normal distribution
                    statistic, p_value = stats.normaltest(df[column].dropna())
                    is_normal = p_value > 0.05
                    
                    skewness = df[column].skew()
                    
                    if abs(skewness) > 1:
                        skew_direction = "right" if skewness > 0 else "left"
                        insights.append({
                            "type": "distribution",
                            "title": f"Skewed Distribution: {column}",
                            "message": f"Data is {skew_direction}-skewed (skewness: {skewness:.2f})",
                            "column": column,
                            "is_normal": is_normal
                        })
            
            # Categorical insights
            for column in categorical_columns:
                value_counts = df[column].value_counts()
                
                # Check for dominant categories
                if len(value_counts) > 1:
                    dominant_pct = (value_counts.iloc[0] / len(df)) * 100
                    
                    if dominant_pct > 80:
                        insights.append({
                            "type": "dominance",
                            "title": f"Dominant Category in {column}",
                            "message": f"'{value_counts.index[0]}' represents {dominant_pct:.1f}% of data",
                            "column": column,
                            "dominant_value": value_counts.index[0]
                        })
                
                # Check for many unique values (potential ID column)
                if value_counts.nunique() > len(df) * 0.9:
                    insights.append({
                        "type": "uniqueness",
                        "title": f"High Uniqueness: {column}",
                        "message": f"Column has {value_counts.nunique()} unique values (potential identifier)",
                        "column": column
                    })
            
            # Missing data insights
            missing_data = df.isnull().sum()
            high_missing = missing_data[missing_data > len(df) * 0.5]
            
            if not high_missing.empty:
                insights.append({
                    "type": "missing_data",
                    "title": "High Missing Data",
                    "message": f"{len(high_missing)} columns have >50% missing data",
                    "details": {col: f"{(count/len(df)*100):.1f}%" for col, count in high_missing.items()}
                })
            
            # Time series insights (if date columns exist)
            date_columns = df.select_dtypes(include=['datetime64']).columns
            if len(date_columns) > 0 and len(numeric_columns) > 0:
                for date_col in date_columns:
                    for numeric_col in numeric_columns[:2]:  # Check first 2 numeric columns
                        # Simple trend analysis
                        df_sorted = df.sort_values(date_col)
                        correlation_with_time = df_sorted[numeric_col].corr(
                            pd.to_numeric(df_sorted[date_col])
                        )
                        
                        if abs(correlation_with_time) > 0.5:
                            trend_direction = "increasing" if correlation_with_time > 0 else "decreasing"
                            insights.append({
                                "type": "trend",
                                "title": f"Time Trend in {numeric_col}",
                                "message": f"{numeric_col} shows {trend_direction} trend over time",
                                "correlation": correlation_with_time
                            })
            
            return insights[:10]  # Return top 10 insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return [{
                "type": "error",
                "message": f"Error generating insights: {str(e)}"
            }]
    
    def save_dashboard_config(self, dashboard_config: Dict[str, Any]) -> str:
        """
        Save dashboard configuration to file or database
        """
        dashboard_id = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add metadata
        dashboard_config['id'] = dashboard_id
        dashboard_config['created_at'] = datetime.now().isoformat()
        dashboard_config['version'] = '1.0'
        
        # Save to file (in production, save to database)
        dashboards_dir = '/tmp/dashboards'  # Use proper directory
        os.makedirs(dashboards_dir, exist_ok=True)
        
        file_path = os.path.join(dashboards_dir, f"{dashboard_id}.json")
        with open(file_path, 'w') as f:
            json.dump(dashboard_config, f, indent=2)
        
        return dashboard_id
    
    def load_dashboard_config(self, dashboard_id: str) -> Dict[str, Any]:
        """
        Load dashboard configuration from file or database
        """
        dashboards_dir = '/tmp/dashboards'
        file_path = os.path.join(dashboards_dir, f"{dashboard_id}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dashboard {dashboard_id} not found")
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def export_data_or_chart(self, export_config: Dict[str, Any]) -> str:
        """
        Export data or chart to various formats
        """
        export_type = export_config.get('type', 'csv')
        data_source = export_config.get('data_source')
        query = export_config.get('query')
        
        # Get data
        df = pd.read_sql(query, self.engines[data_source])
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_{timestamp}.{export_type}"
        file_path = f"/tmp/{filename}"
        
        if export_type == 'csv':
            df.to_csv(file_path, index=False)
        elif export_type == 'excel':
            df.to_excel(file_path, index=False)
        elif export_type == 'json':
            df.to_json(file_path, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported export type: {export_type}")
        
        return file_path
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """
        Run the Flask application
        """
        self.app.run(host=host, port=port, debug=debug)

# HTML Template for the analytics portal
ANALYTICS_PORTAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Analytics Portal</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .drag-drop-area {
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: border-color 0.3s ease;
        }
        .drag-drop-area:hover {
            border-color: #3182ce;
        }
        .chart-container {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin: 8px;
            min-height: 400px;
        }
    </style>
</head>
<body class="bg-gray-100">
    <!-- Header -->
    <header class="bg-white shadow-lg">
        <div class="container mx-auto px-4 py-4">
            <h1 class="text-3xl font-bold text-gray-800">Financial Analytics Portal</h1>
            <p class="text-gray-600 mt-2">Drag and drop analytics with automated insights</p>
        </div>
    </header>

    <!-- Main Content -->
    <div class="container mx-auto px-4 py-8">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            
            <!-- Sidebar: Data Sources & Tools -->
            <div class="lg:col-span-1">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4">Data Sources</h2>
                    <div id="data-sources" class="space-y-2">
                        <!-- Data sources will be loaded here -->
                    </div>
                    
                    <h3 class="text-lg font-semibold mt-6 mb-3">Chart Types</h3>
                    <div class="grid grid-cols-2 gap-2">
                        <button class="chart-type-btn p-2 text-sm border rounded hover:bg-blue-50" data-type="bar">Bar</button>
                        <button class="chart-type-btn p-2 text-sm border rounded hover:bg-blue-50" data-type="line">Line</button>
                        <button class="chart-type-btn p-2 text-sm border rounded hover:bg-blue-50" data-type="pie">Pie</button>
                        <button class="chart-type-btn p-2 text-sm border rounded hover:bg-blue-50" data-type="scatter">Scatter</button>
                        <button class="chart-type-btn p-2 text-sm border rounded hover:bg-blue-50" data-type="histogram">Histogram</button>
                        <button class="chart-type-btn p-2 text-sm border rounded hover:bg-blue-50" data-type="box">Box Plot</button>
                    </div>

                    <h3 class="text-lg font-semibold mt-6 mb-3">Quick Actions</h3>
                    <div class="space-y-2">
                        <button id="generate-insights-btn" class="w-full p-2 bg-green-500 text-white rounded hover:bg-green-600">Generate Insights</button>
                        <button id="save-dashboard-btn" class="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600">Save Dashboard</button>
                        <button id="export-data-btn" class="w-full p-2 bg-purple-500 text-white rounded hover:bg-purple-600">Export Data</button>
                    </div>
                </div>
            </div>

            <!-- Main Area: Charts & Analytics -->
            <div class="lg:col-span-3">
                <!-- Query Builder -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 class="text-xl font-semibold mb-4">Query Builder</h2>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <select id="data-source-select" class="p-2 border rounded">
                            <option value="">Select Data Source</option>
                        </select>
                        <select id="table-select" class="p-2 border rounded">
                            <option value="">Select Table</option>
                        </select>
                        <button id="load-data-btn" class="p-2 bg-indigo-500 text-white rounded hover:bg-indigo-600">Load Data</button>
                    </div>
                    
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2">Custom SQL Query (Optional)</label>
                        <textarea id="sql-query" class="w-full p-3 border rounded-lg" rows="3" placeholder="SELECT * FROM table_name LIMIT 100"></textarea>
                    </div>
                    
                    <button id="execute-query-btn" class="p-2 bg-blue-500 text-white rounded hover:bg-blue-600">Execute Query</button>
                </div>

                <!-- Chart Configuration -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 class="text-xl font-semibold mb-4">Chart Configuration</h2>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-1">Chart Type</label>
                            <select id="chart-type-select" class="w-full p-2 border rounded">
                                <option value="bar">Bar Chart</option>
                                <option value="line">Line Chart</option>
                                <option value="scatter">Scatter Plot</option>
                                <option value="pie">Pie Chart</option>
                                <option value="histogram">Histogram</option>
                                <option value="box">Box Plot</option>
                                <option value="heatmap">Heatmap</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1">X-Axis</label>
                            <select id="x-axis-select" class="w-full p-2 border rounded">
                                <option value="">Select Column</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1">Y-Axis</label>
                            <select id="y-axis-select" class="w-full p-2 border rounded">
                                <option value="">Select Column</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1">Group By</label>
                            <select id="group-by-select" class="w-full p-2 border rounded">
                                <option value="">None</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <input type="text" id="chart-title" class="w-full p-2 border rounded" placeholder="Chart Title">
                    </div>
                    
                    <div class="mt-4">
                        <button id="create-chart-btn" class="p-2 bg-green-500 text-white rounded hover:bg-green-600">Create Chart</button>
                    </div>
                </div>

                <!-- Charts Display Area -->
                <div id="charts-container" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Charts will be displayed here -->
                </div>

                <!-- Insights Panel -->
                <div id="insights-panel" class="bg-white rounded-lg shadow-md p-6 mt-6" style="display: none;">
                    <h2 class="text-xl font-semibold mb-4">Automated Insights</h2>
                    <div id="insights-content">
                        <!-- Insights will be displayed here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // JavaScript for the analytics portal
        let currentData = null;
        let currentColumns = [];
        let chartCounter = 0;

        // Load data sources on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadDataSources();
        });

        async function loadDataSources() {
            try {
                const response = await axios.get('/api/data-sources');
                const dataSources = response.data.data_sources;
                
                const dataSourceSelect = document.getElementById('data-source-select');
                const dataSourcesDiv = document.getElementById('data-sources');
                
                dataSources.forEach(source => {
                    // Add to select dropdown
                    const option = document.createElement('option');
                    option.value = source.name;
                    option.textContent = source.name;
                    dataSourceSelect.appendChild(option);
                    
                    // Add to sidebar
                    const sourceDiv = document.createElement('div');
                    sourceDiv.className = 'p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100';
                    sourceDiv.textContent = source.name;
                    sourceDiv.onclick = () => selectDataSource(source.name, source.tables);
                    dataSourcesDiv.appendChild(sourceDiv);
                });
            } catch (error) {
                console.error('Error loading data sources:', error);
            }
        }

        function selectDataSource(sourceName, tables) {
            const tableSelect = document.getElementById('table-select');
            tableSelect.innerHTML = '<option value="">Select Table</option>';
            
            tables.forEach(table => {
                const option = document.createElement('option');
                option.value = table;
                option.textContent = table;
                tableSelect.appendChild(option);
            });
            
            document.getElementById('data-source-select').value = sourceName;
        }

        // Load data when button is clicked
        document.getElementById('load-data-btn').addEventListener('click', async function() {
            const dataSource = document.getElementById('data-source-select').value;
            const table = document.getElementById('table-select').value;
            
            if (!dataSource || !table) {
                alert('Please select both data source and table');
                return;
            }
            
            try {
                const query = `SELECT * FROM ${table} LIMIT 100`;
                const response = await axios.post('/api/query', {
                    query: query,
                    data_source: dataSource
                });
                
                currentData = response.data.result.data;
                currentColumns = response.data.result.columns;
                
                // Update column selectors
                updateColumnSelectors(currentColumns);
                
                alert(`Loaded ${currentData.length} rows from ${table}`);
            } catch (error) {
                alert('Error loading data: ' + error.response.data.message);
            }
        });

        // Execute custom query
        document.getElementById('execute-query-btn').addEventListener('click', async function() {
            const dataSource = document.getElementById('data-source-select').value;
            const query = document.getElementById('sql-query').value;
            
            if (!dataSource || !query) {
                alert('Please select data source and enter query');
                return;
            }
            
            try {
                const response = await axios.post('/api/query', {
                    query: query,
                    data_source: dataSource
                });
                
                currentData = response.data.result.data;
                currentColumns = response.data.result.columns;
                
                updateColumnSelectors(currentColumns);
                
                alert(`Query executed: ${currentData.length} rows returned`);
            } catch (error) {
                alert('Error executing query: ' + error.response.data.message);
            }
        });

        function updateColumnSelectors(columns) {
            const selectors = ['x-axis-select', 'y-axis-select', 'group-by-select'];
            
            selectors.forEach(selectorId => {
                const selector = document.getElementById(selectorId);
                const currentValue = selector.value;
                
                selector.innerHTML = selectorId === 'group-by-select' ? 
                    '<option value="">None</option>' : 
                    '<option value="">Select Column</option>';
                
                columns.forEach(column => {
                    const option = document.createElement('option');
                    option.value = column;
                    option.textContent = column;
                    if (column === currentValue) option.selected = true;
                    selector.appendChild(option);
                });
            });
        }

        // Create chart
        document.getElementById('create-chart-btn').addEventListener('click', async function() {
            if (!currentData || currentData.length === 0) {
                alert('Please load data first');
                return;
            }
            
            const chartConfig = {
                data_source: document.getElementById('data-source-select').value,
                query: document.getElementById('sql-query').value || 
                       `SELECT * FROM ${document.getElementById('table-select').value} LIMIT 100`,
                chart_type: document.getElementById('chart-type-select').value,
                x_axis: document.getElementById('x-axis-select').value,
                y_axis: document.getElementById('y-axis-select').value,
                group_by: document.getElementById('group-by-select').value || null,
                title: document.getElementById('chart-title').value || 'Chart',
                width: 600,
                height: 400
            };
            
            if (!chartConfig.x_axis || !chartConfig.y_axis) {
                alert('Please select both X and Y axes');
                return;
            }
            
            try {
                const response = await axios.post('/api/chart', chartConfig);
                const chartData = response.data.chart.chart_data;
                
                // Create chart container
                chartCounter++;
                const chartId = `chart-${chartCounter}`;
                const chartContainer = document.createElement('div');
                chartContainer.className = 'chart-container bg-white';
                chartContainer.innerHTML = `<div id="${chartId}"></div>`;
                
                document.getElementById('charts-container').appendChild(chartContainer);
                
                // Render chart using Plotly
                Plotly.newPlot(chartId, chartData.data, chartData.layout, {responsive: true});
                
            } catch (error) {
                alert('Error creating chart: ' + error.response.data.message);
            }
        });

        // Generate insights
        document.getElementById('generate-insights-btn').addEventListener('click', async function() {
            const dataSource = document.getElementById('data-source-select').value;
            const table = document.getElementById('table-select').value;
            
            if (!dataSource || !table) {
                alert('Please select data source and table first');
                return;
            }
            
            try {
                const response = await axios.post('/api/insights', {
                    data_source: dataSource,
                    table: table
                });
                
                const insights = response.data.insights;
                displayInsights(insights);
                
            } catch (error) {
                alert('Error generating insights: ' + error.response.data.message);
            }
        });

        function displayInsights(insights) {
            const insightsPanel = document.getElementById('insights-panel');
            const insightsContent = document.getElementById('insights-content');
            
            insightsContent.innerHTML = '';
            
            insights.forEach(insight => {
                const insightDiv = document.createElement('div');
                insightDiv.className = `p-4 mb-3 rounded-lg border-l-4 ${
                    insight.type === 'error' ? 'bg-red-50 border-red-400' :
                    insight.type === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                    'bg-blue-50 border-blue-400'
                }`;
                
                insightDiv.innerHTML = `
                    <h4 class="font-semibold text-gray-800">${insight.title || insight.type}</h4>
                    <p class="text-gray-600 mt-1">${insight.message}</p>
                    ${insight.details ? `<pre class="text-xs mt-2 bg-gray-100 p-2 rounded">${JSON.stringify(insight.details, null, 2)}</pre>` : ''}
                `;
                
                insightsContent.appendChild(insightDiv);
            });
            
            insightsPanel.style.display = 'block';
        }

        // Save dashboard
        document.getElementById('save-dashboard-btn').addEventListener('click', function() {
            // This would collect all current charts and configuration
            alert('Dashboard save functionality would be implemented here');
        });

        // Export data
        document.getElementById('export-data-btn').addEventListener('click', function() {
            // This would trigger data export
            alert('Data export functionality would be implemented here');
        });
    </script>
</body>
</html>
"""

# Configuration example
if __name__ == "__main__":
    config = {
        'data_sources': {
            'financial_warehouse': {
                'connection_string': 'postgresql://user:password@localhost/financial_planning',
                'type': 'postgresql'
            }
        },
        'redis_url': 'redis://localhost:6379'
    }
    
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    with open('templates/analytics_portal.html', 'w') as f:
        f.write(ANALYTICS_PORTAL_HTML)
    
    # Initialize and run the analytics portal
    analytics = SelfServiceAnalytics(config)
    analytics.run(debug=True)
