import React, { lazy, Suspense } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';

// Dynamic import for D3.js to avoid build issues
const D3EfficientFrontier = lazy(() => import('./D3EfficientFrontier').then(module => ({ default: module.D3EfficientFrontier })));

interface PortfolioPoint {
  risk: number;
  return: number;
  sharpeRatio: number;
  volatility: number;
  expectedReturn: number;
  weights?: { [key: string]: number };
}

interface EfficientFrontierProps {
  id?: string;
  portfolioData?: PortfolioPoint[];
  currentPortfolio?: PortfolioPoint;
  onPointSelect?: (portfolio: PortfolioPoint) => void;
  onRiskReturnChange?: (risk: number, expectedReturn: number) => void;
  className?: string;
}

const EfficientFrontier: React.FC<EfficientFrontierProps> = (props) => {
  return (
    <Card className={`w-full ${props.className || ""}`} id={props.id}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Efficient Frontier
        </CardTitle>
        <CardDescription>
          Portfolio risk vs return optimization curve
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Suspense 
          fallback={
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          }
        >
          <D3EfficientFrontier {...props} />
        </Suspense>
      </CardContent>
    </Card>
  );
};

export default EfficientFrontier;