import React, { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Link2, 
  Shield, 
  CheckCircle, 
  AlertTriangle, 
  Loader2,
  ExternalLink,
  RefreshCw,
  X,
  Building,
  CreditCard,
  DollarSign,
  Lock
} from 'lucide-react';
import { PlaidLinkButtonProps, PlaidAccount, PlaidInstitution } from '@/types/accounts';

// Mock Plaid Link implementation for demonstration
// In production, you would use the actual Plaid Link SDK
interface PlaidLinkHandler {
  open: () => void;
  exit: (options?: any) => void;
  destroy: () => void;
}

interface PlaidLinkProps {
  clientName: string;
  env: 'sandbox' | 'development' | 'production';
  product: string[];
  publicKey: string;
  onSuccess: (publicToken: string, metadata: any) => void;
  onExit?: (error: any, metadata: any) => void;
  onLoad?: () => void;
}

// Mock Plaid Link implementation
const createPlaidLink = (config: PlaidLinkProps): PlaidLinkHandler => {
  return {
    open: () => {
      // Simulate Plaid Link opening
      setTimeout(() => {
        if (config.onLoad) {
          config.onLoad();
        }
        
        // Simulate successful account linking after 2 seconds
        setTimeout(() => {
          const mockMetadata = {
            institution: {
              name: 'Chase',
              institution_id: 'ins_3'
            },
            accounts: [
              {
                id: 'acc_1',
                name: 'Chase Checking',
                mask: '0000',
                type: 'depository',
                subtype: 'checking'
              },
              {
                id: 'acc_2', 
                name: 'Chase Savings',
                mask: '1111',
                type: 'depository',
                subtype: 'savings'
              }
            ],
            link_session_id: 'link-session-123'
          };
          
          config.onSuccess('public-sandbox-token-123', mockMetadata);
        }, 2000);
      }, 100);
    },
    exit: (options?: any) => {
      if (config.onExit) {
        config.onExit(null, { status: 'cancelled' });
      }
    },
    destroy: () => {
      // Cleanup
    }
  };
};

