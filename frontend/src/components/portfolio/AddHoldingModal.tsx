import React, { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Plus, Search } from 'lucide-react'
import { portfolioService } from '@/services/portfolio'
import { fetchMarketData } from '@/lib/supabase'
import { useToast } from '@/hooks/use-toast'

interface AddHoldingModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export const AddHoldingModal: React.FC<AddHoldingModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [symbol, setSymbol] = useState('')
  const [shares, setShares] = useState('')
  const [costBasis, setCostBasis] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [verifiedName, setVerifiedName] = useState('')
  const [error, setError] = useState('')
  const { toast } = useToast()

  const handleVerifySymbol = async () => {
    if (!symbol) return
    
    setIsVerifying(true)
    setError('')
    setVerifiedName('')
    
    try {
      const data = await fetchMarketData('quote', symbol.toUpperCase())
      if (data && data[0]) {
        setVerifiedName(data[0].name || symbol.toUpperCase())
        toast({
          title: 'Symbol verified',
          description: `Found: ${data[0].name} - Current price: $${data[0].price.toFixed(2)}`,
        })
      } else {
        setError('Symbol not found. Please check and try again.')
      }
    } catch (err) {
      setError('Failed to verify symbol. Please try again.')
    } finally {
      setIsVerifying(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!symbol || !shares || !costBasis) {
      setError('Please fill in all fields')
      return
    }
    
    if (!verifiedName) {
      setError('Please verify the symbol first')
      return
    }
    
    setIsLoading(true)
    setError('')
    
    try {
      await portfolioService.addHolding(
        symbol.toUpperCase(),
        parseFloat(shares),
        parseFloat(costBasis)
      )
      
      toast({
        title: 'Holding added',
        description: `Successfully added ${shares} shares of ${verifiedName}`,
      })
      
      onSuccess()
      handleClose()
    } catch (err: any) {
      setError(err.message || 'Failed to add holding')
      toast({
        title: 'Error',
        description: err.message || 'Failed to add holding',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleClose = () => {
    setSymbol('')
    setShares('')
    setCostBasis('')
    setVerifiedName('')
    setError('')
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Holding</DialogTitle>
          <DialogDescription>
            Add a stock or ETF to your portfolio. Enter the symbol and your purchase details.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="symbol">Stock Symbol</Label>
            <div className="flex gap-2">
              <Input
                id="symbol"
                placeholder="e.g., AAPL, MSFT"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={handleVerifySymbol}
                disabled={!symbol || isVerifying || isLoading}
              >
                {isVerifying ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
              </Button>
            </div>
            {verifiedName && (
              <p className="text-sm text-muted-foreground">
                ✓ {verifiedName}
              </p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="shares">Number of Shares</Label>
            <Input
              id="shares"
              type="number"
              step="0.0001"
              placeholder="e.g., 100"
              value={shares}
              onChange={(e) => setShares(e.target.value)}
              disabled={isLoading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="costBasis">Total Cost Basis ($)</Label>
            <Input
              id="costBasis"
              type="number"
              step="0.01"
              placeholder="e.g., 15000.00"
              value={costBasis}
              onChange={(e) => setCostBasis(e.target.value)}
              disabled={isLoading}
            />
            {shares && costBasis && (
              <p className="text-sm text-muted-foreground">
                Average price per share: ${(parseFloat(costBasis) / parseFloat(shares)).toFixed(2)}
              </p>
            )}
          </div>
          
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !verifiedName}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Holding
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}