"""
Self-Service Analytics Platform
Provides a flexible, API-driven analytics layer for business users
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc

from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS


@dataclass
class AnalyticsQuery:
    """Data class for analytics query configuration"""
    data_source: str
    query_type: str  # aggregation, time_series, cohort, etc.
    dimensions: List[str]
    measures: List[str]
    filters: Dict[str, Any]
    date_range: Dict[str, str]
    grouping: Optional[List[str]] = None
    sorting: Optional[List[Dict[str, str]]] = None
    limit: Optional[int] = None


@dataclass
class ChartConfig:
    """Chart configuration for visualizations"""
    chart_type: str  # line, bar, pie, scatter, heatmap, etc.
    title: str
    x_axis: str
    y_axis: Union[str, List[str]]
    color: Optional[str] = None
    size: Optional[str] = None
    facet: Optional[str] = None
    aggregation: Optional[str] = 'sum'


class DataConnector(ABC):
    """Abstract base class for data connectors"""
    
    @abstractmethod
    def connect(self) -> Any:
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def get_schema_info(self) -> Dict[str, Any]:
        pass


class PostgreSQLConnector(DataConnector):
    """PostgreSQL data connector"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = None
    
    def connect(self) -> Any:
        """Establish database connection"""
        try:
            self.engine = create_engine(self.connection_string)
            return self.engine
        except Exception as e:
            logging.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            if not self.engine:
                self.connect()
            
            df = pd.read_sql(text(query), self.engine)
            return df
        except Exception as e:
            logging.error(f"Query execution failed: {str(e)}")
            raise
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            schema_query = """
            SELECT 
                table_schema,
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns 
            WHERE table_schema IN ('dimensions', 'facts', 'marts', 'analytics')
            ORDER BY table_schema, table_name, ordinal_position
            """
            
            df = self.execute_query(schema_query)
            
            schema_info = {}
            for _, row in df.iterrows():
                schema = row['table_schema']
                table = row['table_name']
                
                if schema not in schema_info:
                    schema_info[schema] = {}
                
                if table not in schema_info[schema]:
                    schema_info[schema][table] = {
                        'columns': [],
                        'measures': [],
                        'dimensions': []
                    }
                
                column_info = {
                    'name': row['column_name'],
                    'type': row['data_type'],
                    'nullable': row['is_nullable'] == 'YES'
                }
                
                schema_info[schema][table]['columns'].append(column_info)
                
                # Categorize columns as measures or dimensions
                if row['data_type'] in ['numeric', 'decimal', 'float', 'double precision', 'integer', 'bigint']:
                    if any(keyword in row['column_name'].lower() for keyword in ['amount', 'value', 'count', 'sum', 'avg', 'total']):
                        schema_info[schema][table]['measures'].append(row['column_name'])
                    else:
                        schema_info[schema][table]['dimensions'].append(row['column_name'])
                else:
                    schema_info[schema][table]['dimensions'].append(row['column_name'])
            
            return schema_info
            
        except Exception as e:
            logging.error(f"Failed to get schema info: {str(e)}")
            raise


