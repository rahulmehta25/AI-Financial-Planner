#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLE API for Portfolio Tracker
Just the endpoints you actually need.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import pandas as pd
import yfinance as yf
from datetime import datetime
import json
from portfolio_tracker import PortfolioTracker

app = FastAPI(title="Simple Portfolio Tracker", version="1.0.0")

# Enable CORS for frontend
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
            button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>=� Simple Portfolio Tracker</h1>
            
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
                refreshData();
            }
            
            async function updatePrices() {
                const response = await fetch('/update-prices', {method: 'POST'});
                const data = await response.json();
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
                    html += `<tr>
                        <td><strong>${pos.symbol}</strong></td>
                        <td>${pos.quantity}</td>
                        <td>$${pos.avgCost.toFixed(2)}</td>
                        <td>$${pos.currentPrice.toFixed(2)}</td>
                        <td>$${pos.marketValue.toFixed(2)}</td>
                        <td class="${plClass}">$${pos.unrealizedPL.toFixed(2)}</td>
                        <td class="${plClass}">${pos.gainPercent.toFixed(2)}%</td>
                    </tr>`;
                });
                
                html += '</table>';
                
                const summary = data.summary;
                const totalPlClass = summary.totalUnrealizedPL >= 0 ? 'positive' : 'negative';
                
                html += `<div class="summary">
                    <h2>Portfolio Summary</h2>
                    <p><strong>Total Cost Basis:</strong> $${summary.totalCostBasis.toFixed(2)}</p>
                    <p><strong>Total Market Value:</strong> $${summary.totalMarketValue.toFixed(2)}</p>
                    <p class="${totalPlClass}"><strong>Total Unrealized P&L:</strong> $${summary.totalUnrealizedPL.toFixed(2)}</p>
                    <p class="${totalPlClass}"><strong>Total Gain:</strong> ${summary.totalGainPercent.toFixed(2)}%</p>
                    <p><small>Last Updated: ${new Date(data.lastUpdated).toLocaleString()}</small></p>
                </div>`;
                
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
    return {"message": "Sample portfolio loaded"}

@app.post("/update-prices")
async def update_prices():
    """Update prices from market"""
    if tracker.holdings is None:
        raise HTTPException(status_code=400, detail="No portfolio loaded")
    
    tracker.update_prices()
    tracker.calculate_portfolio()
    return {"message": "Prices updated"}

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file with holdings"""
    content = await file.read()
    
    # Save temporarily and load
    temp_path = f"temp_{file.filename}"
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        tracker.load_holdings(temp_path)
        tracker.update_prices()
        return {"message": f"Loaded {len(tracker.holdings)} positions"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n=� Starting Simple Portfolio Tracker API...")
    print("=� Visit http://localhost:8000 to see your portfolio\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)