import {VALIDATION_CONFIG} from './config';

// Email validation
export const validateEmail = (email: string): string | null => {
  if (!email) {
    return 'Email is required';
  }
  
  if (!VALIDATION_CONFIG.EMAIL_REGEX.test(email)) {
    return 'Please enter a valid email address';
  }
  
  return null;
};

// Password validation
export const validatePassword = (password: string): string | null => {
  if (!password) {
    return 'Password is required';
  }
  
  if (password.length < VALIDATION_CONFIG.PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${VALIDATION_CONFIG.PASSWORD_MIN_LENGTH} characters`;
  }
  
  if (!VALIDATION_CONFIG.PASSWORD_REGEX.test(password)) {
    return 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character';
  }
  
  return null;
};

// Confirm password validation
export const validateConfirmPassword = (password: string, confirmPassword: string): string | null => {
  if (!confirmPassword) {
    return 'Please confirm your password';
  }
  
  if (password !== confirmPassword) {
    return 'Passwords do not match';
  }
  
  return null;
};

// Name validation
export const validateName = (name: string, fieldName: string = 'Name'): string | null => {
  if (!name) {
    return `${fieldName} is required`;
  }
  
  if (name.length < VALIDATION_CONFIG.NAME_MIN_LENGTH) {
    return `${fieldName} must be at least ${VALIDATION_CONFIG.NAME_MIN_LENGTH} characters`;
  }
  
  if (name.length > VALIDATION_CONFIG.NAME_MAX_LENGTH) {
    return `${fieldName} must be no more than ${VALIDATION_CONFIG.NAME_MAX_LENGTH} characters`;
  }
  
  return null;
};

// Phone validation
export const validatePhone = (phone: string): string | null => {
  if (!phone) {
    return null; // Phone is optional
  }
  
  if (!VALIDATION_CONFIG.PHONE_REGEX.test(phone)) {
    return 'Please enter a valid phone number';
  }
  
  return null;
};

// Age validation
export const validateAge = (age: number | string): string | null => {
  const ageNum = typeof age === 'string' ? parseInt(age, 10) : age;
  
  if (!ageNum || isNaN(ageNum)) {
    return 'Age is required';
  }
  
  if (ageNum < 18) {
    return 'You must be at least 18 years old';
  }
  
  if (ageNum > 100) {
    return 'Please enter a valid age';
  }
  
  return null;
};

// Retirement age validation
export const validateRetirementAge = (retirementAge: number | string, currentAge: number | string): string | null => {
  const retirementAgeNum = typeof retirementAge === 'string' ? parseInt(retirementAge, 10) : retirementAge;
  const currentAgeNum = typeof currentAge === 'string' ? parseInt(currentAge, 10) : currentAge;
  
  if (!retirementAgeNum || isNaN(retirementAgeNum)) {
    return 'Retirement age is required';
  }
  
  if (retirementAgeNum <= currentAgeNum) {
    return 'Retirement age must be greater than current age';
  }
  
  if (retirementAgeNum > 100) {
    return 'Please enter a realistic retirement age';
  }
  
  return null;
};

// Currency amount validation
export const validateAmount = (amount: number | string, fieldName: string = 'Amount', isRequired: boolean = true): string | null => {
  const amountNum = typeof amount === 'string' ? parseFloat(amount) : amount;
  
  if (!amountNum && amountNum !== 0) {
    return isRequired ? `${fieldName} is required` : null;
  }
  
  if (isNaN(amountNum)) {
    return `Please enter a valid ${fieldName.toLowerCase()}`;
  }
  
  if (amountNum < 0) {
    return `${fieldName} cannot be negative`;
  }
  
  if (amountNum > 999999999) {
    return `${fieldName} is too large`;
  }
  
  return null;
};

// Goal target amount validation
export const validateGoalAmount = (targetAmount: number | string, currentAmount: number | string = 0): string | null => {
  const targetNum = typeof targetAmount === 'string' ? parseFloat(targetAmount) : targetAmount;
  const currentNum = typeof currentAmount === 'string' ? parseFloat(currentAmount) : currentAmount;
  
  const amountError = validateAmount(targetAmount, 'Target amount');
  if (amountError) {
    return amountError;
  }
  
  if (targetNum <= currentNum) {
    return 'Target amount must be greater than current amount';
  }
  
  return null;
};

// Date validation
export const validateDate = (date: string | Date, fieldName: string = 'Date'): string | null => {
  if (!date) {
    return `${fieldName} is required`;
  }
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return `Please enter a valid ${fieldName.toLowerCase()}`;
  }
  
  return null;
};

// Future date validation
export const validateFutureDate = (date: string | Date, fieldName: string = 'Date'): string | null => {
  const dateError = validateDate(date, fieldName);
  if (dateError) {
    return dateError;
  }
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  if (dateObj <= today) {
    return `${fieldName} must be in the future`;
  }
  
  return null;
};

// Required field validation
export const validateRequired = (value: any, fieldName: string): string | null => {
  if (value === null || value === undefined || value === '') {
    return `${fieldName} is required`;
  }
  
  if (typeof value === 'string' && value.trim() === '') {
    return `${fieldName} is required`;
  }
  
  return null;
};

// Risk tolerance validation
export const validateRiskTolerance = (riskTolerance: string): string | null => {
  const validOptions = ['conservative', 'moderate', 'aggressive'];
  
  if (!riskTolerance) {
    return 'Risk tolerance is required';
  }
  
  if (!validOptions.includes(riskTolerance)) {
    return 'Please select a valid risk tolerance';
  }
  
  return null;
};

// Goal priority validation
export const validateGoalPriority = (priority: string): string | null => {
  const validPriorities = ['low', 'medium', 'high'];
  
  if (!priority) {
    return 'Goal priority is required';
  }
  
  if (!validPriorities.includes(priority)) {
    return 'Please select a valid priority';
  }
  
  return null;
};

// Goal category validation
export const validateGoalCategory = (category: string): string | null => {
  const validCategories = [
    'retirement',
    'emergency_fund',
    'house',
    'education',
    'vacation',
    'debt_payoff',
    'other'
  ];
  
  if (!category) {
    return 'Goal category is required';
  }
  
  if (!validCategories.includes(category)) {
    return 'Please select a valid category';
  }
  
  return null;
};

// Comprehensive form validation
export const validateFormField = (
  value: any,
  fieldType: string,
  fieldName: string,
  options?: any
): string | null => {
  switch (fieldType) {
    case 'email':
      return validateEmail(value);
    case 'password':
      return validatePassword(value);
    case 'confirmPassword':
      return validateConfirmPassword(options?.password || '', value);
    case 'name':
      return validateName(value, fieldName);
    case 'phone':
      return validatePhone(value);
    case 'age':
      return validateAge(value);
    case 'retirementAge':
      return validateRetirementAge(value, options?.currentAge || 0);
    case 'amount':
      return validateAmount(value, fieldName, options?.required !== false);
    case 'goalAmount':
      return validateGoalAmount(value, options?.currentAmount);
    case 'date':
      return validateDate(value, fieldName);
    case 'futureDate':
      return validateFutureDate(value, fieldName);
    case 'required':
      return validateRequired(value, fieldName);
    case 'riskTolerance':
      return validateRiskTolerance(value);
    case 'goalPriority':
      return validateGoalPriority(value);
    case 'goalCategory':
      return validateGoalCategory(value);
    default:
      return null;
  }
};

export default {
  validateEmail,
  validatePassword,
  validateConfirmPassword,
  validateName,
  validatePhone,
  validateAge,
  validateRetirementAge,
  validateAmount,
  validateGoalAmount,
  validateDate,
  validateFutureDate,
  validateRequired,
  validateRiskTolerance,
  validateGoalPriority,
  validateGoalCategory,
  validateFormField,
};