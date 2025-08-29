"""
Real, working portfolio API - not boilerplate!
This actually manages portfolios and fetches real market data
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.real_models import User, Portfolio, Holding, Transaction, init_database, get_session
from core.market_data import MarketDataService

app = FastAPI(title="Portfolio Tracker API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
engine = init_database()

# Pydantic models for API
class HoldingCreate(BaseModel):
    symbol: str
    quantity: float
    cost_basis: float

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TransactionCreate(BaseModel):
    symbol: str
    transaction_type: str  # 'buy' or 'sell'
    quantity: float
    price: float
    fees: Optional[float] = 0
    transaction_date: datetime

class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    total_value: float
    total_cost: float
    total_gain_loss: float
    total_gain_loss_percent: float
    holdings: List[Dict[str, Any]]
    last_updated: datetime

# Dependency to get DB session
def get_db():
    session = get_session(engine)
    try:
        yield session
    finally:
        session.close()

# For demo purposes, we'll use a hardcoded user ID
DEMO_USER_ID = "demo-user-123"

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "alive", "message": "Portfolio Tracker API is running!"}

@app.get("/api/portfolios", response_model=List[Dict[str, Any]])
def get_portfolios(db = Depends(get_db)):
    """Get all portfolios for the user"""
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == DEMO_USER_ID).all()
    result = []
    for p in portfolios:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "total_value": float(p.total_value) if p.total_value else 0,
            "total_gain_loss": float(p.total_gain_loss) if p.total_gain_loss else 0,
            "holdings_count": len(p.holdings),
            "last_updated": p.last_calculated.isoformat() if p.last_calculated else None
        })
    return result

@app.post("/api/portfolios", response_model=Dict[str, Any])
def create_portfolio(portfolio: PortfolioCreate, db = Depends(get_db)):
    """Create a new portfolio"""
    # Check if user exists, if not create demo user
    user = db.query(User).filter(User.id == DEMO_USER_ID).first()
    if not user:
        user = User(
            id=DEMO_USER_ID,
            email="demo@example.com",
            password_hash="demo",
            first_name="Demo",
            last_name="User"
        )
        db.add(user)
        db.commit()
    
    # Create portfolio
    new_portfolio = Portfolio(
        user_id=DEMO_USER_ID,
        name=portfolio.name,
        description=portfolio.description
    )
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    
    return {
        "id": new_portfolio.id,
        "name": new_portfolio.name,
        "description": new_portfolio.description,
        "created": True
    }

@app.get("/api/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio_details(portfolio_id: str, db = Depends(get_db)):
    """Get detailed portfolio information with real market data"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get holdings
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
    
    # Prepare holdings data for market data service
    holdings_data = []
    for h in holdings:
        holdings_data.append({
            'symbol': h.symbol,
            'quantity': float(h.quantity),
            'cost_basis': float(h.cost_basis) if h.cost_basis else 0
        })
    
    # Get real market data and calculate metrics
    if holdings_data:
        metrics = MarketDataService.calculate_portfolio_metrics(holdings_data)
        
        # Update portfolio totals in database
        portfolio.total_value = Decimal(str(metrics['total_value']))
        portfolio.total_cost = Decimal(str(metrics['total_cost']))
        portfolio.total_gain_loss = Decimal(str(metrics['total_gain_loss']))
        portfolio.last_calculated = datetime.now()
        
        # Update individual holdings with current prices
        for h_data in metrics['holdings']:
            holding = next((h for h in holdings if h.symbol == h_data['symbol']), None)
            if holding:
                holding.current_price = Decimal(str(h_data['current_price']))
                holding.market_value = Decimal(str(h_data['market_value']))
                holding.gain_loss = Decimal(str(h_data['gain_loss']))
                holding.gain_loss_percent = Decimal(str(h_data['gain_loss_percent']))
                holding.last_updated = datetime.now()
        
        db.commit()
    else:
        metrics = {
            'total_value': 0,
            'total_cost': 0,
            'total_gain_loss': 0,
            'total_gain_loss_percent': 0,
            'holdings': [],
            'last_updated': datetime.now().isoformat()
        }
    
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        total_value=metrics['total_value'],
        total_cost=metrics['total_cost'],
        total_gain_loss=metrics['total_gain_loss'],
        total_gain_loss_percent=metrics['total_gain_loss_percent'],
        holdings=metrics['holdings'],
        last_updated=datetime.now()
    )

@app.post("/api/portfolios/{portfolio_id}/holdings")
def add_holding(portfolio_id: str, holding: HoldingCreate, db = Depends(get_db)):
    """Add a holding to a portfolio"""
    # Check if portfolio exists
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if holding already exists
    existing = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.symbol == holding.symbol
    ).first()
    
    if existing:
        # Update existing holding (average the cost basis)
        total_shares = float(existing.quantity) + holding.quantity
        total_cost = (float(existing.quantity) * float(existing.cost_basis)) + (holding.quantity * holding.cost_basis)
        existing.quantity = Decimal(str(total_shares))
        existing.cost_basis = Decimal(str(total_cost / total_shares))
        db.commit()
        message = f"Updated {holding.symbol} holding"
    else:
        # Create new holding
        new_holding = Holding(
            portfolio_id=portfolio_id,
            symbol=holding.symbol.upper(),
            quantity=Decimal(str(holding.quantity)),
            cost_basis=Decimal(str(holding.cost_basis))
        )
        db.add(new_holding)
        db.commit()
        message = f"Added {holding.symbol} to portfolio"
    
    # Also record as a transaction
    transaction = Transaction(
        portfolio_id=portfolio_id,
        symbol=holding.symbol.upper(),
        transaction_type='buy',
        quantity=Decimal(str(holding.quantity)),
        price=Decimal(str(holding.cost_basis)),
        transaction_date=datetime.now()
    )
    db.add(transaction)
    db.commit()
    
    return {"success": True, "message": message}

@app.delete("/api/portfolios/{portfolio_id}/holdings/{symbol}")
def remove_holding(portfolio_id: str, symbol: str, db = Depends(get_db)):
    """Remove a holding from a portfolio"""
    holding = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.symbol == symbol.upper()
    ).first()
    
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    db.delete(holding)
    db.commit()
    
    return {"success": True, "message": f"Removed {symbol} from portfolio"}

@app.get("/api/market/quote/{symbol}")
def get_market_quote(symbol: str):
    """Get real-time market quote for a symbol"""
    info = MarketDataService.get_stock_info(symbol.upper())
    if 'error' in info:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return info

@app.get("/api/market/search")
def search_symbols(q: str):
    """Search for stock symbols (simplified for now)"""
    # Common symbols for demo
    common_symbols = {
        "AAPL": "Apple Inc.",
        "GOOGL": "Alphabet Inc.",
        "MSFT": "Microsoft Corporation",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "META": "Meta Platforms Inc.",
        "NVDA": "NVIDIA Corporation",
        "SPY": "SPDR S&P 500 ETF",
        "QQQ": "Invesco QQQ Trust",
        "VOO": "Vanguard S&P 500 ETF"
    }
    
    results = []
    query = q.upper()
    for symbol, name in common_symbols.items():
        if query in symbol or query in name.upper():
            results.append({"symbol": symbol, "name": name})
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)