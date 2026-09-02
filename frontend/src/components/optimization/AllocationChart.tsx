import React, { lazy, Suspense } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart } from 'lucide-react';

// Dynamic import for D3.js to avoid build issues
const D3AllocationChart = lazy(() => import('./D3AllocationChart').then(module => ({ default: module.D3AllocationChart })));

interface AssetAllocation {
  id: string;
  name: string;
  symbol: string;
  percentage: number;
  color: string;
  locked?: boolean;
  minAllocation?: number;
  maxAllocation?: number;
  expectedReturn?: number;
  risk?: number;
}

interface AllocationChartProps {
  id?: string;
  allocations: AssetAllocation[];
  onAllocationChange?: (allocations: AssetAllocation[]) => void;
  editable?: boolean;
  showControls?: boolean;
  className?: string;
}

const AllocationChart: React.FC<AllocationChartProps> = (props) => {
  return (
    <Card className={`w-full ${props.className || ""}`} id={props.id}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PieChart className="h-5 w-5" />
          Asset Allocation
        </CardTitle>
        <CardDescription>
          Interactive portfolio allocation chart
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
          <D3AllocationChart {...props} />
        </Suspense>
      </CardContent>
    </Card>
  );
};

export default AllocationChart;