class QueryBuilder:
    """Builds SQL queries from analytics query configurations"""
    
    def __init__(self, connector: DataConnector):
        self.connector = connector
        self.schema_info = connector.get_schema_info()
    
    def build_query(self, analytics_query: AnalyticsQuery) -> str:
        """Build SQL query from analytics query configuration"""
        try:
            if analytics_query.query_type == 'aggregation':
                return self._build_aggregation_query(analytics_query)
            elif analytics_query.query_type == 'time_series':
                return self._build_time_series_query(analytics_query)
            elif analytics_query.query_type == 'cohort':
                return self._build_cohort_query(analytics_query)
            elif analytics_query.query_type == 'funnel':
                return self._build_funnel_query(analytics_query)
            else:
                raise ValueError(f"Unsupported query type: {analytics_query.query_type}")
                
        except Exception as e:
            logging.error(f"Query building failed: {str(e)}")
            raise
    
    def _build_aggregation_query(self, query: AnalyticsQuery) -> str:
        """Build aggregation query"""
        # Extract table from data source
        table = query.data_source
        
        # Build SELECT clause
        select_parts = []
        
        # Add dimensions
        for dim in query.dimensions:
            select_parts.append(dim)
        
        # Add measures with aggregation
        for measure in query.measures:
            if 'SUM(' in measure.upper():
                select_parts.append(measure)
            elif 'AVG(' in measure.upper():
                select_parts.append(measure)
            elif 'COUNT(' in measure.upper():
                select_parts.append(measure)
            else:
                # Default aggregation based on measure type
                select_parts.append(f"SUM({measure}) as {measure}")
        
        select_clause = "SELECT " + ", ".join(select_parts)
        
        # Build FROM clause
        from_clause = f"FROM {table}"
        
        # Build WHERE clause
        where_conditions = []
        
        # Add date range filter
        if query.date_range:
            start_date = query.date_range.get('start')
            end_date = query.date_range.get('end')
            date_column = query.date_range.get('column', 'date_key')
            
            if start_date:
                where_conditions.append(f"{date_column} >= '{start_date}'")
            if end_date:
                where_conditions.append(f"{date_column} <= '{end_date}'")
        
        # Add custom filters
        for filter_col, filter_val in query.filters.items():
            if isinstance(filter_val, list):
                filter_val_str = "', '".join(str(v) for v in filter_val)
                where_conditions.append(f"{filter_col} IN ('{filter_val_str}')")
            elif isinstance(filter_val, dict):
                # Range filter
                if 'min' in filter_val:
                    where_conditions.append(f"{filter_col} >= {filter_val['min']}")
                if 'max' in filter_val:
                    where_conditions.append(f"{filter_col} <= {filter_val['max']}")
            else:
                where_conditions.append(f"{filter_col} = '{filter_val}'")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Build GROUP BY clause
        group_by_clause = ""
        if query.dimensions:
            group_by_clause = "GROUP BY " + ", ".join(query.dimensions)
        
        # Build ORDER BY clause
        order_by_clause = ""
        if query.sorting:
            order_parts = []
            for sort_config in query.sorting:
                column = sort_config['column']
                direction = sort_config.get('direction', 'ASC')
                order_parts.append(f"{column} {direction}")
            order_by_clause = "ORDER BY " + ", ".join(order_parts)
        
        # Build LIMIT clause
        limit_clause = ""
        if query.limit:
            limit_clause = f"LIMIT {query.limit}"
        
        # Combine all parts
        sql_parts = [select_clause, from_clause, where_clause, group_by_clause, order_by_clause, limit_clause]
        sql_query = " ".join(part for part in sql_parts if part)
        
        return sql_query
    
    def _build_time_series_query(self, query: AnalyticsQuery) -> str:
        """Build time series query with date grouping"""
        base_query = self._build_aggregation_query(query)
        
        # Add time-based window functions for trends
        time_series_query = f"""
        WITH base_data AS (
            {base_query}
        ),
        time_series_with_trends AS (
            SELECT *,
                LAG({query.measures[0]}) OVER (ORDER BY {query.dimensions[0]}) as prev_value,
                AVG({query.measures[0]}) OVER (
                    ORDER BY {query.dimensions[0]} 
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as moving_avg_7,
                STDDEV({query.measures[0]}) OVER (
                    ORDER BY {query.dimensions[0]} 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) as rolling_stddev_30
            FROM base_data
        )
        SELECT *,
            CASE 
                WHEN prev_value IS NOT NULL 
                THEN ({query.measures[0]} - prev_value) / prev_value * 100 
                ELSE 0 
            END as percent_change,
            CASE 
                WHEN {query.measures[0]} > moving_avg_7 THEN 'Above Trend'
                WHEN {query.measures[0]} < moving_avg_7 THEN 'Below Trend'
                ELSE 'On Trend'
            END as trend_status
        FROM time_series_with_trends
        ORDER BY {query.dimensions[0]}
        """
        
        return time_series_query
    
    def _build_cohort_query(self, query: AnalyticsQuery) -> str:
        """Build cohort analysis query"""
        # This is a simplified cohort query template
        cohort_query = f"""
        WITH user_cohorts AS (
            SELECT 
                user_key,
                DATE_TRUNC('month', registration_date) as cohort_month
            FROM dimensions.dim_user
        ),
        user_activities AS (
            SELECT 
                t.user_key,
                uc.cohort_month,
                DATE_TRUNC('month', d.date_actual) as activity_month,
                EXTRACT(MONTH FROM AGE(d.date_actual, uc.cohort_month)) as period_number
            FROM facts.fact_transaction t
            JOIN dimensions.dim_date d ON t.date_key = d.date_key
            JOIN user_cohorts uc ON t.user_key = uc.user_key
        )
        SELECT 
            cohort_month,
            period_number,
            COUNT(DISTINCT user_key) as active_users,
            (SELECT COUNT(DISTINCT user_key) FROM user_cohorts WHERE cohort_month = ua.cohort_month) as cohort_size,
            COUNT(DISTINCT user_key)::float / 
            (SELECT COUNT(DISTINCT user_key) FROM user_cohorts WHERE cohort_month = ua.cohort_month) * 100 as retention_rate
        FROM user_activities ua
        GROUP BY cohort_month, period_number
        ORDER BY cohort_month, period_number
        """
        
        return cohort_query
    
    def _build_funnel_query(self, query: AnalyticsQuery) -> str:
        """Build funnel analysis query"""
        # Funnel analysis based on user activity stages
        funnel_query = f"""
        WITH user_stages AS (
            SELECT 
                user_key,
                CASE WHEN EXISTS (SELECT 1 FROM facts.fact_transaction WHERE user_key = u.user_key) 
                     THEN 1 ELSE 0 END as has_transaction,
                CASE WHEN EXISTS (SELECT 1 FROM facts.fact_portfolio_performance WHERE user_key = u.user_key) 
                     THEN 1 ELSE 0 END as has_portfolio,
                CASE WHEN registration_date IS NOT NULL THEN 1 ELSE 0 END as registered
            FROM dimensions.dim_user u
        )
        SELECT 
            'Registered' as stage,
            1 as stage_order,
            SUM(registered) as users
        FROM user_stages
        UNION ALL
        SELECT 
            'First Transaction' as stage,
            2 as stage_order,
            SUM(has_transaction) as users
        FROM user_stages
        UNION ALL
        SELECT 
            'Active Portfolio' as stage,
            3 as stage_order,
            SUM(has_portfolio) as users
        FROM user_stages
        ORDER BY stage_order
        """
        
        return funnel_query


