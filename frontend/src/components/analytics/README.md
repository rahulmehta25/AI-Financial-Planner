# Advanced Analytics Dashboard

A comprehensive portfolio analytics dashboard built with React, D3.js, and real-time WebSocket updates.

## Features

### 📊 Interactive D3.js Visualizations
- **Portfolio Performance Chart**: Interactive time series visualization with zoom, pan, and multiple chart types (line/area)
- **Correlation Matrix**: Interactive heat map showing asset correlations with customizable color schemes
- **Performance Attribution**: Waterfall charts and bar charts with drill-down capabilities for sector analysis
- **Risk Metrics Visualization**: Value at Risk (VaR) distribution charts and risk metric displays

### 📈 Portfolio Analysis
- **Portfolio Metrics**: Total return, annualized return, volatility, Sharpe ratio, Sortino ratio, max drawdown, beta, alpha
- **Risk Metrics**: VaR (95%, 99%), Conditional VaR, downside deviation, Ulcer index, Calmar ratio
- **Performance Attribution**: Asset class and sector-level attribution analysis with allocation and selection effects
- **Correlation Analysis**: Correlation matrices with statistical significance and diversification metrics

### ⚡ Real-time Data Updates
- **WebSocket Integration**: Real-time portfolio updates, market data, and risk alerts
- **Live Portfolio Value**: Real-time portfolio value updates with day change tracking
- **Risk Alerts**: Automated risk threshold monitoring with customizable alert levels
- **Market Data Feed**: Live price updates for portfolio holdings

### 🔧 Advanced Risk Management
- **Value at Risk (VaR)**: 95% and 99% confidence levels with distribution visualization
- **Stress Testing**: Scenario analysis with customizable market shock scenarios  
- **Monte Carlo Analysis**: Probabilistic analysis with confidence intervals
- **Drawdown Analysis**: Maximum drawdown calculation and visualization

### 📤 Export Functionality
- **Multiple Formats**: PNG, SVG, PDF, CSV, Excel export options
- **Chart Export**: High-quality image export with customizable dimensions
- **Data Export**: Raw data export with filtering options
- **Report Generation**: Comprehensive PDF reports with all analytics

### 🎛️ Interactive Features
- **Drill-down Analysis**: Click through from asset classes to sectors
- **Time Period Filtering**: 1M, 3M, 6M, 1Y, ALL time ranges
- **Dynamic Tooltips**: Detailed information on hover
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Components

### Core Components

#### `AnalyticsDashboard`
Main dashboard component that orchestrates all analytics features.

```tsx
import { AnalyticsDashboard } from '@/components/analytics';

<AnalyticsDashboard 
  portfolioId="portfolio-123"
  className="w-full"
/>
```

#### `PortfolioAnalyticsChart`
Interactive D3.js time series chart for portfolio performance.

```tsx
import { PortfolioAnalyticsChart } from '@/components/analytics';

<PortfolioAnalyticsChart
  data={timeSeriesData}
  metrics={portfolioMetrics}
  benchmarkData={benchmarkData}
  title="Portfolio Performance"
  height={500}
  onExport={handleExport}
/>
```

#### `CorrelationMatrix`
Interactive correlation heat map with multiple color schemes.

```tsx
import { CorrelationMatrix } from '@/components/analytics';

<CorrelationMatrix
  data={correlationData}
  title="Asset Correlation Matrix"
  onExport={handleExport}
  onCellClick={(asset1, asset2, correlation) => console.log(correlation)}
/>
```

#### `PerformanceAttributionChart`
Waterfall and bar charts for performance attribution analysis.

```tsx
import { PerformanceAttributionChart } from '@/components/analytics';

<PerformanceAttributionChart
  data={performanceAttributionData}
  title="Performance Attribution"
  onExport={handleExport}
  onDrillDown={(item) => console.log('Drill down:', item)}
/>
```

#### `RiskMetricsDashboard`
Comprehensive risk metrics display with VaR visualization.

```tsx
import { RiskMetricsDashboard } from '@/components/analytics';

<RiskMetricsDashboard
  riskMetrics={riskMetrics}
  portfolioMetrics={portfolioMetrics}
  returns={returnData}
  onExport={handleExport}
/>
```

