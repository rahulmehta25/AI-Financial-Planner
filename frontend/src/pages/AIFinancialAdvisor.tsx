import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { 
  Brain, 
  TrendingUp, 
  AlertTriangle, 
  BookOpen, 
  DollarSign,
  PieChart,
  Target,
  Info,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { advisorApi, portfolioApi } from '../services/api';

interface TaxOpportunity {
  symbol: string;
  unrealized_loss: string;
  action: string;
  warning: string;
  alternative?: string;
}

interface ContributionStrategy {
  priority: number;
  action: string;
  reason: string;
}

interface FinancialConcept {
  term: string;
  explanation: string;
}

const AIFinancialAdvisor: React.FC = () => {
  const [activeTab, setActiveTab] = useState('health');
  const [healthAnalysis, setHealthAnalysis] = useState<any>(null);
  const [taxOpportunities, setTaxOpportunities] = useState<any>(null);
  const [allocationAdvice, setAllocationAdvice] = useState<any>(null);
  const [selectedConcept, setSelectedConcept] = useState<string>('');
  const [conceptExplanation, setConceptExplanation] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const financialConcepts = [
    'diversification',
    'expense_ratio',
    'compound_interest',
    'dollar_cost_averaging',
    'rebalancing',
    'tax_loss_harvesting'
  ];

  // Fetch portfolio health analysis
  const fetchHealthAnalysis = async () => {
    setLoading(true);
    try {
      const data = await portfolioApi.getHealth();
      setHealthAnalysis(data);
    } catch (err) {
      console.error('Failed to fetch health analysis', err);
    }
    setLoading(false);
  };

  // Fetch tax opportunities
  const fetchTaxOpportunities = async () => {
    setLoading(true);
    try {
      const data = await advisorApi.getTaxOpportunities();
      setTaxOpportunities(data);
    } catch (err) {
      console.error('Failed to fetch tax opportunities', err);
    }
    setLoading(false);
  };

  // Fetch allocation advice
  const fetchAllocationAdvice = async () => {
    setLoading(true);
    try {
      const data = await advisorApi.getInvestmentGuidance();
      setAllocationAdvice(data);
    } catch (err) {
      console.error('Failed to fetch allocation advice', err);
    }
    setLoading(false);
  };

  // Explain financial concept
  const explainConcept = async (concept: string) => {
    setLoading(true);
    try {
      // For now, use local explanations since this endpoint isn't in the API yet
      const explanations: { [key: string]: string } = {
        'diversification': 'Spreading investments across various assets to reduce risk. Don\'t put all your eggs in one basket.',
        'expense_ratio': 'The annual fee charged by funds, expressed as a percentage. Lower is better - aim for under 0.2%.',
        'compound_interest': 'Earning returns on your returns. The most powerful force in investing - start early!',
        'dollar_cost_averaging': 'Investing fixed amounts regularly, regardless of price. Reduces timing risk.',
        'rebalancing': 'Adjusting portfolio back to target allocation. Sells high, buys low automatically.',
        'tax_loss_harvesting': 'Selling losing investments to offset gains and reduce taxes. Watch for wash sale rules.'
      };
      const data = { explanation: explanations[concept] || 'Concept explanation not available.' };
      setConceptExplanation(data.explanation);
      setSelectedConcept(concept);
    } catch (err) {
      console.error('Failed to fetch concept explanation', err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchHealthAnalysis();
    fetchTaxOpportunities();
    fetchAllocationAdvice();
  }, []);

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <Brain className="h-8 w-8 mr-3 text-blue-600" />
          <h1 className="text-3xl font-bold">AI Financial Advisor</h1>
        </div>
        <p className="text-gray-600">Educational guidance based on established financial principles</p>
        
        <Alert className="mt-4">
          <Info className="h-4 w-4" />
          <AlertTitle>Educational Purpose Only</AlertTitle>
          <AlertDescription>
            This AI provides educational information based on established financial principles. 
            It does not provide personalized investment advice. Always consult with qualified 
            professionals for your specific situation.
          </AlertDescription>
        </Alert>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="health">Portfolio Health</TabsTrigger>
          <TabsTrigger value="tax">Tax Optimization</TabsTrigger>
          <TabsTrigger value="allocation">Asset Allocation</TabsTrigger>
          <TabsTrigger value="education">Learn Concepts</TabsTrigger>
        </TabsList>

        {/* Portfolio Health Tab */}
        <TabsContent value="health">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Risk Factors */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertTriangle className="mr-2 h-5 w-5 text-yellow-500" />
                  Risk Factors
                </CardTitle>
              </CardHeader>
              <CardContent>
                {healthAnalysis?.risk_factors?.length > 0 ? (
                  <div className="space-y-4">
                    {healthAnalysis.risk_factors.map((risk: any, index: number) => (
                      <div key={index} className="border-l-4 border-yellow-500 pl-4">
                        <div className="flex items-center mb-1">
                          <span className={`text-xs px-2 py-1 rounded mr-2 ${
                            risk.severity === 'high' ? 'bg-red-100 text-red-700' :
                            risk.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {risk.severity}
                          </span>
                          <p className="font-medium">{risk.message}</p>
                        </div>
                        <p className="text-sm text-gray-600">
                          <BookOpen className="inline h-3 w-3 mr-1" />
                          {risk.education}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No significant risks identified</p>
                )}
              </CardContent>
            </Card>

            {/* Strengths & Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                  Strengths & Actions
                </CardTitle>
              </CardHeader>
              <CardContent>
                {healthAnalysis?.strengths?.length > 0 && (
                  <div className="mb-4">
                    <p className="font-medium mb-2">Portfolio Strengths:</p>
                    <ul className="space-y-1">
                      {healthAnalysis.strengths.map((strength: string, index: number) => (
                        <li key={index} className="flex items-center text-sm">
                          <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {healthAnalysis?.action_items?.length > 0 && (
                  <div>
                    <p className="font-medium mb-2">Recommended Actions:</p>
                    <div className="space-y-2">
                      {healthAnalysis.action_items.map((item: any, index: number) => (
                        <div key={index} className="bg-blue-50 p-3 rounded">
                          <p className="font-medium text-sm">{item.action}</p>
                          <p className="text-xs text-gray-600 mt-1">{item.rationale}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tax Optimization Tab */}
        <TabsContent value="tax">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Tax Loss Harvesting */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <DollarSign className="mr-2 h-5 w-5" />
                  Tax Loss Harvesting Opportunities
                </CardTitle>
              </CardHeader>
              <CardContent>
                {taxOpportunities?.tax_loss_harvesting?.length > 0 ? (
                  <div className="space-y-3">
                    {taxOpportunities.tax_loss_harvesting.map((opp: TaxOpportunity, index: number) => (
                      <div key={index} className="border rounded p-3">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium">{opp.symbol}</span>
                          <span className="text-red-600 font-medium">{opp.unrealized_loss}</span>
                        </div>
                        <p className="text-sm text-gray-600">{opp.action}</p>
                        <Alert className="mt-2">
                          <AlertDescription className="text-xs">
                            {opp.warning}
                          </AlertDescription>
                        </Alert>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No tax loss harvesting opportunities currently available</p>
                )}
              </CardContent>
            </Card>

            {/* Contribution Strategies */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="mr-2 h-5 w-5" />
                  Contribution Priority Guide
                </CardTitle>
              </CardHeader>
              <CardContent>
                {taxOpportunities?.contribution_strategies && (
                  <div className="space-y-3">
                    {taxOpportunities.contribution_strategies.map((strategy: ContributionStrategy) => (
                      <div key={strategy.priority} className="flex">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium">
                          {strategy.priority}
                        </div>
                        <div className="ml-3 flex-1">
                          <p className="font-medium text-sm">{strategy.action}</p>
                          <p className="text-xs text-gray-600 mt-1">{strategy.reason}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Account Placement Guide */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Asset Location Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Asset Type</th>
                      <th className="text-left p-2">Best Account</th>
                      <th className="text-left p-2">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {taxOpportunities?.account_placement?.map((placement: any, index: number) => (
                      <tr key={index} className="border-b">
                        <td className="p-2">{placement.asset_type}</td>
                        <td className="p-2 font-medium">{placement.best_account}</td>
                        <td className="p-2 text-sm text-gray-600">{placement.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Asset Allocation Tab */}
        <TabsContent value="allocation">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {allocationAdvice?.classic_strategies && Object.entries(allocationAdvice.classic_strategies).map(([key, strategy]: [string, any]) => (
              <Card key={key}>
                <CardHeader>
                  <CardTitle className="text-lg">{strategy.description}</CardTitle>
                </CardHeader>
                <CardContent>
                  {strategy.allocation && (
                    <div className="mb-4">
                      <p className="text-sm font-medium mb-2">Allocation:</p>
                      {Object.entries(strategy.allocation).map(([asset, percent]) => (
                        <div key={asset} className="flex justify-between text-sm">
                          <span>{asset}:</span>
                          <span className="font-medium">{percent as string}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {strategy.example_etfs && (
                    <div className="mb-4">
                      <p className="text-sm font-medium mb-1">Example ETFs:</p>
                      <div className="flex gap-2">
                        {strategy.example_etfs.map((etf: string) => (
                          <span key={etf} className="px-2 py-1 bg-gray-100 rounded text-xs">
                            {etf}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {strategy.pros && (
                    <p className="text-sm text-green-600 mb-2">
                      <CheckCircle className="inline h-3 w-3 mr-1" />
                      {strategy.pros}
                    </p>
                  )}
                  
                  {strategy.cons && (
                    <p className="text-sm text-red-600">
                      <XCircle className="inline h-3 w-3 mr-1" />
                      {strategy.cons}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Risk Considerations */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Risk Considerations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {allocationAdvice?.risk_considerations?.map((consideration: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <Info className="h-4 w-4 mr-2 mt-0.5 text-blue-500" />
                    <span className="text-sm">{consideration}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Education Tab */}
        <TabsContent value="education">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Concept Selector */}
            <Card>
              <CardHeader>
                <CardTitle>Learn Financial Concepts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {financialConcepts.map((concept) => (
                    <Button
                      key={concept}
                      variant={selectedConcept === concept ? "default" : "outline"}
                      className="w-full justify-start"
                      onClick={() => explainConcept(concept)}
                    >
                      <BookOpen className="mr-2 h-4 w-4" />
                      {concept.replace(/_/g, ' ').charAt(0).toUpperCase() + concept.replace(/_/g, ' ').slice(1)}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Concept Explanation */}
            <Card>
              <CardHeader>
                <CardTitle>
                  {selectedConcept ? 
                    selectedConcept.replace(/_/g, ' ').charAt(0).toUpperCase() + selectedConcept.replace(/_/g, ' ').slice(1) : 
                    'Select a Concept'
                  }
                </CardTitle>
              </CardHeader>
              <CardContent>
                {conceptExplanation ? (
                  <div className="prose prose-sm">
                    <p className="whitespace-pre-wrap">{conceptExplanation}</p>
                  </div>
                ) : (
                  <p className="text-gray-500">
                    Select a financial concept from the left to learn more about it.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Market Context */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Historical Market Context</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded">
                  <p className="text-2xl font-bold">~10%</p>
                  <p className="text-sm text-gray-600">S&P 500 Average Annual Return (1926-2023)</p>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded">
                  <p className="text-2xl font-bold">3-4</p>
                  <p className="text-sm text-gray-600">Corrections (5-10% decline) per year</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded">
                  <p className="text-2xl font-bold">100%</p>
                  <p className="text-sm text-gray-600">Historical Recovery Rate from Bear Markets</p>
                </div>
              </div>
              
              <Alert className="mt-4">
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Remember: Time in the market beats timing the market. Your investment timeline 
                  matters more than daily movements.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AIFinancialAdvisor;