class ChartGenerator:
    """Generates interactive charts using Plotly"""
    
    def __init__(self):
        self.default_colors = px.colors.qualitative.Set3
    
    def create_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create chart based on configuration"""
        try:
            chart_type = config.chart_type.lower()
            
            if chart_type == 'line':
                return self._create_line_chart(df, config)
            elif chart_type == 'bar':
                return self._create_bar_chart(df, config)
            elif chart_type == 'pie':
                return self._create_pie_chart(df, config)
            elif chart_type == 'scatter':
                return self._create_scatter_chart(df, config)
            elif chart_type == 'heatmap':
                return self._create_heatmap(df, config)
            elif chart_type == 'histogram':
                return self._create_histogram(df, config)
            elif chart_type == 'box':
                return self._create_box_plot(df, config)
            elif chart_type == 'funnel':
                return self._create_funnel_chart(df, config)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
                
        except Exception as e:
            logging.error(f"Chart creation failed: {str(e)}")
            raise
    
    def _create_line_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create line chart"""
        fig = px.line(
            df, 
            x=config.x_axis, 
            y=config.y_axis,
            color=config.color,
            title=config.title
        )
        
        fig.update_layout(
            xaxis_title=config.x_axis,
            yaxis_title=config.y_axis if isinstance(config.y_axis, str) else "Value",
            hovermode='x unified'
        )
        
        return fig
    
    def _create_bar_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bar chart"""
        fig = px.bar(
            df,
            x=config.x_axis,
            y=config.y_axis,
            color=config.color,
            title=config.title
        )
        
        fig.update_layout(
            xaxis_title=config.x_axis,
            yaxis_title=config.y_axis if isinstance(config.y_axis, str) else "Value"
        )
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create pie chart"""
        fig = px.pie(
            df,
            names=config.x_axis,
            values=config.y_axis,
            title=config.title
        )
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create scatter plot"""
        fig = px.scatter(
            df,
            x=config.x_axis,
            y=config.y_axis,
            color=config.color,
            size=config.size,
            title=config.title
        )
        
        return fig
    
    def _create_heatmap(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create heatmap"""
        # Pivot data for heatmap
        if config.color:
            pivot_df = df.pivot(index=config.x_axis, columns=config.y_axis, values=config.color)
        else:
            pivot_df = df.pivot(index=config.x_axis, columns=config.y_axis, values=df.columns[-1])
        
        fig = px.imshow(
            pivot_df,
            title=config.title,
            aspect="auto"
        )
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create histogram"""
        fig = px.histogram(
            df,
            x=config.x_axis,
            color=config.color,
            title=config.title
        )
        
        return fig
    
    def _create_box_plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create box plot"""
        fig = px.box(
            df,
            x=config.x_axis,
            y=config.y_axis,
            color=config.color,
            title=config.title
        )
        
        return fig
    
    def _create_funnel_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create funnel chart"""
        fig = go.Figure(go.Funnel(
            y=df[config.x_axis],
            x=df[config.y_axis],
            textinfo="value+percent initial"
        ))
        
        fig.update_layout(title=config.title)
        
        return fig


class SelfServiceAnalytics:
    """Main self-service analytics platform"""
    
    def __init__(self, connection_string: str):
        self.connector = PostgreSQLConnector(connection_string)
        self.query_builder = QueryBuilder(self.connector)
        self.chart_generator = ChartGenerator()
        
        # Initialize Flask app for API
        self.app = Flask(__name__)
        CORS(self.app)
        self.api = Api(self.app, doc='/api/')
        
        # Setup API routes
        self._setup_api_routes()
    
    def _setup_api_routes(self):
        """Setup REST API routes"""
        
        @self.api.route('/schema')
        class SchemaInfo(Resource):
            def get(self):
                """Get database schema information"""
                try:
                    schema_info = self.connector.get_schema_info()
                    return {'status': 'success', 'data': schema_info}
                except Exception as e:
                    return {'status': 'error', 'message': str(e)}, 500
        
        @self.api.route('/query')
        class ExecuteQuery(Resource):
            def post(self):
                """Execute analytics query"""
                try:
                    query_config = request.get_json()
                    analytics_query = AnalyticsQuery(**query_config)
                    
                    sql_query = self.query_builder.build_query(analytics_query)
                    df = self.connector.execute_query(sql_query)
                    
                    # Convert DataFrame to JSON
                    result = df.to_dict('records')
                    
                    return {
                        'status': 'success',
                        'data': result,
                        'sql_query': sql_query,
                        'row_count': len(result)
                    }
                except Exception as e:
                    return {'status': 'error', 'message': str(e)}, 500
        
        @self.api.route('/chart')
        class GenerateChart(Resource):
            def post(self):
                """Generate chart from data"""
                try:
                    request_data = request.get_json()
                    
                    # Execute query first
                    query_config = request_data['query']
                    chart_config_data = request_data['chart']
                    
                    analytics_query = AnalyticsQuery(**query_config)
                    chart_config = ChartConfig(**chart_config_data)
                    
                    sql_query = self.query_builder.build_query(analytics_query)
                    df = self.connector.execute_query(sql_query)
                    
                    # Generate chart
                    fig = self.chart_generator.create_chart(df, chart_config)
                    
                    # Convert to JSON for frontend
                    chart_json = fig.to_json()
                    
                    return {
                        'status': 'success',
                        'chart': chart_json,
                        'data_points': len(df)
                    }
                except Exception as e:
                    return {'status': 'error', 'message': str(e)}, 500
    
    def create_dashboard_app(self) -> dash.Dash:
        """Create Dash dashboard application"""
        dashboard_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        # Dashboard layout
        dashboard_app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("Financial Analytics Dashboard", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Query Builder"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Data Source"),
                                    dcc.Dropdown(
                                        id='data-source-dropdown',
                                        options=[
                                            {'label': 'Portfolio Performance', 'value': 'facts.fact_portfolio_performance'},
                                            {'label': 'Transactions', 'value': 'facts.fact_transaction'},
                                            {'label': 'Customer Segments', 'value': 'analytics.customer_segments'}
                                        ],
                                        value='facts.fact_portfolio_performance'
                                    )
                                ], width=6),
                                
                                dbc.Col([
                                    dbc.Label("Chart Type"),
                                    dcc.Dropdown(
                                        id='chart-type-dropdown',
                                        options=[
                                            {'label': 'Line Chart', 'value': 'line'},
                                            {'label': 'Bar Chart', 'value': 'bar'},
                                            {'label': 'Scatter Plot', 'value': 'scatter'},
                                            {'label': 'Pie Chart', 'value': 'pie'}
                                        ],
                                        value='line'
                                    )
                                ], width=6)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Date Range"),
                                    dcc.DatePickerRange(
                                        id='date-range-picker',
                                        start_date=datetime.now() - timedelta(days=30),
                                        end_date=datetime.now()
                                    )
                                ], width=12)
                            ], className="mt-3"),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("Generate Chart", id="generate-btn", color="primary", className="mt-3")
                                ])
                            ])
                        ])
                    ])
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        id="loading-chart",
                        children=[dcc.Graph(id="analytics-chart")],
                        type="default"
                    )
                ], width=12)
            ], className="mt-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Data Table"),
                        dbc.CardBody([
                            html.Div(id="data-table")
                        ])
                    ])
                ], width=12)
            ], className="mt-4")
        ], fluid=True)
        
        # Dashboard callbacks
        @dashboard_app.callback(
            [Output('analytics-chart', 'figure'),
             Output('data-table', 'children')],
            [Input('generate-btn', 'n_clicks')],
            [State('data-source-dropdown', 'value'),
             State('chart-type-dropdown', 'value'),
             State('date-range-picker', 'start_date'),
             State('date-range-picker', 'end_date')]
        )
        def update_dashboard(n_clicks, data_source, chart_type, start_date, end_date):
            if n_clicks is None:
                return {}, "Click 'Generate Chart' to view data"
            
            try:
                # Create sample query configuration
                query_config = AnalyticsQuery(
                    data_source=data_source,
                    query_type='aggregation',
                    dimensions=['date_key'],
                    measures=['total_value'],
                    filters={},
                    date_range={
                        'start': start_date,
                        'end': end_date,
                        'column': 'date_key'
                    }
                )
                
                # Execute query
                sql_query = self.query_builder.build_query(query_config)
                df = self.connector.execute_query(sql_query)
                
                if df.empty:
                    return {}, "No data found for the selected criteria"
                
                # Generate chart
                chart_config = ChartConfig(
                    chart_type=chart_type,
                    title=f"{data_source} Analytics",
                    x_axis=df.columns[0],
                    y_axis=df.columns[1] if len(df.columns) > 1 else df.columns[0]
                )
                
                fig = self.chart_generator.create_chart(df, chart_config)
                
                # Create data table
                table_data = df.head(100).to_dict('records')
                table = dbc.Table.from_dataframe(
                    df.head(100), 
                    striped=True, 
                    bordered=True, 
                    hover=True,
                    responsive=True
                )
                
                return fig, table
                
            except Exception as e:
                error_fig = go.Figure().add_annotation(
                    text=f"Error: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False
                )
                return error_fig, f"Error: {str(e)}"
        
        return dashboard_app
    
    def run_api_server(self, host='0.0.0.0', port=5000, debug=False):
        """Run the API server"""
        self.app.run(host=host, port=port, debug=debug)
    
    def run_dashboard(self, host='0.0.0.0', port=8050, debug=False):
        """Run the dashboard server"""
        dashboard_app = self.create_dashboard_app()
        dashboard_app.run_server(host=host, port=port, debug=debug)


# Example usage and configuration
if __name__ == "__main__":
    # Database connection string
    connection_string = "postgresql://username:password@localhost:5432/financial_dw"
    
    # Initialize self-service analytics platform
    analytics_platform = SelfServiceAnalytics(connection_string)
    
    # Run API server (in production, use WSGI server like Gunicorn)
    # analytics_platform.run_api_server(debug=True)
    
    # Run dashboard (in production, deploy as separate application)
    analytics_platform.run_dashboard(debug=True)