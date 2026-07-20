import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Cascadia Code", "monospace"],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          hover: "hsl(var(--primary-hover))",
          glow: "hsl(var(--primary-glow))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
          light: "hsl(var(--success-light))",
          glow: "hsl(var(--success-glow))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
          light: "hsl(var(--warning-light))",
        },
        error: {
          DEFAULT: "hsl(var(--error))",
          foreground: "hsl(var(--error-foreground))",
          light: "hsl(var(--error-light))",
        },
        gold: {
          DEFAULT: "hsl(43 96% 54%)",
          light: "hsl(43 96% 70%)",
          dark: "hsl(38 92% 42%)",
        },
        navy: {
          50: "hsl(220 40% 95%)",
          100: "hsl(220 38% 88%)",
          200: "hsl(220 35% 75%)",
          300: "hsl(220 32% 60%)",
          400: "hsl(220 35% 45%)",
          500: "hsl(220 38% 30%)",
          600: "hsl(220 40% 20%)",
          700: "hsl(220 42% 14%)",
          800: "hsl(220 44% 10%)",
          850: "hsl(220 45% 8%)",
          900: "hsl(222 47% 6%)",
          950: "hsl(222 47% 4%)",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 8px)",
        "3xl": "calc(var(--radius) + 16px)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "gradient-primary": "linear-gradient(135deg, hsl(214 100% 50%) 0%, hsl(214 100% 65%) 100%)",
        "gradient-success": "linear-gradient(135deg, hsl(152 69% 35%) 0%, hsl(152 69% 50%) 100%)",
        "gradient-gold": "linear-gradient(135deg, hsl(38 92% 42%) 0%, hsl(43 96% 60%) 100%)",
        "gradient-card": "linear-gradient(145deg, hsl(220 40% 9% / 0.9) 0%, hsl(220 38% 7% / 0.8) 100%)",
        "gradient-hero": "linear-gradient(135deg, hsl(222 47% 5%) 0%, hsl(220 40% 10%) 50%, hsl(222 47% 5%) 100%)",
        "gradient-sidebar": "linear-gradient(180deg, hsl(222 50% 6%) 0%, hsl(220 45% 8%) 100%)",
      },
      boxShadow: {
        "glow-blue": "0 0 30px hsl(214 100% 57% / 0.25)",
        "glow-green": "0 0 30px hsl(152 69% 40% / 0.25)",
        "glow-gold": "0 0 30px hsl(43 96% 54% / 0.25)",
        "card-raised": "0 20px 40px -8px hsl(222 47% 2% / 0.6), 0 8px 16px -4px hsl(222 47% 2% / 0.4)",
        premium: "0 0 0 1px hsl(220 30% 18% / 0.6), 0 8px 32px hsl(222 47% 2% / 0.5), inset 0 1px 0 hsl(220 50% 60% / 0.06)",
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        float: "float 6s ease-in-out infinite",
        "pulse-glow": "pulse-glow 2.5s ease-in-out infinite",
        shimmer: "shimmer 1.8s ease-in-out infinite",
        "slide-in-bottom": "slideInFromBottom 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards",
        "slide-in-right": "slideInFromRight 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards",
        "slide-in-left": "slideInFromLeft 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards",
        "scale-in": "scaleIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards",
        "fade-in": "fadeIn 0.4s ease-out forwards",
        "count-up": "countUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards",
        "typing-bounce": "typingBounce 1.4s ease-in-out infinite",
        "pulse-dot": "pulse-dot 2.5s ease-in-out infinite",
        "page-enter": "pageEnter 0.35s cubic-bezier(0.4, 0, 0.2, 1) forwards",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px) rotate(0deg)", opacity: "0.6" },
          "50%": { transform: "translateY(-18px) rotate(180deg)", opacity: "0.9" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 20px hsl(214 100% 57% / 0.3)" },
          "50%": { boxShadow: "0 0 45px hsl(214 100% 57% / 0.6), 0 0 80px hsl(214 100% 57% / 0.15)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        slideInFromBottom: {
          from: { opacity: "0", transform: "translateY(24px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        slideInFromRight: {
          from: { opacity: "0", transform: "translateX(24px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        slideInFromLeft: {
          from: { opacity: "0", transform: "translateX(-24px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          from: { opacity: "0", transform: "scale(0.92)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        countUp: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        typingBounce: {
          "0%, 60%, 100%": { transform: "translateY(0)", opacity: "0.5" },
          "30%": { transform: "translateY(-8px)", opacity: "1" },
        },
        "pulse-dot": {
          "0%, 100%": { transform: "scale(1)", opacity: "1" },
          "50%": { transform: "scale(1.3)", opacity: "0.7" },
        },
        pageEnter: {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
        "72": "18rem",
        "80": "20rem",
        "88": "22rem",
        "96": "24rem",
        "sidebar": "260px",
      },
      transitionTimingFunction: {
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
