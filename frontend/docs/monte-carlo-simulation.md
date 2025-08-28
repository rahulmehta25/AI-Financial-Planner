# Monte Carlo Simulation Interface

## Overview

The Monte Carlo Simulation interface provides advanced portfolio analysis capabilities with interactive 3D visualization, statistical analysis, and comprehensive risk modeling. This implementation integrates with the backend's sophisticated Monte Carlo engine to deliver institutional-grade financial simulation tools.

## Features

### 1. Interactive Parameter Controls
- **Time Horizon**: 1-50 years simulation period
- **Investment Parameters**: Initial investment and monthly contributions
- **Market Parameters**: Expected return, volatility, risk-free rate
- **Advanced Settings**: Jump diffusion parameters, regime switching, number of simulations

### 2. 3D Visualization with Three.js
- Interactive 3D rendering of simulation paths
- Real-time rotation and perspective changes
- GPU-accelerated rendering when available
- Configurable path sampling for performance

### 3. Statistical Analysis
- **Probability Distributions**: Histogram, density, and cumulative distribution functions
- **Risk Metrics**: VaR, CVaR, Sharpe ratio, maximum drawdown, skewness, kurtosis
- **Confidence Intervals**: 10%, 25%, 50%, 75%, 90% bands
- **Success Rate Calculation**: Target achievement probability

### 4. Interactive Charts with Plotly
- Multiple visualization modes (distribution, density, cumulative, percentiles)
- Responsive design with zoom and pan capabilities
- Export functionality for charts and data

### 5. Scenario Comparison
- Side-by-side scenario analysis
- Parameter comparison tables
- Performance metrics comparison

## Component Architecture

```
MonteCarloSimulation.tsx (Main Page)
├── SimulationControls.tsx (Parameter Inputs)
├── SimulationResults.tsx (3D Visualization & Metrics)
└── ProbabilityChart.tsx (Statistical Analysis)
```

### SimulationControls.tsx
- Tabbed interface (Basic, Market, Advanced)
- Form validation and parameter constraints
- Preset configurations for different asset classes
- Real-time parameter validation with warnings

### SimulationResults.tsx
- Three.js 3D path visualization
- Plotly.js 2D charts for simulation paths
- Confidence interval bands
- Comprehensive risk metrics display
- Export functionality

### ProbabilityChart.tsx
- Multiple chart types for probability analysis
- Target amount analysis with success rates
- Interactive percentile visualization
- Risk metrics summary

## API Integration

### Service Layer (monteCarlo.ts)
```typescript
interface MonteCarloRequest {
  timeHorizon: number;
  initialInvestment: number;
  monthlyContribution: number;
  expectedReturn: number;
  volatility: number;
  riskFreeRate: number;
  numSimulations: number;
  jumpIntensity: number;
  jumpSizeMean: number;
  jumpSizeStd: number;
  enableRegimeSwitching: boolean;
  regimeDetection: boolean;
  targetAmount?: number;
  successThreshold: number;
}
```

### Backend Integration
- Maps frontend parameters to backend Monte Carlo engine
- Handles asynchronous simulation requests
- Provides simulation status tracking
- Supports result export in multiple formats

## Technical Implementation

### Dependencies
- **Three.js**: 3D visualization and WebGL rendering
- **Plotly.js**: Interactive charting and statistical plots
- **React Plotly.js**: React wrapper for Plotly integration
- **@types/three**: TypeScript definitions for Three.js

### Performance Considerations
- Path sampling limits (100 paths for 3D, 50 paths for 2D)
- Progressive loading for large simulations
- GPU acceleration detection and fallback
- Memory management for large datasets

### Accessibility
- Unique IDs for all interactive elements
- Proper ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility

## Usage Examples

### Basic Portfolio Simulation
1. Set time horizon (e.g., 30 years)
2. Configure initial investment ($100,000)
3. Set monthly contribution ($1,000)
4. Adjust expected return (8%) and volatility (15%)
5. Run 10,000 simulations
6. Analyze results and risk metrics

### Advanced Risk Modeling
1. Enable jump diffusion for black swan events
2. Configure regime switching for market cycles
3. Set target amount for success rate calculation
4. Increase simulation count for higher accuracy
5. Compare multiple scenarios side-by-side

### Asset Class Presets
- **Stocks**: High growth (10% return, 16% volatility)
- **Bonds**: Low risk (4% return, 5% volatility)  
- **Balanced**: Mixed portfolio (7% return, 12% volatility)
- **Aggressive**: Maximum growth (12% return, 20% volatility)

## Testing and Validation

### Parameter Validation
- Range constraints for all numerical inputs
- Logical validation (retirement age > current age)
- Warning system for extreme parameters
- Real-time feedback on parameter changes

### Performance Testing
- Simulation execution time monitoring
- Memory usage tracking
- Browser compatibility testing
- Mobile responsiveness validation

### Integration Testing
- Backend API connectivity
- Error handling and user feedback
- Export functionality validation
- Chart rendering across devices

## Future Enhancements

### Planned Features
- Historical backtesting integration
- Custom asset allocation modeling
- Monte Carlo with options strategies
- Real-time market data integration
- Advanced scenario stress testing

### Performance Improvements
- Web Workers for background processing
- Progressive simulation results loading
- Enhanced GPU acceleration
- Streaming results for large simulations

## Files Created

### Frontend Components
- `/frontend/src/pages/MonteCarloSimulation.tsx` - Main page component
- `/frontend/src/components/simulation/SimulationControls.tsx` - Parameter controls
- `/frontend/src/components/simulation/SimulationResults.tsx` - Results visualization
- `/frontend/src/components/simulation/ProbabilityChart.tsx` - Statistical charts
- `/frontend/src/services/monteCarlo.ts` - API service layer

### Backend Integration
- Enhanced `/backend/app/api/v1/endpoints/monte_carlo.py` - Added generic simulation endpoints
- Integration with existing `/backend/app/services/modeling/monte_carlo.py` - Advanced Monte Carlo engine

### Configuration
- Updated `/frontend/src/App.tsx` - Added route configuration
- Updated `/frontend/src/components/Navigation.tsx` - Added navigation item
- Updated `/frontend/package.json` - Added required dependencies

## Deployment Notes

### Required Dependencies
```bash
npm install three @types/three plotly.js react-plotly.js @types/plotly.js-dist-min
```

### Browser Compatibility
- Modern browsers with WebGL support
- Progressive enhancement for older browsers
- Mobile-responsive design for tablets and phones

### Performance Requirements
- Minimum 4GB RAM for large simulations
- WebGL-capable graphics for 3D visualization
- Modern CPU for real-time parameter updates

This comprehensive Monte Carlo simulation interface provides professional-grade financial modeling capabilities with an intuitive user experience, making advanced portfolio analysis accessible to both novice and expert users.