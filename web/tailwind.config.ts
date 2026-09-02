import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1b1915",
        "ink-soft": "#3f3a33",
        paper: "#f4f0e7",
        "paper-deep": "#ebe4d6",
        card: "#fffcf7",
        accent: "#3f5c4b",
        "accent-hover": "#334a3d",
        sage: "#8fa392",
        "sage-wash": "#e4ebe4",
        muted: "#6f675c",
        line: "#e4ddd0",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
        num: ["var(--font-num)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 1px rgba(27, 25, 21, 0.04), 0 12px 32px rgba(27, 25, 21, 0.05)",
        lift: "0 1px 1px rgba(27, 25, 21, 0.04), 0 18px 40px rgba(27, 25, 21, 0.08)",
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
    },
  },
  plugins: [],
};

export default config;
