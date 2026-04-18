import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1220",
        paper: "#f8fafc",
        accent: "#4f46e5",
        muted: "#64748b",
      },
    },
  },
  plugins: [],
};

export default config;
