# AI Financial Planning Frontend

A comprehensive React/Next.js frontend application for the AI-driven financial planning system. This application provides users with an intuitive multi-step interface to input their financial information and receive personalized retirement planning recommendations through Monte Carlo simulations.

## 🚀 Features

### Multi-Step Intake Form
- **Personal Information**: Age, retirement goals, marital status, location
- **Financial Snapshot**: Income, expenses, savings, debt analysis
- **Account Buckets**: 401(k), IRA, HSA, and taxable account management
- **Risk Assessment**: Investment risk tolerance and experience evaluation  
- **Retirement Goals**: Income needs, inflation assumptions, major expenses

### Results Dashboard
- **Probability Analysis**: Monte Carlo simulation results with success probability
- **Interactive Visualizations**: Portfolio projections and allocation charts
- **Trade-off Scenarios**: Compare different saving/retirement strategies
- **AI Narrative**: Personalized recommendations and insights
- **PDF Export**: Professional financial plan reports

### Technical Features
- **Form Validation**: Comprehensive validation with React Hook Form + Zod
- **State Management**: Zustand for efficient state handling
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Accessibility**: WCAG 2.1 AA compliance
- **TypeScript**: Full type safety throughout the application
- **Real-time Calculations**: Dynamic updates as users input data

## 🛠️ Technology Stack

- **Framework**: Next.js 14 with App Router
- **React**: 18.2+ with Hooks and Context
- **TypeScript**: Full type safety and IntelliSense
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for global state
- **Form Handling**: React Hook Form with Zod validation
- **Charts**: Recharts for data visualization
- **UI Components**: Radix UI primitives with custom styling
- **PDF Generation**: jsPDF with html2canvas for reports
- **Icons**: Lucide React icon library
- **API Integration**: Axios with TypeScript interfaces

## 📦 Project Structure

```
frontend/src/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles and CSS variables
│   ├── layout.tsx         # Root layout component
│   └── page.tsx           # Main application page
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   │   ├── button.tsx    # Button with variants and loading states
│   │   ├── input.tsx     # Input with validation and accessibility
│   │   ├── card.tsx      # Card layout components
│   │   ├── progress.tsx  # Progress indicators with steps
│   │   └── select.tsx    # Dropdown select with search
│   ├── forms/            # Form step components
│   │   ├── FormWizard.tsx          # Main form orchestrator
│   │   ├── PersonalInfoForm.tsx    # Step 1: Personal details
│   │   ├── FinancialSnapshotForm.tsx # Step 2: Current finances
│   │   ├── AccountBucketsForm.tsx   # Step 3: Investment accounts
│   │   ├── RiskPreferenceForm.tsx   # Step 4: Risk assessment
│   │   ├── RetirementGoalsForm.tsx  # Step 5: Future goals
│   │   └── FormReview.tsx          # Step 6: Review and submit
│   ├── charts/           # Data visualization components
│   │   ├── ProbabilityChart.tsx      # Monte Carlo results
│   │   ├── PortfolioAllocationChart.tsx # Asset allocation
│   │   └── TradeOffChart.tsx         # Scenario comparisons
│   └── ResultsDashboard.tsx # Main results display
├── store/                # State management
│   └── financialPlanningStore.ts # Zustand store
├── lib/                  # Utility libraries
│   ├── utils.ts          # General utilities and helpers
│   ├── validationSchemas.ts # Zod validation schemas
│   ├── api.ts           # API integration and error handling
│   ├── pdfExport.ts     # PDF generation utilities
│   └── accessibility.ts # Accessibility helpers
└── types/               # TypeScript type definitions
    ├── financial.ts     # Financial planning types
    └── index.ts         # Type re-exports
```

## 🚦 Getting Started

### Prerequisites
- Node.js 18.0 or higher
- npm 8.0 or higher

