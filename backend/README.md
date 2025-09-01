# AI Financial Planner Backend

## Deployment on Railway

This backend is configured for deployment on Railway with PostgreSQL.

### Environment Variables Required

```env
DATABASE_URL=(automatically provided by Railway)
JWT_SECRET_KEY=your-secure-jwt-secret
SECRET_KEY=your-secure-secret-key
ENV=production
```

### Endpoints

- `/` - Health check
- `/health` - Basic health check
- `/api/v1/analytics/investments/compare` - Compare investment performance
- `/api/v1/analytics/portfolio/analysis` - Get portfolio analysis
- `/api/v1/auth/register` - User registration
- `/api/v1/auth/login` - User login

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8001
```

### Database Initialization

After deployment, initialize the database:

```bash
python init_railway_db.py
```