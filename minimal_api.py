#!/usr/bin/env python3
"""
Minimal API that works with ZERO dependencies beyond standard library
This ACTUALLY WORKS without any pip install
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse
from datetime import datetime

# Sample data - in production this would come from database
PORTFOLIO_DATA = {
    "AAPL": {
        "quantity": 50,
        "avg_cost": 150.50,
        "current_price": 195.50,  # Hardcoded for demo
        "total_cost": 7525.00,
        "market_value": 9775.00,
        "unrealized_gain": 2250.00,
        "realized_gains": 225.00
    },
    "GOOGL": {
        "quantity": 75,
        "avg_cost": 141.50,
        "current_price": 175.25,  # Hardcoded for demo
        "total_cost": 10612.50,
        "market_value": 13143.75,
        "unrealized_gain": 2531.25,
        "realized_gains": 0
    },
    "MSFT": {
        "quantity": 75,
        "avg_cost": 380.00,
        "current_price": 425.50,  # Hardcoded for demo
        "total_cost": 28500.00,
        "market_value": 31912.50,
        "unrealized_gain": 3412.50,
        "realized_gains": 0
    }
}

TRANSACTIONS = [
    {"date": "2024-01-15", "symbol": "AAPL", "action": "buy", "quantity": 100, "price": 150.50},
    {"date": "2024-01-20", "symbol": "GOOGL", "action": "buy", "quantity": 50, "price": 140.25},
    {"date": "2024-02-01", "symbol": "AAPL", "action": "sell", "quantity": 50, "price": 155.00},
    {"date": "2024-02-15", "symbol": "MSFT", "action": "buy", "quantity": 75, "price": 380.00},
    {"date": "2024-03-01", "symbol": "GOOGL", "action": "buy", "quantity": 25, "price": 145.00},
]

class PortfolioHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_html_response()
        elif parsed_path.path == '/api/portfolio':
            self.send_json_response(PORTFOLIO_DATA)
        elif parsed_path.path == '/api/transactions':
            self.send_json_response(TRANSACTIONS)
        elif parsed_path.path == '/api/summary':
            summary = self.calculate_summary()
            self.send_json_response(summary)
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def calculate_summary(self):
        """Calculate portfolio summary"""
        total_cost = sum(p['total_cost'] for p in PORTFOLIO_DATA.values())
        total_value = sum(p['market_value'] for p in PORTFOLIO_DATA.values())
        total_unrealized = sum(p['unrealized_gain'] for p in PORTFOLIO_DATA.values())
        total_realized = sum(p['realized_gains'] for p in PORTFOLIO_DATA.values())
        
        return {
            "total_cost": total_cost,
            "total_value": total_value,
            "total_unrealized_gain": total_unrealized,
            "total_realized_gain": total_realized,
            "total_gain": total_unrealized + total_realized,
            "total_return_percent": ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            "positions_count": len(PORTFOLIO_DATA)
        }
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_html_response(self):
        """Send HTML interface"""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Tracker - Working Demo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        h1 {
            color: white;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        h2 {
            color: #333;
            margin-top: 0;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        tr:hover {
            background: #f9fafb;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Portfolio Tracker</h1>
        
        <div class="card">
            <div id="summary" class="loading">Loading summary...</div>
        </div>
        
        <div class="card">
            <h2>Positions</h2>
            <div id="portfolio" class="loading">Loading portfolio...</div>
        </div>
        
        <div class="card">
            <h2>Recent Transactions</h2>
            <div id="transactions" class="loading">Loading transactions...</div>
        </div>
    </div>
    
    <script>
        async function loadData() {
            // Load summary
            const summaryRes = await fetch('/api/summary');
            const summary = await summaryRes.json();
            
            document.getElementById('summary').innerHTML = `
                <div class="summary-grid">
                    <div class="metric">
                        <div class="metric-value">$${summary.total_value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                        <div class="metric-label">Total Value</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">$${summary.total_cost.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                        <div class="metric-label">Total Cost</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value ${summary.total_gain >= 0 ? 'positive' : 'negative'}">
                            ${summary.total_gain >= 0 ? '+' : ''}$${summary.total_gain.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                        </div>
                        <div class="metric-label">Total Gain/Loss</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value ${summary.total_return_percent >= 0 ? 'positive' : 'negative'}">
                            ${summary.total_return_percent >= 0 ? '+' : ''}${summary.total_return_percent.toFixed(2)}%
                        </div>
                        <div class="metric-label">Total Return</div>
                    </div>
                </div>
            `;
            
            // Load portfolio
            const portfolioRes = await fetch('/api/portfolio');
            const portfolio = await portfolioRes.json();
            
            let portfolioHtml = '<table><thead><tr><th>Symbol</th><th>Quantity</th><th>Avg Cost</th><th>Current Price</th><th>Market Value</th><th>Unrealized G/L</th><th>% Change</th></tr></thead><tbody>';
            
            for (const [symbol, data] of Object.entries(portfolio)) {
                const percentChange = ((data.current_price - data.avg_cost) / data.avg_cost * 100);
                portfolioHtml += `
                    <tr>
                        <td><strong>${symbol}</strong></td>
                        <td>${data.quantity}</td>
                        <td>$${data.avg_cost.toFixed(2)}</td>
                        <td>$${data.current_price.toFixed(2)}</td>
                        <td>$${data.market_value.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td class="${data.unrealized_gain >= 0 ? 'positive' : 'negative'}">
                            ${data.unrealized_gain >= 0 ? '+' : ''}$${data.unrealized_gain.toLocaleString('en-US', {minimumFractionDigits: 2})}
                        </td>
                        <td class="${percentChange >= 0 ? 'positive' : 'negative'}">
                            ${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(2)}%
                        </td>
                    </tr>
                `;
            }
            
            portfolioHtml += '</tbody></table>';
            document.getElementById('portfolio').innerHTML = portfolioHtml;
            
            // Load transactions
            const transactionsRes = await fetch('/api/transactions');
            const transactions = await transactionsRes.json();
            
            let transactionsHtml = '<table><thead><tr><th>Date</th><th>Symbol</th><th>Action</th><th>Quantity</th><th>Price</th><th>Total</th></tr></thead><tbody>';
            
            for (const tx of transactions) {
                const total = tx.quantity * tx.price;
                transactionsHtml += `
                    <tr>
                        <td>${tx.date}</td>
                        <td><strong>${tx.symbol}</strong></td>
                        <td>${tx.action.toUpperCase()}</td>
                        <td>${tx.quantity}</td>
                        <td>$${tx.price.toFixed(2)}</td>
                        <td>$${total.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    </tr>
                `;
            }
            
            transactionsHtml += '</tbody></table>';
            document.getElementById('transactions').innerHTML = transactionsHtml;
        }
        
        // Load data on page load
        loadData();
        
        // Refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=8001):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, PortfolioHandler)
    print(f"✅ Portfolio Tracker API running at http://localhost:{port}")
    print(f"📊 Open http://localhost:{port} in your browser to see the interface")
    print(f"🔌 API endpoints:")
    print(f"   - http://localhost:{port}/api/portfolio")
    print(f"   - http://localhost:{port}/api/transactions")
    print(f"   - http://localhost:{port}/api/summary")
    print(f"\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Server stopped")

if __name__ == '__main__':
    run_server()