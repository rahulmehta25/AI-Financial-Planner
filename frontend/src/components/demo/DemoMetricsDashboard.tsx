import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface DemoMetrics {
  total_launches: number;
  total_completions: number;
  completion_rate: number;
  avg_demo_duration: number;
  system_performance: {
    avg_cpu_usage: number;
    avg_memory_usage: number;
  };
  recent_errors: Array<{
    timestamp: string;
    type: string;
    details: string;
  }>;
}

interface PerformanceData {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  demo_duration: number;
}

export const DemoMetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DemoMetrics | null>(null);
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);

  useEffect(() => {
    // Fetch metrics from backend API
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/demo/metrics');
        const data = await response.json();
        setMetrics(data.daily_metrics);
        setPerformanceData(data.performance_history);
      } catch (error) {
        console.error('Failed to fetch demo metrics:', error);
      }
    };

    // Initial fetch
    fetchMetrics();

    // Set up periodic refresh
    const intervalId = setInterval(fetchMetrics, 60000); // Refresh every minute

    // Cleanup interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  if (!metrics) return <div>Loading metrics...</div>;

  return (
    <div id="demo-metrics-dashboard" className="p-4 bg-white shadow-md rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Demo Performance Dashboard</h2>
      
      <div className="grid grid-cols-2 gap-4">
        {/* Performance Overview */}
        <div id="demo-performance-overview" className="bg-gray-100 p-4 rounded-lg">
          <h3 className="font-semibold mb-2">Performance Summary</h3>
          <ul>
            <li>Total Launches: {metrics.total_launches}</li>
            <li>Total Completions: {metrics.total_completions}</li>
            <li>Completion Rate: {metrics.completion_rate.toFixed(2)}%</li>
            <li>Avg Demo Duration: {metrics.avg_demo_duration.toFixed(2)} seconds</li>
          </ul>
        </div>

        {/* System Performance */}
        <div id="system-performance" className="bg-gray-100 p-4 rounded-lg">
          <h3 className="font-semibold mb-2">System Performance</h3>
          <ul>
            <li>Avg CPU Usage: {metrics.system_performance.avg_cpu_usage.toFixed(2)}%</li>
            <li>Avg Memory Usage: {metrics.system_performance.avg_memory_usage.toFixed(2)}%</li>
          </ul>
        </div>
      </div>

      {/* Performance Charts */}
      <div id="performance-charts" className="mt-4">
        <h3 className="font-semibold mb-2">Performance Trends</h3>
        <LineChart width={600} height={300} data={performanceData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="cpu_usage" stroke="#8884d8" activeDot={{ r: 8 }} />
          <Line type="monotone" dataKey="memory_usage" stroke="#82ca9d" />
          <Line type="monotone" dataKey="demo_duration" stroke="#ffc658" />
        </LineChart>
      </div>

      {/* Recent Errors */}
      <div id="recent-errors" className="mt-4 bg-red-50 p-4 rounded-lg">
        <h3 className="font-semibold text-red-600 mb-2">Recent Errors</h3>
        <ul>
          {metrics.recent_errors.map((error, index) => (
            <li key={index} className="mb-2 text-sm">
              <strong>{error.type}</strong>: {error.details} 
              <span className="text-gray-500 ml-2">{error.timestamp}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};