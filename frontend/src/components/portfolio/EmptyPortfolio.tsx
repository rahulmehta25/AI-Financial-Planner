import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PieChart, Plus, TrendingUp, BarChart3 } from 'lucide-react'

interface EmptyPortfolioProps {
  onAddHolding: () => void
}

export const EmptyPortfolio: React.FC<EmptyPortfolioProps> = ({ onAddHolding }) => {
  return (
    <div className="mt-8">
      <Card className="glass border-white/20">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 to-success/20 flex items-center justify-center">
            <PieChart className="w-10 h-10 text-primary" />
          </div>
          <CardTitle className="text-2xl">Welcome to Your Portfolio</CardTitle>
          <CardDescription className="text-base mt-2">
            Start building your investment portfolio by adding your first holding
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center pb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="p-4 rounded-lg bg-muted/50">
              <TrendingUp className="w-8 h-8 text-success mx-auto mb-2" />
              <h3 className="font-semibold mb-1">Track Performance</h3>
              <p className="text-sm text-muted-foreground">
                Monitor real-time market data and portfolio growth
              </p>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <BarChart3 className="w-8 h-8 text-primary mx-auto mb-2" />
              <h3 className="font-semibold mb-1">Analyze Holdings</h3>
              <p className="text-sm text-muted-foreground">
                Get insights into your asset allocation and risk
              </p>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <PieChart className="w-8 h-8 text-accent mx-auto mb-2" />
              <h3 className="font-semibold mb-1">Optimize Strategy</h3>
              <p className="text-sm text-muted-foreground">
                Receive AI-powered recommendations for your portfolio
              </p>
            </div>
          </div>
          
          <Button 
            onClick={onAddHolding}
            size="lg"
            className="bg-gradient-to-r from-primary to-success hover:opacity-90"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add Your First Holding
          </Button>
          
          <p className="text-sm text-muted-foreground mt-4">
            Add stocks, ETFs, or other investments to start tracking your portfolio
          </p>
        </CardContent>
      </Card>
    </div>
  )
}