### Installation
1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Environment Variables
Create a `.env.local` file in the frontend directory:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NODE_ENV=development
```

## 🎨 Design System

### Color Palette
- **Primary**: Blue (#3b82f6) for actions and focus states
- **Success**: Green (#10b981) for positive outcomes
- **Warning**: Amber (#f59e0b) for moderate risk
- **Danger**: Red (#ef4444) for high risk or errors
- **Neutral**: Gray scale for text and backgrounds

### Typography
- **Headings**: Inter font family, various weights
- **Body**: Inter regular (400) and medium (500)
- **Code**: JetBrains Mono for monospace elements

### Spacing
- Consistent 4px base unit scale
- Responsive spacing with Tailwind utilities
- Container max-widths: sm (640px), md (768px), lg (1024px), xl (1280px)

## 📱 Responsive Design

The application follows a mobile-first approach:

- **Mobile** (320px+): Single column layout, stacked forms
- **Tablet** (768px+): Two-column forms, larger touch targets  
- **Desktop** (1024px+): Multi-column layouts, sidebar navigation
- **Large screens** (1280px+): Optimized spacing and typography

### Breakpoint Strategy
```css
sm: 640px   /* Small devices */
md: 768px   /* Medium devices */ 
lg: 1024px  /* Large devices */
xl: 1280px  /* Extra large devices */
2xl: 1536px /* 2X large devices */
```

## ♿ Accessibility Features

### WCAG 2.1 AA Compliance
- **Color Contrast**: 4.5:1 ratio for normal text, 3:1 for large text
- **Keyboard Navigation**: Full keyboard support for all interactions
- **Screen Reader Support**: ARIA labels, landmarks, and live regions
- **Focus Management**: Visible focus indicators and logical tab order
- **Semantic HTML**: Proper heading hierarchy and landmark roles

### Form Accessibility
- Error messages linked with `aria-describedby`
- Required fields marked with `aria-required`
- Fieldset and legend for grouped controls
- Progress announcement for multi-step forms
- Validation feedback with screen reader support

### Interactive Elements
- Minimum 44px touch targets
- High contrast focus indicators
- Keyboard shortcuts for common actions
- Error prevention and clear recovery paths

## 🔧 Development Features

### Form Validation
Each form step includes comprehensive validation:
```typescript
// Example: Personal Info validation
const personalInfoSchema = z.object({
  age: z.number().min(18).max(100),
  retirementAge: z.number().min(50).max(90),
  maritalStatus: z.enum(['single', 'married', 'divorced', 'widowed']),
  // ... additional fields
}).refine((data) => data.retirementAge > data.age, {
  message: "Retirement age must be greater than current age",
  path: ["retirementAge"],
});
```

### State Management
Zustand provides efficient state management:
```typescript
// Centralized store with persistence
const useFinancialPlanningStore = create(
  persist(
    (set, get) => ({
      formData: initialFormData,
      currentStep: 'personal-info',
      setPersonalInfo: (data) => set((state) => ({
        formData: { ...state.formData, personalInfo: data }
      })),
      // ... additional actions
    }),
    { name: 'financial-planning-storage' }
  )
);
```

### API Integration
Type-safe API calls with error handling:
```typescript
// API response wrapper
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: APIError;
}

// Usage
const response = await financialPlanningAPI.runSimulation(formData);
if (response.success) {
  setResults(response.data);
} else {
  handleError(response.error);
}
```

## 📊 Data Visualization

### Chart Components
- **Probability Chart**: Monte Carlo simulation results with confidence intervals
- **Portfolio Allocation**: Pie chart with detailed breakdown
- **Trade-off Scenarios**: Bar chart comparing different strategies

### Chart Features
- Responsive design with proper scaling
- Accessible color schemes and patterns
- Interactive tooltips with detailed information
- Export capabilities for reports

## 📄 PDF Export

The application generates comprehensive PDF reports including:
- Executive summary with key metrics
- Input data summary for verification
- Detailed simulation results
- Portfolio allocation recommendations
- Trade-off scenario analysis
- AI-generated narrative and insights
- Important disclaimers and assumptions

## 🧪 Testing Strategy

### Form Testing
- Validation rule testing for all input fields
- User flow testing through multi-step wizard
- Error state testing and recovery paths
- Cross-browser compatibility testing

### Accessibility Testing
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Keyboard navigation testing
- Color contrast validation
- WAVE accessibility evaluation

### Performance Testing
- Bundle size optimization
- Loading state management
- Chart rendering performance
- Mobile device testing

## 🚀 Deployment

### Build Process
```bash
# Type checking
npm run type-check

# Linting and formatting
npm run lint
npm run format

# Production build
npm run build

# Start production server
npm start
```

### Optimization Features
- Code splitting with dynamic imports
- Image optimization with Next.js Image
- CSS optimization and purging
- Bundle analysis with webpack-bundle-analyzer

## 🔒 Security Considerations

- Input validation and sanitization
- XSS prevention with proper escaping
- HTTPS enforcement in production
- Environment variable protection
- Secure API communication

## 📈 Performance Metrics

- **First Contentful Paint**: < 2s
- **Time to Interactive**: < 3s
- **Cumulative Layout Shift**: < 0.1
- **Bundle Size**: < 500KB gzipped

## 🤝 Contributing

1. Follow the established TypeScript patterns
2. Maintain accessibility standards
3. Add appropriate error handling
4. Include responsive design considerations
5. Update documentation for new features

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Hook Form](https://react-hook-form.com/)
- [Zod Validation](https://zod.dev/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

This frontend application provides a comprehensive, accessible, and user-friendly interface for the AI Financial Planning system, combining modern web development practices with financial planning expertise.