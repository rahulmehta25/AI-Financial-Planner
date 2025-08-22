'use client';

import React, { useState, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ExportOptions,
  PortfolioMetrics,
  RiskMetrics,
  PerformanceAttribution,
  CorrelationData,
  TimeSeriesData,
} from '@/types/analytics';
import { 
  Download, 
  FileImage, 
  FileText, 
  File,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import html2canvas from 'html2canvas';

interface ExportManagerProps {
  portfolioMetrics?: PortfolioMetrics;
  riskMetrics?: RiskMetrics;
  performanceAttribution?: PerformanceAttribution[];
  correlationData?: CorrelationData;
  timeSeriesData?: TimeSeriesData[];
  className?: string;
}

interface ExportJob {
  id: string;
  type: ExportOptions['format'];
  status: 'pending' | 'processing' | 'completed' | 'error';
  filename: string;
  downloadUrl?: string;
  error?: string;
  progress?: number;
}

export const ExportManager: React.FC<ExportManagerProps> = ({
  portfolioMetrics,
  riskMetrics,
  performanceAttribution,
  correlationData,
  timeSeriesData,
  className = '',
}) => {
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [selectedFormat, setSelectedFormat] = useState<ExportOptions['format']>('png');
  const [selectedQuality, setSelectedQuality] = useState<'low' | 'medium' | 'high'>('high');
  const [includeData, setIncludeData] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const jobIdCounter = useRef(0);

  // Create export job
  const createExportJob = useCallback((format: ExportOptions['format'], filename: string): ExportJob => {
    const id = `export-${++jobIdCounter.current}`;
    return {
      id,
      type: format,
      status: 'pending',
      filename,
      progress: 0
    };
  }, []);

  // Update export job
  const updateExportJob = useCallback((id: string, updates: Partial<ExportJob>) => {
    setExportJobs(prev => prev.map(job => 
      job.id === id ? { ...job, ...updates } : job
    ));
  }, []);

  // Export as PNG/SVG
  const exportAsImage = useCallback(async (format: 'png' | 'svg', elementId?: string) => {
    const job = createExportJob(format, `analytics-${format}-${Date.now()}`);
    setExportJobs(prev => [job, ...prev]);
    updateExportJob(job.id, { status: 'processing', progress: 10 });

    try {
      let element: HTMLElement | null = null;
      
      if (elementId) {
        element = document.getElementById(elementId);
      } else {
        // Find the main analytics container
        element = document.querySelector('[data-analytics-container]') as HTMLElement ||
                 document.querySelector('.analytics-dashboard') as HTMLElement ||
                 document.body;
      }

      if (!element) {
        throw new Error('Element not found for export');
      }

      updateExportJob(job.id, { progress: 30 });

      if (format === 'svg') {
        // Export as SVG
        const svgElements = element.querySelectorAll('svg');
        if (svgElements.length === 0) {
          throw new Error('No SVG elements found');
        }

        // Create a combined SVG
        const combinedSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        combinedSvg.setAttribute('width', '1200');
        combinedSvg.setAttribute('height', '800');
        combinedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

        let yOffset = 0;
        svgElements.forEach((svg, index) => {
          const clonedSvg = svg.cloneNode(true) as SVGElement;
          const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
          g.setAttribute('transform', `translate(0, ${yOffset})`);
          
          // Copy all children to the group
          while (clonedSvg.firstChild) {
            g.appendChild(clonedSvg.firstChild);
          }
          
          combinedSvg.appendChild(g);
          yOffset += 300; // Space between charts
        });

        updateExportJob(job.id, { progress: 70 });

        const svgData = new XMLSerializer().serializeToString(combinedSvg);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(svgBlob);
        
        updateExportJob(job.id, { 
          status: 'completed', 
          progress: 100, 
          downloadUrl: url,
          filename: `${job.filename}.svg`
        });

      } else {
        // Export as PNG using html2canvas
        updateExportJob(job.id, { progress: 50 });
        
        const canvas = await html2canvas(element, {
          quality: selectedQuality === 'high' ? 1 : selectedQuality === 'medium' ? 0.7 : 0.5,
          scale: selectedQuality === 'high' ? 2 : 1,
          backgroundColor: '#ffffff',
          useCORS: true,
          allowTaint: true,
        });

        updateExportJob(job.id, { progress: 80 });

        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            updateExportJob(job.id, { 
              status: 'completed', 
              progress: 100, 
              downloadUrl: url,
              filename: `${job.filename}.png`
            });
          } else {
            throw new Error('Failed to create image blob');
          }
        }, 'image/png', selectedQuality === 'high' ? 1 : 0.8);
      }

    } catch (error) {
      console.error('Export error:', error);
      updateExportJob(job.id, { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Export failed' 
      });
    }
  }, [createExportJob, updateExportJob, selectedQuality]);

  // Export as CSV
  const exportAsCSV = useCallback(async (dataType: 'all' | 'portfolio' | 'risk' | 'attribution' | 'correlation' | 'timeseries') => {
    const job = createExportJob('csv', `analytics-${dataType}-${Date.now()}`);
    setExportJobs(prev => [job, ...prev]);
    updateExportJob(job.id, { status: 'processing', progress: 20 });

    try {
      let csvContent = '';
      
      switch (dataType) {
        case 'portfolio':
          if (portfolioMetrics) {
            csvContent = 'Metric,Value\n';
            Object.entries(portfolioMetrics).forEach(([key, value]) => {
              csvContent += `${key},${value}\n`;
            });
          }
          break;

        case 'risk':
          if (riskMetrics) {
            csvContent = 'Risk Metric,Value\n';
            Object.entries(riskMetrics).forEach(([key, value]) => {
              csvContent += `${key},${value}\n`;
            });
          }
          break;

        case 'attribution':
          if (performanceAttribution) {
            csvContent = 'Asset Class,Allocation Effect,Selection Effect,Total Contribution\n';
            performanceAttribution.forEach(item => {
              csvContent += `${item.assetClass},${item.allocationEffect},${item.selectionEffect},${item.totalContribution}\n`;
            });
          }
          break;

        case 'correlation':
          if (correlationData) {
            csvContent = 'Asset 1,Asset 2,Correlation\n';
            for (let i = 0; i < correlationData.assets.length; i++) {
              for (let j = 0; j < correlationData.assets.length; j++) {
                csvContent += `${correlationData.assets[i]},${correlationData.assets[j]},${correlationData.matrix[i][j]}\n`;
              }
            }
          }
          break;

        case 'timeseries':
          if (timeSeriesData) {
            csvContent = 'Date,Value,Label\n';
            timeSeriesData.forEach(item => {
              csvContent += `${item.date.toISOString()},${item.value},${item.label || ''}\n`;
            });
          }
          break;

        case 'all':
          // Combine all data
          csvContent = '=== PORTFOLIO METRICS ===\n';
          if (portfolioMetrics) {
            Object.entries(portfolioMetrics).forEach(([key, value]) => {
              csvContent += `${key},${value}\n`;
            });
          }
          csvContent += '\n=== RISK METRICS ===\n';
          if (riskMetrics) {
            Object.entries(riskMetrics).forEach(([key, value]) => {
              csvContent += `${key},${value}\n`;
            });
          }
          if (performanceAttribution) {
            csvContent += '\n=== PERFORMANCE ATTRIBUTION ===\n';
            csvContent += 'Asset Class,Allocation Effect,Selection Effect,Total Contribution\n';
            performanceAttribution.forEach(item => {
              csvContent += `${item.assetClass},${item.allocationEffect},${item.selectionEffect},${item.totalContribution}\n`;
            });
          }
          break;
      }

      updateExportJob(job.id, { progress: 80 });

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      
      updateExportJob(job.id, { 
        status: 'completed', 
        progress: 100, 
        downloadUrl: url,
        filename: `${job.filename}.csv`
      });

    } catch (error) {
      console.error('CSV export error:', error);
      updateExportJob(job.id, { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'CSV export failed' 
      });
    }
  }, [createExportJob, updateExportJob, portfolioMetrics, riskMetrics, performanceAttribution, correlationData, timeSeriesData]);

  // Export as PDF (simplified version)
  const exportAsPDF = useCallback(async () => {
    const job = createExportJob('pdf', `analytics-report-${Date.now()}`);
    setExportJobs(prev => [job, ...prev]);
    updateExportJob(job.id, { status: 'processing', progress: 20 });

    try {
      // For now, we'll create a simple HTML report and convert to PDF
      // In a real implementation, you'd use a PDF library like jsPDF or puppeteer
      
      let htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Analytics Report</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
            .section { margin-bottom: 30px; }
            .metric { display: flex; justify-content: space-between; margin: 5px 0; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Portfolio Analytics Report</h1>
            <p>Generated on: ${new Date().toLocaleDateString()}</p>
          </div>
      `;

      if (portfolioMetrics) {
        htmlContent += `
          <div class="section">
            <h2>Portfolio Metrics</h2>
            <div class="metric"><span>Total Return:</span><span>${portfolioMetrics.totalReturn.toFixed(2)}%</span></div>
            <div class="metric"><span>Annualized Return:</span><span>${portfolioMetrics.annualizedReturn.toFixed(2)}%</span></div>
            <div class="metric"><span>Volatility:</span><span>${portfolioMetrics.volatility.toFixed(2)}%</span></div>
            <div class="metric"><span>Sharpe Ratio:</span><span>${portfolioMetrics.sharpeRatio.toFixed(2)}</span></div>
            <div class="metric"><span>Sortino Ratio:</span><span>${portfolioMetrics.sortinoRatio.toFixed(2)}</span></div>
            <div class="metric"><span>Max Drawdown:</span><span>${portfolioMetrics.maxDrawdown.toFixed(2)}%</span></div>
          </div>
        `;
      }

      if (riskMetrics) {
        htmlContent += `
          <div class="section">
            <h2>Risk Metrics</h2>
            <div class="metric"><span>VaR (95%):</span><span>${riskMetrics.var95.toFixed(2)}%</span></div>
            <div class="metric"><span>VaR (99%):</span><span>${riskMetrics.var99.toFixed(2)}%</span></div>
            <div class="metric"><span>CVaR (95%):</span><span>${riskMetrics.cvar95.toFixed(2)}%</span></div>
            <div class="metric"><span>CVaR (99%):</span><span>${riskMetrics.cvar99.toFixed(2)}%</span></div>
          </div>
        `;
      }

      if (performanceAttribution) {
        htmlContent += `
          <div class="section">
            <h2>Performance Attribution</h2>
            <table>
              <tr><th>Asset Class</th><th>Allocation Effect</th><th>Selection Effect</th><th>Total Contribution</th></tr>
        `;
        performanceAttribution.forEach(item => {
          htmlContent += `
            <tr>
              <td>${item.assetClass}</td>
              <td>${item.allocationEffect.toFixed(3)}%</td>
              <td>${item.selectionEffect.toFixed(3)}%</td>
              <td>${item.totalContribution.toFixed(3)}%</td>
            </tr>
          `;
        });
        htmlContent += '</table></div>';
      }

      htmlContent += '</body></html>';

      updateExportJob(job.id, { progress: 80 });

      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      
      updateExportJob(job.id, { 
        status: 'completed', 
        progress: 100, 
        downloadUrl: url,
        filename: `${job.filename}.html`
      });

    } catch (error) {
      console.error('PDF export error:', error);
      updateExportJob(job.id, { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'PDF export failed' 
      });
    }
  }, [createExportJob, updateExportJob, portfolioMetrics, riskMetrics, performanceAttribution]);

  // Handle export
  const handleExport = useCallback(async (format: ExportOptions['format'], elementId?: string) => {
    setIsExporting(true);
    try {
      switch (format) {
        case 'png':
        case 'svg':
          await exportAsImage(format, elementId);
          break;
        case 'csv':
          await exportAsCSV('all');
          break;
        case 'pdf':
          await exportAsPDF();
          break;
        default:
          throw new Error(`Unsupported format: ${format}`);
      }
    } finally {
      setIsExporting(false);
    }
  }, [exportAsImage, exportAsCSV, exportAsPDF]);

  // Download file
  const downloadFile = useCallback((job: ExportJob) => {
    if (job.downloadUrl) {
      const link = document.createElement('a');
      link.href = job.downloadUrl;
      link.download = job.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, []);

  // Clear completed jobs
  const clearCompleted = useCallback(() => {
    exportJobs.forEach(job => {
      if (job.downloadUrl) {
        URL.revokeObjectURL(job.downloadUrl);
      }
    });
    setExportJobs(prev => prev.filter(job => job.status === 'processing'));
  }, [exportJobs]);

  const getStatusIcon = (status: ExportJob['status']) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <File className="h-4 w-4 text-gray-600" />;
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      <div className="space-y-6">
        {/* Export Controls */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Export Analytics
          </h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-4">
            <Select value={selectedFormat} onValueChange={(value: any) => setSelectedFormat(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="png">PNG Image</SelectItem>
                <SelectItem value="svg">SVG Vector</SelectItem>
                <SelectItem value="pdf">PDF Report</SelectItem>
                <SelectItem value="csv">CSV Data</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedQuality} onValueChange={(value: any) => setSelectedQuality(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low Quality</SelectItem>
                <SelectItem value="medium">Medium Quality</SelectItem>
                <SelectItem value="high">High Quality</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="includeData"
                checked={includeData}
                onChange={(e) => setIncludeData(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="includeData" className="text-sm text-gray-600 dark:text-gray-400">
                Include Raw Data
              </label>
            </div>

            <Button
              onClick={() => handleExport(selectedFormat)}
              disabled={isExporting}
              className="w-full"
            >
              {isExporting ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Export
            </Button>
          </div>

          {/* Quick Export Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportAsCSV('portfolio')}
              disabled={isExporting || !portfolioMetrics}
            >
              <FileText className="h-4 w-4 mr-1" />
              Portfolio CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportAsCSV('risk')}
              disabled={isExporting || !riskMetrics}
            >
              <FileText className="h-4 w-4 mr-1" />
              Risk CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportAsImage('png')}
              disabled={isExporting}
            >
              <FileImage className="h-4 w-4 mr-1" />
              Screenshot
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportAsPDF()}
              disabled={isExporting}
            >
              <File className="h-4 w-4 mr-1" />
              Full Report
            </Button>
          </div>
        </div>

        {/* Export Jobs */}
        {exportJobs.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100">
                Export History
              </h4>
              <Button
                variant="outline"
                size="sm"
                onClick={clearCompleted}
                disabled={!exportJobs.some(job => job.status === 'completed')}
              >
                Clear Completed
              </Button>
            </div>

            <div className="space-y-2">
              {exportJobs.slice(0, 5).map(job => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {job.filename}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        {job.type.toUpperCase()} • {job.status}
                        {job.error && ` • ${job.error}`}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {job.status === 'processing' && job.progress && (
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        {job.progress}%
                      </div>
                    )}
                    {job.status === 'completed' && job.downloadUrl && (
                      <Button
                        size="sm"
                        onClick={() => downloadFile(job)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ExportManager;