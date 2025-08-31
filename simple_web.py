#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLE WEB INTERFACE for Portfolio Tracker
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
from portfolio_tracker import PortfolioTracker

app = FastAPI(title="Simple Portfolio Tracker", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global tracker instance
tracker = PortfolioTracker()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple HTML interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Portfolio Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            h1 { color: #333; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #4CAF50; color: white; }
            .positive { color: green; font-weight: bold; }
            .negative { color: red; font-weight: bold; }
            .summary { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
            button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            button:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Portfolio Tracker</h1>
            
            <div class="summary">
                <h2>Quick Actions</h2>
                <button onclick="loadSample()">Load Sample Portfolio</button>
                <button onclick="updatePrices()">Update Prices</button>
                <button onclick="refreshData()">Refresh Display</button>
            </div>
            
            <div id="portfolio"></div>
        </div>
        
        <script>
            async function loadSample() {
                const response = await fetch('/load-sample');
                const data = await response.json();
                alert(data.message);
                refreshData();
            }
            
            async function updatePrices() {
                const response = await fetch('/update-prices', {method: 'POST'});
                const data = await response.json();
                alert(data.message);
                refreshData();
            }
            
            async function refreshData() {
                const response = await fetch('/portfolio');
                const data = await response.json();
                displayPortfolio(data);
            }
            
            function displayPortfolio(data) {
                if (data.error) {
                    document.getElementById('portfolio').innerHTML = '<p>No portfolio loaded. Click "Load Sample Portfolio" to start.</p>';
                    return;
                }
                
                let html = '<h2>Holdings</h2><table>';
                html += '<tr><th>Symbol</th><th>Quantity</th><th>Avg Cost</th><th>Current Price</th><th>Market Value</th><th>P&L</th><th>Gain %</th></tr>';
                
                data.positions.forEach(pos => {
                    const plClass = pos.unrealizedPL >= 0 ? 'positive' : 'negative';
                    html += '<tr>';
                    html += '<td><strong>' + pos.symbol + '</strong></td>';
                    html += '<td>' + pos.quantity + '</td>';
                    html += '<td>$' + pos.avgCost.toFixed(2) + '</td>';
                    html += '<td>$' + pos.currentPrice.toFixed(2) + '</td>';
                    html += '<td>$' + pos.marketValue.toFixed(2) + '</td>';
                    html += '<td class="' + plClass + '">$' + pos.unrealizedPL.toFixed(2) + '</td>';
                    html += '<td class="' + plClass + '">' + pos.gainPercent.toFixed(2) + '%</td>';
                    html += '</tr>';
                });
                
                html += '</table>';
                
                const summary = data.summary;
                const totalPlClass = summary.totalUnrealizedPL >= 0 ? 'positive' : 'negative';
                
                html += '<div class="summary">';
                html += '<h2>Portfolio Summary</h2>';
                html += '<p><strong>Total Cost Basis:</strong> $' + summary.totalCostBasis.toFixed(2) + '</p>';
                html += '<p><strong>Total Market Value:</strong> $' + summary.totalMarketValue.toFixed(2) + '</p>';
                html += '<p class="' + totalPlClass + '"><strong>Total Unrealized P&L:</strong> $' + summary.totalUnrealizedPL.toFixed(2) + '</p>';
                html += '<p class="' + totalPlClass + '"><strong>Total Gain:</strong> ' + summary.totalGainPercent.toFixed(2) + '%</p>';
                html += '<p><small>Last Updated: ' + new Date(data.lastUpdated).toLocaleString() + '</small></p>';
                html += '</div>';
                
                document.getElementById('portfolio').innerHTML = html;
            }
            
            // Load on startup
            refreshData();
        </script>
    </body>
    </html>
    """

@app.get("/portfolio")
async def get_portfolio():
    """Get current portfolio as JSON"""
    try:
        return json.loads(tracker.get_json_summary())
    except:
        return {"error": "No portfolio loaded"}

@app.get("/load-sample")
async def load_sample():
    """Load the sample holdings CSV"""
    tracker.load_holdings('docs/holdings_sample.csv')
    tracker.update_prices()
    return {"message": "Sample portfolio loaded successfully!"}

@app.post("/update-prices")
async def update_prices():
    """Update prices from market"""
    if tracker.holdings is None:
        raise HTTPException(status_code=400, detail="No portfolio loaded")
    
    tracker.update_prices()
    tracker.calculate_portfolio()
    return {"message": "Prices updated from market!"}

if __name__ == "__main__":
    import uvicorn
    print("\nStarting Simple Portfolio Tracker...")
    print("Visit http://localhost:8001 to see your portfolio\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)