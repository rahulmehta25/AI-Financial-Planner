# AI Financial Planning System

A comprehensive, AI-driven financial planning platform that provides Monte Carlo simulations, trade-off analysis, and personalized retirement planning recommendations.

## 🚀 Features

### Core Financial Planning
- **Monte Carlo Simulations**: 50,000 path simulations for retirement planning
- **Trade-off Analysis**: Three key scenarios (save more, retire later, spend less)
- **Portfolio Recommendations**: Risk-based asset allocation with ETF suggestions
- **Compliance Features**: Built-in disclaimers and audit logging

### AI Integration
- **Generative AI Narratives**: Client-friendly explanations of complex financial data
- **OpenAI/Anthropic Support**: Configurable LLM providers for narrative generation
- **Template-based Prompts**: Controlled content generation for compliance

### Technical Features
- **High Performance**: Numba-optimized simulations targeting <30 second completion
- **Audit Trail**: 100% reproducible results with comprehensive logging
- **Security**: JWT authentication, rate limiting, and input validation
- **Scalability**: Microservices-oriented architecture for independent deployment

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI**: High-performance web framework with automatic API documentation
- **SQLAlchemy**: Async ORM with PostgreSQL support
- **Monte Carlo Engine**: Numba-optimized simulation engine
- **Audit System**: Comprehensive logging for compliance and reproducibility

### Frontend (React/Next.js)
- **Form Wizard**: Multi-step financial data collection
- **Results Dashboard**: Interactive visualization of simulation results
- **Responsive Design**: Modern UI with Tailwind CSS
- **State Management**: Zustand for efficient state handling

### Database (PostgreSQL)
- **Financial Models**: User profiles, plans, simulations, and audit logs
- **JSONB Support**: Flexible storage for complex financial data
- **Indexing**: Optimized queries for performance
- **Migrations**: Alembic for schema management

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (optional, for caching)
- Node.js 18+ (for frontend)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Financial-Planning
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.template .env
# Edit .env with your configuration

# Run development server
python start_dev.py
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Database Setup
```bash
# Start PostgreSQL
# Create database: financial_planning

# Run migrations
cd backend
alembic upgrade head
```

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/financial_planning

# Security
SECRET_KEY=your-secret-key-here

# AI/LLM
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Simulation
DEFAULT_MONTE_CARLO_ITERATIONS=50000
SIMULATION_TIMEOUT_SECONDS=300
```

### API Configuration
- **Base URL**: `http://localhost:8000`
- **API Version**: `/api/v1`
- **Documentation**: `http://localhost:8000/docs`

## 📊 API Endpoints

### Financial Planning
- `POST /api/v1/plans/create` - Create new financial plan
- `GET /api/v1/plans/{plan_id}/status` - Check plan status
- `GET /api/v1/plans/{plan_id}/results` - Get plan results
- `GET /api/v1/plans/{plan_id}/export/pdf` - Export PDF report

### Simulations
- `POST /api/v1/simulations/monte-carlo` - Run Monte Carlo simulation
- `POST /api/v1/simulations/scenario-analysis` - Run scenario analysis
- `GET /api/v1/simulations/{simulation_id}/status` - Check simulation status

### User Management
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/users/profile` - Get user profile

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Run full test suite
pytest tests/ --cov=app --cov-report=html
```

## 📈 Performance

### Simulation Engine
- **Target**: 50,000 simulations in <30 seconds
- **Optimization**: Numba JIT compilation
- **Parallelization**: Multi-core processing support
- **Memory**: Efficient numpy arrays and memory management

### Database Performance
- **Connection Pooling**: Configurable pool sizes
- **Indexing**: Optimized for common queries
- **Async Operations**: Non-blocking database access

## 🔒 Security & Compliance

### Authentication
- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting protection
- Session management

### Compliance
- **Audit Logging**: Complete audit trail for all operations
- **Data Retention**: Configurable retention policies
- **Disclaimers**: Built-in compliance disclaimers
- **Reproducibility**: 100% reproducible results with logging

### Data Protection
- Input validation with Pydantic
- SQL injection protection
- XSS protection
- CORS configuration

## 🚀 Deployment

### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Production
```bash
# Set production environment
export ENVIRONMENT=production

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running
- **Implementation Guide**: `AI Financial Planner Implementation Guide.md`
- **Activity Log**: `docs/activity.md`
- **Database Schema**: `docs/database_documentation.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation
- Review the activity log
- Open an issue on GitHub

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Core Monte Carlo simulation engine
- ✅ Basic API endpoints
- ✅ Frontend form wizard
- ✅ Database models and audit logging

### Phase 2 (Next)
- 🔄 AI narrative generation integration
- 🔄 PDF export functionality
- 🔄 Advanced portfolio optimization
- 🔄 Real-time market data integration

### Phase 3 (Future)
- 📋 Mobile application
- 📋 Advanced analytics dashboard
- 📋 Multi-currency support
- 📋 Integration with financial institutions

---

**Note**: This system is designed for educational and planning purposes. All simulations are estimates, not guarantees. Please consult with qualified financial professionals for actual financial advice.