import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, TrendingUp, ArrowLeft, Mail, CheckCircle } from "lucide-react";
import { authService } from "@/services/authService";
import { useToast } from "@/hooks/use-toast";

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isEmailSent, setIsEmailSent] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; general?: string }>({});

  const { toast } = useToast();

  const validateForm = () => {
    const newErrors: typeof errors = {};

    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await authService.requestPasswordReset({ email });
      setIsEmailSent(true);
      toast({
        title: "Reset email sent!",
        description: "Check your email for password reset instructions.",
      });
    } catch (error: any) {
      const errorMessage = error.message || "Failed to send reset email. Please try again.";
      setErrors({ general: errorMessage });
      toast({
        title: "Failed to send email",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendEmail = async () => {
    setIsLoading(true);
    try {
      await authService.requestPasswordReset({ email });
      toast({
        title: "Email resent!",
        description: "Check your email for the new reset instructions.",
      });
    } catch (error: any) {
      toast({
        title: "Failed to resend email",
        description: error.message || "Please try again later.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isEmailSent) {
    return (
      <div id="forgot-password-success-page" className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center p-4">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-success/10 rounded-full blur-3xl" />
        </div>

        <div id="success-container" className="relative w-full max-w-md">
          <Card id="success-card" className="glass border-white/10">
            <CardHeader id="success-header" className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 rounded-full bg-success/20 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-success" />
              </div>
              <div>
                <CardTitle className="text-2xl">Check your email</CardTitle>
                <CardDescription className="mt-2">
                  We've sent password reset instructions to
                  <br />
                  <strong>{email}</strong>
                </CardDescription>
              </div>
            </CardHeader>

            <CardContent id="success-content" className="text-center space-y-4">
              <div className="p-4 rounded-lg bg-muted/20 border border-white/10">
                <Mail className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Didn't receive the email? Check your spam folder or
                </p>
              </div>
            </CardContent>

            <CardFooter id="success-footer" className="flex flex-col space-y-4">
              <Button
                id="resend-email-button"
                onClick={handleResendEmail}
                variant="outline"
                className="w-full glass border-white/20"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Resending...
                  </>
                ) : (
                  "Resend email"
                )}
              </Button>

              <Link to="/login" className="w-full">
                <Button id="back-to-login-button" variant="ghost" className="w-full">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to sign in
                </Button>
              </Link>
            </CardFooter>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div id="forgot-password-page" className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-success/10 rounded-full blur-3xl" />
      </div>

      <div id="forgot-password-container" className="relative w-full max-w-md">
        {/* Logo and branding */}
        <div id="forgot-password-branding" className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-success flex items-center justify-center">
              <TrendingUp className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-success">
              FinanceAI
            </span>
          </div>
          <p className="text-muted-foreground text-sm">
            Reset your password to regain access
          </p>
        </div>

        <Card id="forgot-password-card" className="glass border-white/10">
          <CardHeader id="forgot-password-header" className="space-y-1">
            <CardTitle className="text-2xl text-center">Forgot Password</CardTitle>
            <CardDescription className="text-center">
              Enter your email address and we'll send you a link to reset your password
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent id="forgot-password-form" className="space-y-4">
              {errors.general && (
                <Alert id="forgot-password-error-alert" variant="destructive">
                  <AlertDescription>{errors.general}</AlertDescription>
                </Alert>
              )}

              <div id="email-field" className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (errors.email) {
                      setErrors(prev => ({ ...prev, email: undefined }));
                    }
                  }}
                  className={`glass border-white/20 ${errors.email ? 'border-destructive' : ''}`}
                  disabled={isLoading}
                  autoFocus
                />
                {errors.email && (
                  <p id="email-error" className="text-sm text-destructive">{errors.email}</p>
                )}
              </div>

              <div id="help-text" className="p-4 rounded-lg bg-muted/10 border border-white/10">
                <p className="text-sm text-muted-foreground">
                  We'll send a secure link to reset your password. The link will expire in 1 hour for your security.
                </p>
              </div>
            </CardContent>

            <CardFooter id="forgot-password-footer" className="flex flex-col space-y-4">
              <Button
                id="reset-password-submit-button"
                type="submit"
                className="w-full bg-gradient-to-r from-primary to-primary-hover hover:shadow-glow"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending Reset Link...
                  </>
                ) : (
                  "Send Reset Link"
                )}
              </Button>

              <Link to="/login" className="w-full">
                <Button id="back-to-login-link-button" variant="ghost" className="w-full">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to sign in
                </Button>
              </Link>

              <div id="register-link" className="text-center text-sm">
                <span className="text-muted-foreground">Don't have an account? </span>
                <Link
                  to="/register"
                  className="text-primary hover:text-primary/80 font-medium transition-colors"
                >
                  Sign up
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;