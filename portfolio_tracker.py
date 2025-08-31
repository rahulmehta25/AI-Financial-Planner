#!/usr/bin/env python3
"""
SIMPLE WORKING PORTFOLIO TRACKER
No boilerplate. Just functionality that works.
"""
import pandas as pd
import yfinance as yf
from datetime import datetime
from decimal import Decimal
import json

class PortfolioTracker:
    def __init__(self, holdings_csv=None):
        """Initialize with optional CSV file path"""
        self.holdings = None
        if holdings_csv:
            self.load_holdings(holdings_csv)
    
    def load_holdings(self, csv_path):
        """Load holdings from CSV file"""
        # Read CSV, handling potential formatting issues
        df = pd.read_csv(csv_path, on_bad_lines='skip')
        # Remove TOTAL row and any empty rows
        self.holdings = df[(df['Symbol'] != 'TOTAL') & (df['Symbol'].notna())].copy()
        print(f"Loaded {len(self.holdings)} positions from {csv_path}")
        return self.holdings
    
    def update_prices(self):
        """Fetch current prices from yfinance"""
        if self.holdings is None:
            raise ValueError("No holdings loaded. Call load_holdings() first.")
        
        symbols = self.holdings['Symbol'].tolist()
        print(f"Fetching prices for: {symbols}")
        
        current_prices = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    current_prices[symbol] = round(price, 2)
                    print(f"  {symbol}: ${price:.2f}")
            except Exception as e:
                print(f"  {symbol}: Error - {e}")
                current_prices[symbol] = 0
        
        # Update the dataframe
        self.holdings['Current Price'] = self.holdings['Symbol'].map(current_prices)
        self.holdings['Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return current_prices
    
    def calculate_portfolio(self):
        """Calculate portfolio metrics"""
        if self.holdings is None:
            raise ValueError("No holdings loaded.")
        
        # Calculate for each position
        self.holdings['Market Value'] = self.holdings['Quantity'] * self.holdings['Current Price']
        self.holdings['Cost Basis'] = self.holdings['Quantity'] * self.holdings['Avg Cost (open)']
        self.holdings['Unrealized P&L'] = self.holdings['Market Value'] - self.holdings['Cost Basis']
        self.holdings['Gain %'] = (self.holdings['Unrealized P&L'] / self.holdings['Cost Basis'] * 100).round(2)
        
        # Calculate totals
        totals = {
            'Total Cost Basis': self.holdings['Cost Basis'].sum(),
            'Total Market Value': self.holdings['Market Value'].sum(),
            'Total Unrealized P&L': self.holdings['Unrealized P&L'].sum(),
            'Total Gain %': 0
        }
        
        if totals['Total Cost Basis'] > 0:
            totals['Total Gain %'] = round(
                (totals['Total Unrealized P&L'] / totals['Total Cost Basis'] * 100), 2
            )
        
        return totals
    
    def display_portfolio(self):
        """Display portfolio in a nice format"""
        if self.holdings is None:
            print("No holdings to display")
            return
        
        print("\n" + "="*80)
        print("PORTFOLIO HOLDINGS")
        print("="*80)
        
        # Display each position
        for _, row in self.holdings.iterrows():
            print(f"\n{row['Symbol']}:")
            print(f"  Quantity: {row['Quantity']} shares")
            print(f"  Avg Cost: ${row['Avg Cost (open)']:.2f}")
            print(f"  Current: ${row['Current Price']:.2f}")
            print(f"  Value: ${row['Market Value']:.2f}")
            print(f"  P&L: ${row['Unrealized P&L']:.2f} ({row['Gain %']:.1f}%)")
        
        # Display totals
        totals = self.calculate_portfolio()
        print("\n" + "-"*80)
        print("PORTFOLIO SUMMARY")
        print("-"*80)
        print(f"Total Cost Basis:    ${totals['Total Cost Basis']:,.2f}")
        print(f"Total Market Value:  ${totals['Total Market Value']:,.2f}")
        print(f"Total Unrealized P&L: ${totals['Total Unrealized P&L']:,.2f}")
        print(f"Total Gain:          {totals['Total Gain %']:.2f}%")
        print("="*80)
    
    def save_to_csv(self, output_path='portfolio_updated.csv'):
        """Save updated portfolio to CSV"""
        if self.holdings is not None:
            # Add totals row
            totals = self.calculate_portfolio()
            totals_row = pd.DataFrame([{
                'Symbol': 'TOTAL',
                'Quantity': self.holdings['Quantity'].sum(),
                'Avg Cost (open)': '',
                'Current Price': '',
                'Cost Basis': totals['Total Cost Basis'],
                'Market Value': totals['Total Market Value'],
                'Unrealized P&L': totals['Total Unrealized P&L'],
                'Gain %': totals['Total Gain %'],
                'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            
            output_df = pd.concat([self.holdings, totals_row], ignore_index=True)
            output_df.to_csv(output_path, index=False)
            print(f"\nPortfolio saved to {output_path}")
    
    def get_json_summary(self):
        """Get portfolio summary as JSON"""
        if self.holdings is None:
            return json.dumps({"error": "No holdings loaded"})
        
        totals = self.calculate_portfolio()
        positions = []
        
        for _, row in self.holdings.iterrows():
            positions.append({
                'symbol': row['Symbol'],
                'quantity': float(row['Quantity']),
                'avgCost': float(row['Avg Cost (open)']),
                'currentPrice': float(row['Current Price']),
                'marketValue': float(row['Market Value']),
                'unrealizedPL': float(row['Unrealized P&L']),
                'gainPercent': float(row['Gain %'])
            })
        
        return json.dumps({
            'positions': positions,
            'summary': {
                'totalCostBasis': float(totals['Total Cost Basis']),
                'totalMarketValue': float(totals['Total Market Value']),
                'totalUnrealizedPL': float(totals['Total Unrealized P&L']),
                'totalGainPercent': float(totals['Total Gain %'])
            },
            'lastUpdated': datetime.now().isoformat()
        }, indent=2)


def main():
    """Run the portfolio tracker"""
    print("SIMPLE PORTFOLIO TRACKER")
    print("========================\n")
    
    # Create tracker and load sample data
    tracker = PortfolioTracker()
    
    # Load the sample holdings
    tracker.load_holdings('docs/holdings_sample.csv')
    
    # Update prices from market
    print("\nFetching current market prices...")
    tracker.update_prices()
    
    # Calculate and display
    tracker.display_portfolio()
    
    # Save updated portfolio
    tracker.save_to_csv('portfolio_current.csv')
    
    # Also save as JSON for potential API use
    with open('portfolio_current.json', 'w') as f:
        f.write(tracker.get_json_summary())
    print("Portfolio saved to portfolio_current.json")


if __name__ == "__main__":
    main()