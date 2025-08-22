# AI Financial Planning Demo - Deployment Guide

A fully functional demonstration of the AI Financial Planning System with advanced Monte Carlo simulations, portfolio optimization, real-time WebSocket updates, and comprehensive financial analytics.

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)

```bash
./start_demo.sh
```

This script will:
- Check system requirements
- Install missing dependencies automatically
- Choose the appropriate demo version based on available libraries
- Start the server with optimal configuration

### Option 2: Manual Startup

#### Basic Demo (Minimal Dependencies)
```bash
# Install basic requirements
pip3 install fastapi uvicorn numpy pydantic "python-jose[cryptography]" "passlib[bcrypt]"

# Run minimal demo
python3 minimal_working_demo.py
```

#### Full-Featured Demo (All Features)
```bash
# Install all dependencies
pip3 install -r requirements_demo.txt

# Run full demo
python3 working_demo.py
```

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Disk**: 500MB available space
- **Network**: Internet connection for package installation

### Core Dependencies (Always Required)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `numpy` - Numerical computing
- `pydantic` - Data validation
- `python-jose[cryptography]` - JWT tokens
- `passlib[bcrypt]` - Password hashing

### Advanced Dependencies (Optional, Enable Extra Features)
- `scipy` - Advanced portfolio optimization
- `matplotlib` + `seaborn` - Chart generation
- `numba` - JIT compilation for faster simulations
- `reportlab` - PDF report generation
- `pandas` - Data manipulation

## 🌟 Features

### Core Features (Available in Both Versions)
✅ **FastAPI Backend** - Production-ready REST API with auto-generated documentation  
✅ **SQLite Database** - Zero-configuration database with full ACID compliance  
✅ **JWT Authentication** - Secure user authentication and authorization  
✅ **Monte Carlo Simulations** - High-performance portfolio growth projections  
✅ **Risk Assessment** - Comprehensive financial risk analysis  
✅ **Real-time WebSocket** - Live updates and real-time data streaming  
✅ **Financial Goal Tracking** - Personal financial goal management  
✅ **AI Recommendations** - Intelligent financial advice generation  
✅ **Analytics Dashboard** - Comprehensive performance metrics  

### Advanced Features (Full Version Only)
🔬 **Advanced Portfolio Optimization** - Modern Portfolio Theory with Scipy  
📊 **Interactive Charts** - Matplotlib/Seaborn visualizations  
⚡ **Numba Acceleration** - JIT-compiled simulations (10x speed improvement)  
📄 **PDF Report Generation** - Professional financial planning reports  
🎨 **Enhanced Visualizations** - Publication-quality charts and graphs  

## 🔧 API Endpoints

### Public Endpoints
- `GET /` - API information and quick start guide
- `GET /health` - System health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation
- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /sample-data` - Create demo data

### Authenticated Endpoints
- `GET/POST /profile` - Financial profile management
- `GET/POST /goals` - Financial goals management
- `POST /simulate` - Monte Carlo portfolio simulations
- `POST /optimize-portfolio` - Portfolio optimization
- `GET /recommendations` - Personalized financial advice
- `GET /analytics` - Performance analytics dashboard
- `GET /visualize/{chart_type}` - Chart generation (full version)
- `POST /generate-report` - PDF report creation (full version)
- `WebSocket /ws` - Real-time updates

## 👤 Demo User Accounts

### Pre-created Demo Users
| Email | Password | Profile | Description |
|-------|----------|---------|-------------|
| `demo@example.com` | `demo123` | Moderate Risk | Primary demo user with sample data |
| `young.professional@example.com` | `demo123` | Aggressive | Young investor, high growth focus |
| `experienced.investor@example.com` | `demo123` | Conservative | Experienced investor, capital preservation |

### Creating Your Own Account
You can register new users through:
- API endpoint: `POST /register`
- Interactive docs: Visit `/docs` and use the register endpoint

## 🎯 Demo Workflow

### 1. Initial Setup
```bash
# Start the demo
./start_demo.sh

# Create sample data (if not already created)
curl http://localhost:8000/sample-data
```

### 2. Authentication
```bash
# Login to get access token
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@example.com&password=demo123"
```

### 3. Run a Simulation
```bash
# Run Monte Carlo simulation
curl -X POST "http://localhost:8000/simulate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "years_to_retirement": 20,
    "monthly_contribution": 1000,
    "initial_amount": 50000,
    "risk_level": "moderate",
    "num_simulations": 10000
  }'
```

### 4. Optimize Portfolio
```bash
# Get optimal portfolio allocation
curl -X POST "http://localhost:8000/optimize-portfolio" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "risk_tolerance": "moderate",
    "investment_amount": 100000
  }'
