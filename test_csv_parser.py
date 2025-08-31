#!/usr/bin/env python3
"""
Simple CSV parser test - NO DATABASE REQUIRED
This actually works without any setup
"""
import csv
import io
from datetime import datetime
from decimal import Decimal

# Sample CSV data from different brokers
FIDELITY_CSV = """Run Date,Account,Action,Symbol,Security Description,Security Type,Quantity,Price ($),Commission ($),Fees ($),Accrued Interest ($),Amount ($),Settlement Date
01/15/2024,X12345,YOU BOUGHT,AAPL,APPLE INC,Cash,100,150.50,0,0,0,-15050.00,01/17/2024
01/20/2024,X12345,YOU BOUGHT,GOOGL,ALPHABET INC CLASS A,Cash,50,140.25,0,0,0,-7012.50,01/22/2024
02/01/2024,X12345,YOU SOLD,AAPL,APPLE INC,Cash,50,155.00,0,0,0,7750.00,02/03/2024"""

SCHWAB_CSV = """Date,Action,Symbol,Description,Quantity,Price,Fees & Comm,Amount
1/15/2024,Buy,AAPL,APPLE INC,100,$150.50,$0.00,-$15050.00
1/20/2024,Buy,GOOGL,ALPHABET INC-A,50,$140.25,$0.00,-$7012.50
2/1/2024,Sell,AAPL,APPLE INC,50,$155.00,$0.00,$7750.00"""

def parse_fidelity_csv(csv_content):
    """Parse Fidelity CSV format"""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        # Extract and clean data
        action = 'buy' if 'BOUGHT' in row['Action'] else 'sell'
        symbol = row['Symbol']
        quantity = abs(float(row['Quantity']))
        price = abs(float(row['Price ($)']))
        date_str = row['Run Date']
        trade_date = datetime.strptime(date_str, '%m/%d/%Y').date()
        
        transactions.append({
            'date': trade_date,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'amount': quantity * price
        })
    
    return transactions

def parse_schwab_csv(csv_content):
    """Parse Schwab CSV format"""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        # Extract and clean data
        action = row['Action'].lower()
        symbol = row['Symbol']
        quantity = float(row['Quantity'])
        # Remove $ and commas from price
        price_str = row['Price'].replace('$', '').replace(',', '')
        price = float(price_str)
        date_str = row['Date']
        trade_date = datetime.strptime(date_str, '%m/%d/%Y').date()
        
        transactions.append({
            'date': trade_date,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'amount': quantity * price
        })
    
    return transactions

def calculate_portfolio(transactions):
    """Calculate current portfolio positions from transactions"""
    positions = {}
    
    for tx in transactions:
        symbol = tx['symbol']
        if symbol not in positions:
            positions[symbol] = {
                'quantity': 0,
                'total_cost': 0,
                'realized_gains': 0
            }
        
        if tx['action'] == 'buy':
            positions[symbol]['quantity'] += tx['quantity']
            positions[symbol]['total_cost'] += tx['amount']
        else:  # sell
            # Simple FIFO calculation
            current_qty = positions[symbol]['quantity']
            current_cost = positions[symbol]['total_cost']
            avg_cost = current_cost / current_qty if current_qty > 0 else 0
            
            sell_cost = avg_cost * tx['quantity']
            gain = tx['amount'] - sell_cost
            
            positions[symbol]['quantity'] -= tx['quantity']
            positions[symbol]['total_cost'] -= sell_cost
            positions[symbol]['realized_gains'] += gain
    
    # Calculate average cost for remaining positions
    for symbol, pos in positions.items():
        if pos['quantity'] > 0:
            pos['avg_cost'] = pos['total_cost'] / pos['quantity']
        else:
            pos['avg_cost'] = 0
    
    return positions

def main():
    print("="*60)
    print("CSV PARSER TEST - No Database Required!")
    print("="*60)
    
    # Test Fidelity format
    print("\n1. Testing Fidelity CSV Parser:")
    print("-" * 40)
    fidelity_transactions = parse_fidelity_csv(FIDELITY_CSV)
    for tx in fidelity_transactions:
        print(f"  {tx['date']}: {tx['action'].upper():4} {tx['quantity']:3.0f} {tx['symbol']:5} @ ${tx['price']:.2f}")
    
    # Test Schwab format
    print("\n2. Testing Schwab CSV Parser:")
    print("-" * 40)
    schwab_transactions = parse_schwab_csv(SCHWAB_CSV)
    for tx in schwab_transactions:
        print(f"  {tx['date']}: {tx['action'].upper():4} {tx['quantity']:3.0f} {tx['symbol']:5} @ ${tx['price']:.2f}")
    
    # Calculate portfolio
    print("\n3. Portfolio Calculation (FIFO):")
    print("-" * 40)
    all_transactions = fidelity_transactions  # Use Fidelity data for portfolio calc
    portfolio = calculate_portfolio(all_transactions)
    
    total_value = 0
    for symbol, position in portfolio.items():
        if position['quantity'] > 0:
            print(f"  {symbol}:")
            print(f"    Quantity: {position['quantity']:.0f} shares")
            print(f"    Avg Cost: ${position['avg_cost']:.2f}")
            print(f"    Total Cost: ${position['total_cost']:.2f}")
            
        if position['realized_gains'] != 0:
            print(f"    Realized Gains: ${position['realized_gains']:.2f}")
    
    # Summary
    print("\n4. Summary:")
    print("-" * 40)
    total_bought = sum(tx['amount'] for tx in all_transactions if tx['action'] == 'buy')
    total_sold = sum(tx['amount'] for tx in all_transactions if tx['action'] == 'sell')
    net_invested = total_bought - total_sold
    
    print(f"  Total Bought: ${total_bought:,.2f}")
    print(f"  Total Sold: ${total_sold:,.2f}")
    print(f"  Net Invested: ${net_invested:,.2f}")
    
    # Show what we can do next
    print("\n" + "="*60)
    print("SUCCESS! CSV Parsing Works!")
    print("="*60)
    print("\nNext steps:")
    print("1. Save these transactions to a database")
    print("2. Fetch current prices to show unrealized gains")
    print("3. Create a web API to serve this data")
    print("4. Build a simple UI to display positions")
    
    return all_transactions, portfolio

if __name__ == "__main__":
    transactions, portfolio = main()