const PlaidLinkButton: React.FC<PlaidLinkButtonProps> = ({
  onSuccess,
  onExit,
  onLoad,
  className = '',
  disabled = false,
  variant = 'default'
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [linkHandler, setLinkHandler] = useState<PlaidLinkHandler | null>(null);

  const handleSuccess = useCallback((publicToken: string, metadata: any) => {
    setIsLoading(false);
    setError(null);
    onSuccess(publicToken, metadata);
  }, [onSuccess]);

  const handleExit = useCallback((error: any, metadata: any) => {
    setIsLoading(false);
    if (error) {
      setError(error.message || 'Failed to link account');
    }
    if (onExit) {
      onExit(error, metadata);
    }
  }, [onExit]);

  const handleLoad = useCallback(() => {
    setIsLoading(true);
    if (onLoad) {
      onLoad();
    }
  }, [onLoad]);

  useEffect(() => {
    // Initialize Plaid Link
    const config: PlaidLinkProps = {
      clientName: 'Financial Planning App',
      env: 'sandbox', // Use 'production' in real app
      product: ['transactions', 'accounts', 'investments'],
      publicKey: process.env.REACT_APP_PLAID_PUBLIC_KEY || 'test-key',
      onSuccess: handleSuccess,
      onExit: handleExit,
      onLoad: handleLoad
    };

    const handler = createPlaidLink(config);
    setLinkHandler(handler);

    return () => {
      if (handler) {
        handler.destroy();
      }
    };
  }, [handleSuccess, handleExit, handleLoad]);

  const handleClick = () => {
    if (linkHandler && !disabled && !isLoading) {
      setError(null);
      linkHandler.open();
    }
  };

  return (
    <div id="plaid-link-container" className="space-y-4">
      <Button
        id="plaid-link-button"
        onClick={handleClick}
        disabled={disabled || isLoading || !linkHandler}
        variant={variant}
        className={`${className} relative`}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Connecting...
          </>
        ) : (
          <>
            <Link2 className="h-4 w-4 mr-2" />
            Link Bank Account
          </>
        )}
      </Button>

      {error && (
        <Alert id="plaid-link-error" className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {error}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setError(null)}
              className="ml-2 h-auto p-0 text-red-600 hover:text-red-800"
            >
              <X className="h-3 w-3" />
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

// Enhanced Plaid Link component with institution selection
export const PlaidLinkWithInstitutions: React.FC<PlaidLinkButtonProps & {
  showInstitutions?: boolean;
  supportedInstitutions?: PlaidInstitution[];
}> = ({
  onSuccess,
  onExit,
  onLoad,
  className = '',
  disabled = false,
  variant = 'default',
  showInstitutions = true,
  supportedInstitutions = []
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentlyLinked, setRecentlyLinked] = useState<any[]>([]);

  const popularInstitutions = [
    { name: 'Chase', logo: '🏦', supported: true },
    { name: 'Bank of America', logo: '🏛️', supported: true },
    { name: 'Wells Fargo', logo: '🏪', supported: true },
    { name: 'Citi', logo: '🏢', supported: true },
    { name: 'Capital One', logo: '🏬', supported: true },
    { name: 'US Bank', logo: '🏦', supported: true },
    { name: 'TD Bank', logo: '🏛️', supported: true },
    { name: 'PNC Bank', logo: '🏪', supported: true }
  ];

  const handleSuccess = useCallback((publicToken: string, metadata: any) => {
    setIsLoading(false);
    setError(null);
    
    // Add to recently linked
    setRecentlyLinked(prev => [{
      institution: metadata.institution,
      accounts: metadata.accounts,
      linkedAt: new Date().toISOString()
    }, ...prev.slice(0, 2)]); // Keep only last 3
    
    onSuccess(publicToken, metadata);
  }, [onSuccess]);

  const handleExit = useCallback((error: any, metadata: any) => {
    setIsLoading(false);
    if (error) {
      setError(error.message || 'Failed to link account');
    }
    if (onExit) {
      onExit(error, metadata);
    }
  }, [onExit]);

  return (
    <Card id="plaid-link-enhanced-container">
      <CardHeader id="plaid-link-header">
        <CardTitle className="flex items-center space-x-2">
          <Link2 className="h-5 w-5" />
          <span>Connect Your Accounts</span>
        </CardTitle>
        <p className="text-sm text-gray-600">
          Securely link your bank accounts to get a complete financial picture
        </p>
      </CardHeader>

      <CardContent id="plaid-link-content" className="space-y-6">
        {/* Security Information */}
        <div id="security-info" className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-green-800 mb-2">
                Bank-level Security
              </h4>
              <ul className="text-xs text-green-700 space-y-1">
                <li className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3" />
                  <span>256-bit SSL encryption</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3" />
                  <span>Read-only access to your data</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3" />
                  <span>Never store your bank credentials</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Main Link Button */}
        <div id="main-link-section" className="text-center">
          <PlaidLinkButton
            onSuccess={handleSuccess}
            onExit={handleExit}
            onLoad={onLoad}
            disabled={disabled}
            variant="default"
            className="w-full h-12 text-lg"
          />
          <p className="text-xs text-gray-500 mt-2">
            Powered by Plaid • Trusted by millions
          </p>
        </div>

        {/* Recently Linked Accounts */}
        {recentlyLinked.length > 0 && (
          <div id="recently-linked-section" className="space-y-3">
            <h4 className="text-sm font-medium text-gray-900">Recently Connected</h4>
            {recentlyLinked.map((linked, index) => (
              <div
                key={index}
                id={`recently-linked-${index}`}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Building className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {linked.institution.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {linked.accounts.length} account{linked.accounts.length !== 1 ? 's' : ''} connected
                    </p>
                  </div>
                </div>
                <Badge className="bg-green-100 text-green-800">
                  Connected
                </Badge>
              </div>
            ))}
          </div>
        )}

        {/* Popular Institutions */}
        {showInstitutions && (
          <div id="popular-institutions-section" className="space-y-3">
            <h4 className="text-sm font-medium text-gray-900">Popular Institutions</h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {popularInstitutions.map((institution, index) => (
                <div
                  key={index}
                  id={`institution-${index}`}
                  className={`p-3 border rounded-lg text-center transition-colors ${
                    institution.supported
                      ? 'border-gray-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer'
                      : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-50'
                  }`}
                  onClick={institution.supported ? () => {
                    // Could trigger Plaid Link with pre-selected institution
                  } : undefined}
                >
                  <div className="text-2xl mb-1">{institution.logo}</div>
                  <p className="text-xs font-medium text-gray-900">
                    {institution.name}
                  </p>
                  {institution.supported && (
                    <Badge className="mt-1 bg-green-100 text-green-800 text-xs">
                      Supported
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* What Gets Connected */}
        <div id="connection-info-section" className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-3">
            What information do we access?
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-blue-800">
            <div className="flex items-start space-x-2">
              <CreditCard className="h-4 w-4 mt-0.5" />
              <div>
                <p className="font-medium">Account Details</p>
                <p>Account names, types, balances</p>
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <DollarSign className="h-4 w-4 mt-0.5" />
              <div>
                <p className="font-medium">Transactions</p>
                <p>Recent transaction history</p>
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <Lock className="h-4 w-4 mt-0.5" />
              <div>
                <p className="font-medium">Identity</p>
                <p>Account holder information</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <Alert id="plaid-enhanced-error" className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              <div className="flex items-center justify-between">
                <span>{error}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setError(null)}
                  className="h-auto p-1 text-red-600 hover:text-red-800"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Help Links */}
        <div id="help-links-section" className="text-center space-y-2 pt-4 border-t">
          <p className="text-xs text-gray-500">
            Need help? 
            <button className="ml-1 text-blue-600 hover:text-blue-800 underline">
              View supported institutions
            </button>
            {' • '}
            <button className="text-blue-600 hover:text-blue-800 underline">
              Security FAQ
            </button>
          </p>
          <div className="flex items-center justify-center space-x-2 text-xs text-gray-400">
            <ExternalLink className="h-3 w-3" />
            <span>Powered by Plaid</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PlaidLinkButton;