### Supporting Components

#### `WebSocketProvider`
Provides real-time data updates via WebSocket connection.

```tsx
import { WebSocketProvider } from '@/components/analytics';

<WebSocketProvider autoConnect={true} url="ws://localhost:8000/ws/portfolio">
  <App />
</WebSocketProvider>
```

#### `ExportManager`
Handles export functionality for charts and data.

```tsx
import { ExportManager } from '@/components/analytics';

<ExportManager
  portfolioMetrics={portfolioMetrics}
  riskMetrics={riskMetrics}
  performanceAttribution={performanceAttribution}
  correlationData={correlationData}
  timeSeriesData={timeSeriesData}
/>
```

### Store Integration

The analytics dashboard uses Zustand for state management:

```tsx
import { useAnalyticsStore, useAnalyticsData, useAnalyticsActions } from '@/store/analyticsStore';

// Get all analytics data
const { portfolioMetrics, riskMetrics, isLoading, error } = useAnalyticsData();

// Get analytics actions
const { setPortfolioMetrics, refreshData, addAlert } = useAnalyticsActions();
```

## Data Types

### Portfolio Metrics
```typescript
interface PortfolioMetrics {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  beta: number;
  alpha: number;
  informationRatio: number;
  trackingError: number;
}
```

### Risk Metrics
```typescript
interface RiskMetrics {
  var95: number;
  var99: number;
  cvar95: number;
  cvar99: number;
  expectedShortfall: number;
  downsideDeviation: number;
  maxDrawdown: number;
  ulcerIndex: number;
  calmarRatio: number;
}
```

### Performance Attribution
```typescript
interface PerformanceAttribution {
  assetClass: string;
  allocation: number;
  benchmark: number;
  portfolioReturn: number;
  allocationEffect: number;
  selectionEffect: number;
  totalContribution: number;
  sectors?: SectorAttribution[];
}
```

## Usage Examples

### Basic Implementation
```tsx
import { AnalyticsDashboard } from '@/components/analytics';

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4">
        <AnalyticsDashboard portfolioId="demo-portfolio" />
      </div>
    </div>
  );
}
```

### With Custom Data
```tsx
import { AnalyticsDashboard } from '@/components/analytics';

const customData = {
  portfolioMetrics: {
    totalReturn: 12.5,
    annualizedReturn: 10.2,
    volatility: 16.8,
    sharpeRatio: 0.85,
    // ... other metrics
  },
  // ... other data
};

<AnalyticsDashboard 
  portfolioId="custom-portfolio"
  initialData={customData}
/>
```

### Real-time Updates
```tsx
import { WebSocketProvider, AnalyticsDashboard } from '@/components/analytics';

<WebSocketProvider autoConnect={true}>
  <AnalyticsDashboard portfolioId="live-portfolio" />
</WebSocketProvider>
```

## Styling and Themes

The dashboard supports both light and dark themes using Tailwind CSS:

```tsx
// Light theme (default)
<div className="bg-white dark:bg-gray-900">
  <AnalyticsDashboard />
</div>

// Dark theme
<div className="dark">
  <AnalyticsDashboard />
</div>
```

## Performance Considerations

- **Virtualization**: Large datasets are virtualized for performance
- **Debounced Updates**: Real-time updates are debounced to prevent excessive re-renders
- **Memoization**: Heavy calculations are memoized using React.useMemo
- **Lazy Loading**: Charts are lazy-loaded to improve initial page load
- **Data Pagination**: Large datasets are paginated for better performance

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Dependencies

- React 18.2+
- D3.js 7.8+
- Zustand 4.4+
- Tailwind CSS 3.3+
- Lucide React (icons)
- html2canvas (export functionality)

## Contributing

When adding new analytics features:

1. Add type definitions to `types/analytics.ts`
2. Create the component in `components/analytics/`
3. Add state management to `store/analyticsStore.ts`
4. Update the main `AnalyticsDashboard` component
5. Add export functionality to `ExportManager`
6. Update this README with usage examples

## License

This analytics dashboard is part of the AI Financial Planning System and follows the same license terms.