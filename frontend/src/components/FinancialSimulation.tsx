import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { financialPlanningService, FinancialProfile, SimulationResult } from '@/services/financialPlanning'
import { Calculator, TrendingUp, Target, AlertCircle, CheckCircle } from 'lucide-react'

export const FinancialSimulation = () => {
  const [profile, setProfile] = useState<FinancialProfile>({
    age: 35,
    income: 75000,
    savings: 1500,
    risk_tolerance: 'moderate'
  })
  
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      const simulationResult = await financialPlanningService.runSimulation(profile)
      setResult(simulationResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run simulation')
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'conservative': return 'text-blue-600'
      case 'moderate': return 'text-yellow-600'
      case 'aggressive': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getSuccessColor = (probability: number) => {
    if (probability >= 80) return 'text-green-600'
    if (probability >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      <Card className="glass hover-lift">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-primary" />
            Financial Planning Simulation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="age">Age</Label>
                <Input
                  id="age"
                  type="number"
                  min="18"
                  max="100"
                  value={profile.age}
                  onChange={(e) => setProfile({ ...profile, age: parseInt(e.target.value) })}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="income">Annual Income ($)</Label>
                <Input
                  id="income"
                  type="number"
                  min="10000"
                  value={profile.income}
                  onChange={(e) => setProfile({ ...profile, income: parseInt(e.target.value) })}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="savings">Monthly Savings ($)</Label>
                <Input
                  id="savings"
                  type="number"
                  min="0"
                  value={profile.savings}
                  onChange={(e) => setProfile({ ...profile, savings: parseInt(e.target.value) })}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="risk">Risk Tolerance</Label>
                <Select
                  value={profile.risk_tolerance}
                  onValueChange={(value: 'conservative' | 'moderate' | 'aggressive') => 
                    setProfile({ ...profile, risk_tolerance: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="conservative">Conservative</SelectItem>
                    <SelectItem value="moderate">Moderate</SelectItem>
                    <SelectItem value="aggressive">Aggressive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading}
            >
              {loading ? 'Running Simulation...' : '🚀 Run Simulation'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card className="glass hover-lift animate-slide-in-top">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              Simulation Results
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {result.result.success_probability}%
                </div>
                <div className="text-sm text-blue-600">Success Probability</div>
                <Progress 
                  value={result.result.success_probability} 
                  className="mt-2"
                />
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  ${result.result.median_balance.toLocaleString()}
                </div>
                <div className="text-sm text-green-600">Projected Balance at 65</div>
                <TrendingUp className="h-8 w-8 text-green-600 mx-auto mt-2" />
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {profile.risk_tolerance.charAt(0).toUpperCase() + profile.risk_tolerance.slice(1)}
                </div>
                <div className="text-sm text-purple-600">Risk Profile</div>
                <Target className="h-8 w-8 text-purple-600 mx-auto mt-2" />
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-amber-200">
              <div className="flex items-start gap-2">
                <Target className="h-5 w-5 text-amber-600 mt-0.5" />
                <div>
                  <div className="font-semibold text-amber-800 mb-1">AI Recommendation</div>
                  <div className="text-amber-700">{result.result.recommendation}</div>
                </div>
              </div>
            </div>
            
            <div className="text-xs text-muted-foreground text-center">
              Simulation ID: {result.simulation_id}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
