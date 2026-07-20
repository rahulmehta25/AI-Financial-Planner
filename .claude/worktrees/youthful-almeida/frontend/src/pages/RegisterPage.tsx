import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, Eye, EyeOff, TrendingUp, Check, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{
    firstName?: string;
    lastName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    terms?: string;
    general?: string;
  }>({});

  const { signUp } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

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

  const passwordStrength = getPasswordStrength(formData.password);

  const validateForm = () => {
    const newErrors: typeof errors = {};

    // First name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = "First name is required";
    } else if (formData.firstName.trim().length < 2) {
      newErrors.firstName = "First name must be at least 2 characters";
    }

    // Last name validation
    if (!formData.lastName.trim()) {
      newErrors.lastName = "Last name is required";
    } else if (formData.lastName.trim().length < 2) {
      newErrors.lastName = "Last name must be at least 2 characters";
    }

    // Email validation
    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (passwordStrength.score < 3) {
      newErrors.password = "Please choose a stronger password";
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    // Terms acceptance
    if (!acceptTerms) {
      newErrors.terms = "You must accept the terms and conditions";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof typeof formData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
    // Clear specific field error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const fullName = `${formData.firstName.trim()} ${formData.lastName.trim()}`;
      const result = await signUp(formData.email, formData.password, fullName);

      if (result.error) {
        throw result.error;
      }

      if (result.data?.user) {
        // Check if email confirmation is required
        if (result.data.user.confirmed_at === null) {
          toast({
            title: "Check your email!",
            description: "We've sent you a confirmation email. Please verify your account before signing in.",
          });
          navigate("/login");
        } else {
          // User is confirmed and can sign in
          toast({
            title: "Account created successfully!",
            description: "Welcome to FinanceAI. You can now access your dashboard.",
          });
          navigate("/dashboard");
        }
      } else {
        // Account created but need email confirmation
        toast({
          title: "Account created!",
          description: "Please check your email to confirm your account.",
        });
        navigate("/login");
      }
    } catch (error: any) {
      const errorMessage = error.message || "Registration failed. Please try again.";
      setErrors({ general: errorMessage });
      toast({
        title: "Registration Failed",
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

  return (
    <div id="register-page" className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-success/10 rounded-full blur-3xl" />
      </div>

      <div id="register-container" className="relative w-full max-w-md">
        {/* Logo and branding */}
        <div id="register-branding" className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-success flex items-center justify-center">
              <TrendingUp className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-success">
              FinanceAI
            </span>
          </div>
          <p className="text-muted-foreground text-sm">
            Create your account and start your financial journey
          </p>
        </div>

        <Card id="register-card" className="glass border-white/10">
          <CardHeader id="register-header" className="space-y-1">
            <CardTitle className="text-2xl text-center">Create Account</CardTitle>
            <CardDescription className="text-center">
              Enter your information to get started
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent id="register-form" className="space-y-4">
              {errors.general && (
                <Alert id="register-error-alert" variant="destructive">
                  <AlertDescription>{errors.general}</AlertDescription>
                </Alert>
              )}

              <div id="name-fields" className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    type="text"
                    placeholder="John"
                    value={formData.firstName}
                    onChange={handleInputChange("firstName")}
                    className={`glass border-white/20 ${errors.firstName ? 'border-destructive' : ''}`}
                    disabled={isLoading}
                  />
                  {errors.firstName && (
                    <p id="firstName-error" className="text-sm text-destructive">{errors.firstName}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    type="text"
                    placeholder="Doe"
                    value={formData.lastName}
                    onChange={handleInputChange("lastName")}
                    className={`glass border-white/20 ${errors.lastName ? 'border-destructive' : ''}`}
                    disabled={isLoading}
                  />
                  {errors.lastName && (
                    <p id="lastName-error" className="text-sm text-destructive">{errors.lastName}</p>
                  )}
                </div>
              </div>

              <div id="email-field" className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="john@example.com"
                  value={formData.email}
                  onChange={handleInputChange("email")}
                  className={`glass border-white/20 ${errors.email ? 'border-destructive' : ''}`}
                  disabled={isLoading}
                />
                {errors.email && (
                  <p id="email-error" className="text-sm text-destructive">{errors.email}</p>
                )}
              </div>

              <div id="password-field" className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={handleInputChange("password")}
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
                {formData.password && (
                  <PasswordStrengthIndicator checks={passwordStrength.checks} score={passwordStrength.score} />
                )}
                {errors.password && (
                  <p id="password-error" className="text-sm text-destructive">{errors.password}</p>
                )}
              </div>

              <div id="confirm-password-field" className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange("confirmPassword")}
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

              <div id="terms-field" className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="terms"
                    checked={acceptTerms}
                    onCheckedChange={setAcceptTerms}
                    disabled={isLoading}
                  />
                  <Label htmlFor="terms" className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    I accept the{" "}
                    <Link to="/terms" className="text-primary hover:text-primary/80 underline">
                      Terms of Service
                    </Link>{" "}
                    and{" "}
                    <Link to="/privacy" className="text-primary hover:text-primary/80 underline">
                      Privacy Policy
                    </Link>
                  </Label>
                </div>
                {errors.terms && (
                  <p id="terms-error" className="text-sm text-destructive">{errors.terms}</p>
                )}
              </div>
            </CardContent>

            <CardFooter id="register-footer" className="flex flex-col space-y-4">
              <Button
                id="register-submit-button"
                type="submit"
                className="w-full bg-gradient-to-r from-primary to-primary-hover hover:shadow-glow"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Account...
                  </>
                ) : (
                  "Create Account"
                )}
              </Button>

              <div id="login-link" className="text-center text-sm">
                <span className="text-muted-foreground">Already have an account? </span>
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

export default RegisterPage;