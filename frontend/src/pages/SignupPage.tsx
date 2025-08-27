import React, { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Eye, EyeOff, Loader2, Check, X } from 'lucide-react'

const SignupPage: React.FC = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false
  })
  
  const { signup, isAuthenticated, isLoading, error, clearError } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Get return URL from location state
  const returnUrl = location.state?.returnUrl || '/dashboard'

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate(returnUrl, { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate, returnUrl])

  // Clear error when component mounts or form changes
  useEffect(() => {
    clearError()
  }, [clearError])

  // Validate password
  useEffect(() => {
    const password = formData.password
    setPasswordValidation({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    })

    if (Object.keys(formData).some(key => formData[key as keyof typeof formData] !== '')) {
      clearError()
    }
  }, [formData, clearError])

  const handleInputChange = (field: keyof typeof formData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!isFormValid) {
      return
    }

    setIsSubmitting(true)
    
    try {
      await signup({
        firstName: formData.firstName.trim(),
        lastName: formData.lastName.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password
      })
      // Navigation will be handled by useEffect above
    } catch (error) {
      // Error handling is done in the auth context
    } finally {
      setIsSubmitting(false)
    }
  }

  const isPasswordValid = Object.values(passwordValidation).every(Boolean)
  const doPasswordsMatch = formData.password !== '' && formData.password === formData.confirmPassword
  const isFormValid = 
    formData.firstName.trim() !== '' &&
    formData.lastName.trim() !== '' &&
    formData.email.trim() !== '' &&
    isPasswordValid &&
    doPasswordsMatch

  const isSubmitDisabled = !isFormValid || isSubmitting || isLoading

  const ValidationIcon: React.FC<{ isValid: boolean }> = ({ isValid }) => (
    isValid ? (
      <Check className="h-3 w-3 text-green-500" />
    ) : (
      <X className="h-3 w-3 text-gray-300" />
    )
  )

  return (
    <div id="signup-page" className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card id="signup-card" className="w-full max-w-md">
        <CardHeader id="signup-header" className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Create Account</CardTitle>
          <CardDescription className="text-center">
            Start your financial planning journey today
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent id="signup-content" className="space-y-4">
            {error && (
              <Alert id="signup-error" variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div id="name-fields" className="grid grid-cols-2 gap-3">
              <div id="first-name-field" className="space-y-2">
                <Label htmlFor="firstName">First Name</Label>
                <Input
                  id="firstName"
                  type="text"
                  placeholder="John"
                  value={formData.firstName}
                  onChange={handleInputChange('firstName')}
                  disabled={isSubmitting || isLoading}
                  required
                  autoComplete="given-name"
                />
              </div>
              
              <div id="last-name-field" className="space-y-2">
                <Label htmlFor="lastName">Last Name</Label>
                <Input
                  id="lastName"
                  type="text"
                  placeholder="Doe"
                  value={formData.lastName}
                  onChange={handleInputChange('lastName')}
                  disabled={isSubmitting || isLoading}
                  required
                  autoComplete="family-name"
                />
              </div>
            </div>
            
            <div id="email-field" className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="john@example.com"
                value={formData.email}
                onChange={handleInputChange('email')}
                disabled={isSubmitting || isLoading}
                required
                autoComplete="email"
              />
            </div>
            
            <div id="password-field" className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a secure password"
                  value={formData.password}
                  onChange={handleInputChange('password')}
                  disabled={isSubmitting || isLoading}
                  required
                  autoComplete="new-password"
                  className="pr-10"
                />
                <Button
                  id="password-toggle"
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isSubmitting || isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-500" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-500" />
                  )}
                </Button>
              </div>
              
              {formData.password && (
                <div id="password-requirements" className="text-xs space-y-1 mt-2">
                  <div className="flex items-center gap-2">
                    <ValidationIcon isValid={passwordValidation.length} />
                    <span className={passwordValidation.length ? 'text-green-600' : 'text-gray-500'}>
                      At least 8 characters
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ValidationIcon isValid={passwordValidation.uppercase} />
                    <span className={passwordValidation.uppercase ? 'text-green-600' : 'text-gray-500'}>
                      One uppercase letter
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ValidationIcon isValid={passwordValidation.lowercase} />
                    <span className={passwordValidation.lowercase ? 'text-green-600' : 'text-gray-500'}>
                      One lowercase letter
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ValidationIcon isValid={passwordValidation.number} />
                    <span className={passwordValidation.number ? 'text-green-600' : 'text-gray-500'}>
                      One number
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ValidationIcon isValid={passwordValidation.special} />
                    <span className={passwordValidation.special ? 'text-green-600' : 'text-gray-500'}>
                      One special character
                    </span>
                  </div>
                </div>
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
                  onChange={handleInputChange('confirmPassword')}
                  disabled={isSubmitting || isLoading}
                  required
                  autoComplete="new-password"
                  className="pr-10"
                />
                <Button
                  id="confirm-password-toggle"
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={isSubmitting || isLoading}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-500" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-500" />
                  )}
                </Button>
              </div>
              
              {formData.confirmPassword && (
                <div id="password-match-indicator" className="flex items-center gap-2 text-xs mt-1">
                  <ValidationIcon isValid={doPasswordsMatch} />
                  <span className={doPasswordsMatch ? 'text-green-600' : 'text-red-500'}>
                    {doPasswordsMatch ? 'Passwords match' : 'Passwords do not match'}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
          
          <CardFooter id="signup-footer" className="flex flex-col space-y-4">
            <Button
              id="signup-submit"
              type="submit"
              className="w-full"
              disabled={isSubmitDisabled}
            >
              {isSubmitting || isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </Button>
            
            <div id="signup-links" className="text-center space-y-2">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link 
                  to="/login" 
                  state={{ returnUrl }}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  Sign in
                </Link>
              </p>
              <Link 
                to="/"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Back to Home
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}

export default SignupPage