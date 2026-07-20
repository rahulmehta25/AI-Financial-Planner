import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Upload, RefreshCw, TrendingUp, TrendingDown, AlertTriangle, BookOpen } from 'lucide-react';
import { portfolioApi } from '../services/api';

interface Position {
  symbol: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPL: number;
  gainPercent: number;
}

interface PortfolioSummary {
  totalCostBasis: number;
  totalMarketValue: number;
  totalUnrealizedPL: number;
  totalGainPercent: number;
}

interface PortfolioData {
  positions: Position[];
  summary: PortfolioSummary;
  lastUpdated: string;
}

interface HealthAnalysis {
  risk_factors: Array<{
    type: string;
    severity: string;
    message: string;
    education: string;
  }>;
  strengths: string[];
  action_items: Array<{
    priority: string;
    action: string;
    rationale: string;
  }>;
}

const PortfolioTracker: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [healthAnalysis, setHealthAnalysis] = useState<HealthAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Fetch portfolio data
  const fetchPortfolio = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await portfolioApi.getPortfolio();
      
      if (data.error) {
        setError('No portfolio loaded. Please load sample data.');
      } else {
        setPortfolio(data);
        // Fetch health analysis
        const healthData = await portfolioApi.getHealth();
        setHealthAnalysis(healthData);
      }
    } catch (err) {
      setError('Failed to fetch portfolio data. The API may be loading, please try again.');
    }
    setLoading(false);
  };

  // Load sample portfolio
  const loadSamplePortfolio = async () => {
    setLoading(true);
    try {
      // Since we're using serverless functions, the data is loaded automatically
      await fetchPortfolio();
    } catch (err) {
      setError('Failed to load portfolio data');
    }
    setLoading(false);
  };

  // Update prices
  const updatePrices = async () => {
    setLoading(true);
    try {
      await portfolioApi.updatePrices();
      await fetchPortfolio();
    } catch (err) {
      setError('Failed to update prices');
    }
    setLoading(false);
  };

  // Handle file upload
  const handleFileUpload = async () => {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    setLoading(true);
    try {
      await fetch('http://localhost:8002/upload-csv', {
        method: 'POST',
        body: formData
      });
      await fetchPortfolio();
      setSelectedFile(null);
    } catch (err) {
      setError('Failed to upload CSV file');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">Portfolio Tracker</h1>
        <p className="text-gray-600">Track your real portfolio with live market data</p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 mb-6">
        <Button onClick={loadSamplePortfolio} disabled={loading}>
          Load Sample Portfolio
        </Button>
        <Button onClick={updatePrices} disabled={loading || !portfolio}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Update Prices
        </Button>
        <div className="flex gap-2">
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            className="hidden"
            id="csv-upload"
          />
          <label htmlFor="csv-upload">
            <Button as="span" variant="outline" className="cursor-pointer">
              <Upload className="mr-2 h-4 w-4" />
              Choose CSV
            </Button>
          </label>
          {selectedFile && (
            <Button onClick={handleFileUpload} disabled={loading}>
              Upload {selectedFile.name}
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Alert className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Portfolio Summary */}
      {portfolio && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Value</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(portfolio.summary.totalMarketValue)}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Cost Basis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(portfolio.summary.totalCostBasis)}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Unrealized P&L</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${portfolio.summary.totalUnrealizedPL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(portfolio.summary.totalUnrealizedPL)}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Gain</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${portfolio.summary.totalGainPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(portfolio.summary.totalGainPercent)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Health Analysis */}
          {healthAnalysis && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Risk Factors */}
              {healthAnalysis.risk_factors.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <AlertTriangle className="mr-2 h-5 w-5 text-yellow-500" />
                      Risk Factors
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {healthAnalysis.risk_factors.map((risk, index) => (
                        <div key={index} className="border-l-4 border-yellow-500 pl-3">
                          <p className="font-medium">{risk.message}</p>
                          <p className="text-sm text-gray-600 mt-1">
                            <BookOpen className="inline h-3 w-3 mr-1" />
                            {risk.education}
                          </p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Action Items */}
              {healthAnalysis.action_items.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Recommended Actions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {healthAnalysis.action_items.map((item, index) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-3">
                          <div className="flex items-center">
                            <span className={`text-xs px-2 py-1 rounded mr-2 ${
                              item.priority === 'high' ? 'bg-red-100 text-red-700' :
                              item.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {item.priority}
                            </span>
                            <p className="font-medium">{item.action}</p>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{item.rationale}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Holdings Table */}
          <Card>
            <CardHeader>
              <CardTitle>Holdings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Symbol</th>
                      <th className="text-right p-2">Quantity</th>
                      <th className="text-right p-2">Avg Cost</th>
                      <th className="text-right p-2">Current Price</th>
                      <th className="text-right p-2">Market Value</th>
                      <th className="text-right p-2">Unrealized P&L</th>
                      <th className="text-right p-2">Gain %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.positions.map((position) => (
                      <tr key={position.symbol} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{position.symbol}</td>
                        <td className="text-right p-2">{position.quantity}</td>
                        <td className="text-right p-2">{formatCurrency(position.avgCost)}</td>
                        <td className="text-right p-2">{formatCurrency(position.currentPrice)}</td>
                        <td className="text-right p-2">{formatCurrency(position.marketValue)}</td>
                        <td className={`text-right p-2 font-medium ${position.unrealizedPL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(position.unrealizedPL)}
                        </td>
                        <td className={`text-right p-2 font-medium ${position.gainPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {position.gainPercent >= 0 ? <TrendingUp className="inline h-4 w-4 mr-1" /> : <TrendingDown className="inline h-4 w-4 mr-1" />}
                          {formatPercent(position.gainPercent)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-4 text-sm text-gray-500">
                Last updated: {new Date(portfolio.lastUpdated).toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Educational Note */}
      <Card className="mt-6">
        <CardContent className="pt-6">
          <p className="text-sm text-gray-600">
            <strong>Note:</strong> Market data is provided by yfinance with a 15-minute delay. 
            This tool is for educational purposes and portfolio tracking only. 
            Not investment advice.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default PortfolioTracker;