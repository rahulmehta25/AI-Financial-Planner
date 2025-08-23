# AI Financial Planning System - Frontend

## Overview
Modern React-based frontend for the AI Financial Planning System, providing an intuitive interface for financial management, portfolio analysis, and AI-powered recommendations.

## Tech Stack
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Radix UI** for component library
- **Recharts** for data visualization
- **React Query** for API state management
- **React Router** for navigation

## Getting Started

### Prerequisites
- Node.js 18+ and npm installed
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Application pages
│   ├── services/       # API services
│   ├── config/         # Configuration files
│   ├── hooks/          # Custom React hooks
│   └── lib/            # Utility functions
├── public/             # Static assets
└── package.json        # Dependencies
```

## Features

- **Dashboard**: Real-time portfolio overview and insights
- **Portfolio Management**: Track holdings and performance
- **Goal Planning**: Set and monitor financial goals
- **AI Chat**: Interactive financial advisor
- **Analytics**: Advanced charts and reports
- **Simulations**: Monte Carlo and portfolio optimization

## API Integration

The frontend connects to the backend API at `http://localhost:8000`. Configuration can be found in `src/config/api.ts`.

## Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=AI Financial Planning System
```

## Development

```bash
# Run linter
npm run lint

# Type checking
npm run type-check

# Run tests
npm test
```

## Building for Production

```bash
# Create optimized build
npm run build

# Preview production build locally
npm run preview
```

## Docker Support

```bash
# Build Docker image
docker build -t financial-planning-frontend .

# Run container
docker run -p 3000:80 financial-planning-frontend
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

Proprietary - All rights reserved