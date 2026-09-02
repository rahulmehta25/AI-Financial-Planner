import { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Eye, EyeOff, TrendingUp, Check, X, CheckCircle } from "lucide-react";
import { authService } from "@/services/authService";
import { useToast } from "@/hooks/use-toast";

const ResetPasswordPage = () => {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isTokenValid, setIsTokenValid] = useState(true);
  const [isResetComplete, setIsResetComplete] = useState(false);
  const [errors, setErrors] = useState<{ 
    password?: string; 
    confirmPassword?: string; 
    token?: string;
    general?: string;
  }>({});

  const { toast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  // Password strength indicators
  const getPasswordStrength = (password: string) => {
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };

    const score = Object.values(checks).filter(Boolean).length;
    return { checks, score };
  };

  const passwordStrength = getPasswordStrength(password);

  // Validate token on component mount
  useEffect(() => {
    if (!token) {
      setErrors({ token: "Invalid or missing reset token" });
      setIsTokenValid(false);
      return;
    }

    // You could add a token validation API call here
    // For now, we'll assume the token is valid if it exists
  }, [token]);

  const validateForm = () => {
    const newErrors: typeof errors = {};

    if (!token) {
      newErrors.token = "Invalid or missing reset token";
      setIsTokenValid(false);
      return false;
    }

    // Password validation
    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (passwordStrength.score < 3) {
      newErrors.password = "Please choose a stronger password";
    }

    // Confirm password validation
    if (!confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!validateForm() || !token) {
      return;
    }

    setIsLoading(true);

    try {
      await authService.confirmPasswordReset({
        token,
        newPassword: password,
      });

      setIsResetComplete(true);
      toast({
        title: "Password reset successful!",
        description: "Your password has been updated. You can now sign in with your new password.",
      });

      // Auto-redirect to login after 3 seconds
      setTimeout(() => {
        navigate("/login");
      }, 3000);

    } catch (error: any) {
      const errorMessage = error.message || "Failed to reset password. Please try again.";
      if (errorMessage.includes("token") || errorMessage.includes("expired")) {
        setErrors({ token: "Reset link has expired or is invalid" });
        setIsTokenValid(false);
      } else {
        setErrors({ general: errorMessage });
      }
      toast({
        title: "Password reset failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const PasswordStrengthIndicator = ({ checks, score }: { checks: any; score: number }) => {
    const getStrengthColor = () => {
      if (score < 2) return "bg-destructive";
      if (score < 4) return "bg-yellow-500";
      return "bg-success";
    };

    const getStrengthText = () => {
      if (score < 2) return "Weak";
      if (score < 4) return "Medium";
      return "Strong";
    };

    return (
      <div id="password-strength" className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${getStrengthColor()}`}
              style={{ width: `${(score / 5) * 100}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground">{getStrengthText()}</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className={`flex items-center gap-1 ${checks.length ? 'text-success' : 'text-muted-foreground'}`}>
            {checks.length ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            8+ characters
          </div>
          <div className={`flex items-center gap-1 ${checks.uppercase ? 'text-success' : 'text-muted-foreground'}`}>
            {checks.uppercase ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            Uppercase
          </div>
          <div className={`flex items-center gap-1 ${checks.lowercase ? 'text-success' : 'text-muted-foreground'}`}>
            {checks.lowercase ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            Lowercase
          </div>
          <div className={`flex items-center gap-1 ${checks.number ? 'text-success' : 'text-muted-foreground'}`}>
            {checks.number ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            Number
          </div>
        </div>
      </div>
    );
  };

  // Success state
  if (isResetComplete) {
    return (
      <div id="reset-password-success-page" className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center p-4">
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
                <CardTitle className="text-2xl">Password Reset Complete</CardTitle>
                <CardDescription className="mt-2">
                  Your password has been successfully updated. You will be redirected to the login page shortly.
                </CardDescription>
              </div>
            </CardHeader>

            <CardFooter id="success-footer">
              <Link to="/login" className="w-full">
                <Button id="continue-to-login-button" className="w-full bg-gradient-to-r from-primary to-primary-hover">
                  Continue to Sign In
                </Button>
              </Link>
            </CardFooter>
          </Card>
        </div>
      </div>
    );
  }

  // Invalid token state
  if (!isTokenValid || errors.token) {
    return (
      <div id="reset-password-invalid-page" className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center p-4">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-success/10 rounded-full blur-3xl" />
        </div>

        <div id="invalid-token-container" className="relative w-full max-w-md">
          <Card id="invalid-token-card" className="glass border-white/10">
            <CardHeader id="invalid-token-header" className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 rounded-full bg-destructive/20 flex items-center justify-center">
                <X className="w-8 h-8 text-destructive" />
              </div>
              <div>
                <CardTitle className="text-2xl">Invalid Reset Link</CardTitle>
                <CardDescription className="mt-2">
                  This password reset link is invalid or has expired. Please request a new reset link.
                </CardDescription>
              </div>
            </CardHeader>

            <CardFooter id="invalid-token-footer" className="flex flex-col space-y-3">
              <Link to="/forgot-password" className="w-full">
                <Button id="request-new-link-button" className="w-full bg-gradient-to-r from-primary to-primary-hover">
                  Request New Reset Link
                </Button>
              </Link>
              <Link to="/login" className="w-full">
                <Button id="back-to-login-button" variant="outline" className="w-full glass border-white/20">
                  Back to Sign In
                </Button>
              </Link>
            </CardFooter>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div id="reset-password-page" className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-success/10 rounded-full blur-3xl" />
      </div>

      <div id="reset-password-container" className="relative w-full max-w-md">
        {/* Logo and branding */}
        <div id="reset-password-branding" className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-success flex items-center justify-center">
              <TrendingUp className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-success">
              FinanceAI
            </span>
          </div>
          <p className="text-muted-foreground text-sm">
            Create a new secure password for your account
          </p>
        </div>

        <Card id="reset-password-card" className="glass border-white/10">
          <CardHeader id="reset-password-header" className="space-y-1">
            <CardTitle className="text-2xl text-center">Reset Password</CardTitle>
            <CardDescription className="text-center">
              Enter your new password below
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent id="reset-password-form" className="space-y-4">
              {errors.general && (
                <Alert id="reset-password-error-alert" variant="destructive">
                  <AlertDescription>{errors.general}</AlertDescription>
                </Alert>
              )}

              <div id="password-field" className="space-y-2">
                <Label htmlFor="password">New Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your new password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errors.password) {
                        setErrors(prev => ({ ...prev, password: undefined }));
                      }
                    }}
                    className={`glass border-white/20 pr-10 ${errors.password ? 'border-destructive' : ''}`}
                    disabled={isLoading}
                  />
                  <Button
                    id="toggle-password"
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                </div>
                {password && (
                  <PasswordStrengthIndicator checks={passwordStrength.checks} score={passwordStrength.score} />
                )}
                {errors.password && (
                  <p id="password-error" className="text-sm text-destructive">{errors.password}</p>
                )}
              </div>

              <div id="confirm-password-field" className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your new password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (errors.confirmPassword) {
                        setErrors(prev => ({ ...prev, confirmPassword: undefined }));
                      }
                    }}
                    className={`glass border-white/20 pr-10 ${errors.confirmPassword ? 'border-destructive' : ''}`}
                    disabled={isLoading}
                  />
                  <Button
                    id="toggle-confirm-password"
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                </div>
                {errors.confirmPassword && (
                  <p id="confirm-password-error" className="text-sm text-destructive">{errors.confirmPassword}</p>
                )}
              </div>
            </CardContent>

            <CardFooter id="reset-password-footer" className="flex flex-col space-y-4">
              <Button
                id="reset-password-submit-button"
                type="submit"
                className="w-full bg-gradient-to-r from-primary to-primary-hover hover:shadow-glow"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating Password...
                  </>
                ) : (
                  "Update Password"
                )}
              </Button>

              <div id="back-to-login-link" className="text-center text-sm">
                <span className="text-muted-foreground">Remember your password? </span>
                <Link
                  to="/login"
                  className="text-primary hover:text-primary/80 font-medium transition-colors"
                >
                  Sign in
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default ResetPasswordPage;