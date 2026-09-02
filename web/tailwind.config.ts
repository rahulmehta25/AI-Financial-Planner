import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#241f19",
        "ink-soft": "#4a453d",
        paper: "#f7f3ec",
        sand: "#efe8dc",
        accent: "#4a6756",
        "accent-hover": "#3d5648",
        muted: "#7a7368",
        line: "#e2d9cc",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
    },
  },
  plugins: [],
};

export default config;