```

## 📊 Performance Benchmarks

### Monte Carlo Simulation Performance
| Configuration | Simulations | Time (seconds) | Memory Usage |
|---------------|-------------|----------------|--------------|
| Minimal (NumPy) | 10,000 | ~2-3 seconds | ~100MB |
| Full (Numba JIT) | 10,000 | ~0.5-1 seconds | ~150MB |
| Full (Numba JIT) | 50,000 | ~2-3 seconds | ~300MB |

### System Resource Usage
- **Idle**: ~50MB RAM, 0% CPU
- **Under Load**: ~200MB RAM, 5-15% CPU (single simulation)
- **Database**: ~10MB SQLite file for demo data

## 🔍 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: No module named 'fastapi'
pip3 install fastapi uvicorn

# Error: No module named 'numpy'
pip3 install numpy

# Error: No module named 'jose'
pip3 install python-jose[cryptography]
```

#### 2. Port Already in Use
```bash
# Error: [Errno 48] Address already in use
# Solution: Kill existing process or use different port
lsof -ti:8000 | xargs kill -9

# Or run on different port
uvicorn minimal_working_demo:app --port 8001
```

#### 3. Permission Errors
```bash
# Error: Permission denied
# Solution: Make script executable
chmod +x start_demo.sh

# Or run with bash
bash start_demo.sh
```

#### 4. Database Issues
```bash
# Error: Database locked
# Solution: Remove database file and restart
rm -f minimal_demo_financial_planning.db
python3 minimal_working_demo.py
```

### Performance Issues

#### Slow Simulations
- Reduce `num_simulations` parameter (default: 10,000)
- Install Numba for JIT acceleration: `pip3 install numba`
- Use minimal demo for faster startup

#### Memory Issues
- Reduce simulation count
- Close other applications
- Use minimal demo version

## 🧪 Testing the Demo

### Automated Testing
```bash
# Run simple functionality test
python3 simple_ml_test.py

# Run comprehensive test suite (if available)
python3 test_demo.py
```

### Manual Testing Checklist
- [ ] Server starts without errors
- [ ] Health check returns "healthy" status
- [ ] Interactive docs accessible at `/docs`
- [ ] User registration works
- [ ] User login returns JWT token
- [ ] Sample data creation succeeds
- [ ] Monte Carlo simulation completes
- [ ] Portfolio optimization returns allocation
- [ ] WebSocket connection established
- [ ] All endpoints return expected responses

## 📈 Advanced Configuration

### Environment Variables
```bash
# Database configuration
export DATABASE_FILE="custom_demo.db"

# Security configuration
export SECRET_KEY="your-custom-secret-key"
export ACCESS_TOKEN_EXPIRE_MINUTES=60

# Performance tuning
export DEFAULT_SIMULATIONS=5000
export MAX_SIMULATIONS=25000
```

### Custom Settings
```python
# Modify simulation parameters
SIMULATION_DEFAULTS = {
    "num_simulations": 10000,
    "years_range": (1, 50),
    "contribution_range": (100, 10000)
}

# Adjust risk profiles
RISK_PROFILES = {
    "conservative": {"return": 0.06, "volatility": 0.08},
    "moderate": {"return": 0.08, "volatility": 0.12},
    "aggressive": {"return": 0.10, "volatility": 0.18}
}
```

## 🔒 Security Notes

### Demo Security Features
- JWT token authentication
- Password hashing with bcrypt
- SQL injection protection via parameterized queries
- CORS configuration for frontend integration
- Input validation with Pydantic

### Production Considerations
- Change default secret key
- Use environment variables for sensitive data
- Enable HTTPS in production
- Implement rate limiting
- Add comprehensive logging
- Use production database (PostgreSQL)

## 📚 Additional Resources

### Documentation
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`
- OpenAPI specification: Available through `/docs`

### Code Structure
- `minimal_working_demo.py` - Minimal dependencies version
- `working_demo.py` - Full-featured version
- `simple_ml_test.py` - Basic functionality tests
- `requirements_demo.txt` - All dependencies
- `start_demo.sh` - Automated startup script

### Support
- Check logs for error messages
- Review API documentation at `/docs`
- Verify system requirements are met
- Test with minimal demo first if issues occur

## 🎉 Success Indicators

Your demo is working correctly when:
1. ✅ Server starts and shows impressive startup banner
2. ✅ Health check returns `{"status": "healthy"}`
3. ✅ Interactive docs load at `/docs`
4. ✅ Sample data creation succeeds
5. ✅ Monte Carlo simulation completes in <5 seconds
6. ✅ Portfolio optimization returns valid allocation
7. ✅ WebSocket connection shows real-time updates
8. ✅ All demo user accounts work for authentication

**Demo is ready when you see: "🎉 All tests passed! The demo should work correctly."**

---

**Enjoy exploring the AI Financial Planning System! 🚀**