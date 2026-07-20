"""
Chart generation service for PDF reports using Plotly
"""

import io
import base64
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# Configure Plotly for static image generation
pio.kaleido.scope.mathjax = None

logger = logging.getLogger(__name__)


class ChartGeneratorService:
    """Service for generating financial charts for PDF reports"""
    
    def __init__(self):
        self.default_colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#3A86FF',
            'muted': '#6C757D'
        }
        
        self.chart_config = {
            'width': 800,
            'height': 400,
            'scale': 2,  # High DPI for PDF
            'format': 'png'
        }
    
    def generate_net_worth_projection(
        self, 
        projection_data: List[Dict],
        current_net_worth: float,
        title: str = "Net Worth Projection"
    ) -> str:
        """Generate net worth projection chart"""
        try:
            df = pd.DataFrame(projection_data)
            
            fig = go.Figure()
            
            # Add projection line
            fig.add_trace(go.Scatter(
                x=df['year'],
                y=df['net_worth'],
                mode='lines+markers',
                name='Projected Net Worth',
                line=dict(color=self.default_colors['primary'], width=3),
                marker=dict(size=6)
            ))
            
            # Add current net worth baseline
            fig.add_hline(
                y=current_net_worth,
                line_dash="dash",
                line_color=self.default_colors['muted'],
                annotation_text=f"Current: ${current_net_worth:,.0f}"
            )
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                xaxis_title="Year",
                yaxis_title="Net Worth ($)",
                yaxis=dict(tickformat='$,.0f'),
                template='plotly_white',
                showlegend=True,
                font=dict(family="Arial", size=12),
                margin=dict(l=60, r=60, t=80, b=60)
            )
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating net worth projection chart: {e}")
            return self._generate_error_chart("Net Worth Projection Error")
    
    def generate_goal_progress_chart(
        self, 
        goals_data: List[Dict],
        title: str = "Financial Goals Progress"
    ) -> str:
        """Generate goals progress chart"""
        try:
            if not goals_data:
                return self._generate_placeholder_chart("No Goals Data Available")
            
            df = pd.DataFrame(goals_data)
            
            fig = go.Figure()
            
            # Create horizontal bar chart
            colors = [self.default_colors['success'] if progress >= 75 
                     else self.default_colors['warning'] if progress >= 50 
                     else self.default_colors['primary'] 
                     for progress in df['progress_percentage']]
            
            fig.add_trace(go.Bar(
                y=df['name'],
                x=df['progress_percentage'],
                orientation='h',
                marker=dict(color=colors),
                text=[f"{p:.1f}%" for p in df['progress_percentage']],
                textposition='inside'
            ))
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                xaxis_title="Progress (%)",
                yaxis_title="Goals",
                xaxis=dict(range=[0, 100]),
                template='plotly_white',
                showlegend=False,
                font=dict(family="Arial", size=12),
                margin=dict(l=150, r=60, t=80, b=60)
            )
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating goal progress chart: {e}")
            return self._generate_error_chart("Goal Progress Error")
    
    def generate_asset_allocation_pie(
        self, 
        allocation_data: Dict[str, float],
        title: str = "Asset Allocation"
    ) -> str:
        """Generate asset allocation pie chart"""
        try:
            if not allocation_data:
                return self._generate_placeholder_chart("No Asset Data Available")
            
            labels = list(allocation_data.keys())
            values = list(allocation_data.values())
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(
                    colors=[self.default_colors['primary'], 
                           self.default_colors['secondary'],
                           self.default_colors['success'],
                           self.default_colors['warning'],
                           self.default_colors['info'],
                           self.default_colors['muted']][:len(labels)]
                ),
                textinfo='label+percent',
                textfont=dict(size=12)
            )])
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                template='plotly_white',
                showlegend=True,
                font=dict(family="Arial", size=12),
                margin=dict(l=60, r=60, t=80, b=60),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.01
                )
            )
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating asset allocation chart: {e}")
            return self._generate_error_chart("Asset Allocation Error")
    
    def generate_cash_flow_chart(
        self, 
        cash_flow_data: List[Dict],
        title: str = "Monthly Cash Flow"
    ) -> str:
        """Generate cash flow chart"""
        try:
            if not cash_flow_data:
                return self._generate_placeholder_chart("No Cash Flow Data Available")
            
            df = pd.DataFrame(cash_flow_data)
            
            fig = go.Figure()
            
            # Add income bars
            fig.add_trace(go.Bar(
                x=df['month'],
                y=df['income'],
                name='Income',
                marker_color=self.default_colors['success']
            ))
            
            # Add expense bars
            fig.add_trace(go.Bar(
                x=df['month'],
                y=[-exp for exp in df['expenses']],  # Negative for visual effect
                name='Expenses',
                marker_color=self.default_colors['warning']
            ))
            
            # Add net cash flow line
            net_flow = [inc - exp for inc, exp in zip(df['income'], df['expenses'])]
            fig.add_trace(go.Scatter(
                x=df['month'],
                y=net_flow,
                mode='lines+markers',
                name='Net Cash Flow',
                line=dict(color=self.default_colors['primary'], width=3),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                xaxis_title="Month",
                yaxis_title="Amount ($)",
                yaxis2=dict(
                    title="Net Cash Flow ($)",
                    overlaying='y',
                    side='right',
                    tickformat='$,.0f'
                ),
                yaxis=dict(tickformat='$,.0f'),
                template='plotly_white',
                showlegend=True,
                font=dict(family="Arial", size=12),
                margin=dict(l=60, r=80, t=80, b=60),
                barmode='relative'
            )
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating cash flow chart: {e}")
            return self._generate_error_chart("Cash Flow Error")
    
    def generate_monte_carlo_results(
        self, 
        simulation_results: Dict,
        title: str = "Monte Carlo Simulation Results"
    ) -> str:
        """Generate Monte Carlo simulation results chart"""
        try:
            if not simulation_results:
                return self._generate_placeholder_chart("No Simulation Data Available")
            
            # Extract percentile data
            years = simulation_results.get('years', [])
            p10 = simulation_results.get('percentile_10', [])
            p50 = simulation_results.get('percentile_50', [])
            p90 = simulation_results.get('percentile_90', [])
            
            fig = go.Figure()
            
            # Add confidence bands
            fig.add_trace(go.Scatter(
                x=years + years[::-1],
                y=p90 + p10[::-1],
                fill='toself',
                fillcolor='rgba(46, 134, 171, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='80% Confidence Band'
            ))
            
            # Add median line
            fig.add_trace(go.Scatter(
                x=years,
                y=p50,
                mode='lines',
                name='Median (50th percentile)',
                line=dict(color=self.default_colors['primary'], width=3)
            ))
            
            # Add percentile lines
            fig.add_trace(go.Scatter(
                x=years,
                y=p90,
                mode='lines',
                name='90th percentile',
                line=dict(color=self.default_colors['success'], width=2, dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=years,
                y=p10,
                mode='lines',
                name='10th percentile',
                line=dict(color=self.default_colors['warning'], width=2, dash='dash')
            ))
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                xaxis_title="Years",
                yaxis_title="Portfolio Value ($)",
                yaxis=dict(tickformat='$,.0f'),
                template='plotly_white',
                showlegend=True,
                font=dict(family="Arial", size=12),
                margin=dict(l=60, r=60, t=80, b=60)
            )
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating Monte Carlo chart: {e}")
            return self._generate_error_chart("Monte Carlo Simulation Error")
    
    def generate_risk_return_scatter(
        self, 
        portfolio_data: List[Dict],
        title: str = "Risk vs Return Analysis"
    ) -> str:
        """Generate risk vs return scatter plot"""
        try:
            if not portfolio_data:
                return self._generate_placeholder_chart("No Portfolio Data Available")
            
            df = pd.DataFrame(portfolio_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['risk'],
                y=df['return'],
                mode='markers+text',
                text=df['name'],
                textposition='top center',
                marker=dict(
                    size=12,
                    color=self.default_colors['primary'],
                    opacity=0.7
                ),
                name='Portfolios'
            ))
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                xaxis_title="Risk (Standard Deviation %)",
                yaxis_title="Expected Return (%)",
                template='plotly_white',
                showlegend=False,
                font=dict(family="Arial", size=12),
                margin=dict(l=60, r=60, t=80, b=60)
            )
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating risk-return chart: {e}")
            return self._generate_error_chart("Risk Return Analysis Error")
    
    def _fig_to_base64(self, fig: go.Figure) -> str:
        """Convert Plotly figure to base64 encoded string"""
        try:
            img_bytes = fig.to_image(
                format=self.chart_config['format'],
                width=self.chart_config['width'],
                height=self.chart_config['height'],
                scale=self.chart_config['scale']
            )
            
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error converting figure to base64: {e}")
            return self._generate_error_chart("Chart Generation Error")
    
    def _generate_error_chart(self, error_message: str) -> str:
        """Generate error placeholder chart"""
        fig = go.Figure()
        fig.add_annotation(
            text=error_message,
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            template='plotly_white',
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(l=60, r=60, t=80, b=60)
        )
        return self._fig_to_base64(fig)
    
    def _generate_placeholder_chart(self, message: str) -> str:
        """Generate placeholder chart when no data is available"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color=self.default_colors['muted'])
        )
        fig.update_layout(
            template='plotly_white',
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(l=60, r=60, t=80, b=60)
        )
        return self._fig_to_base64(fig)