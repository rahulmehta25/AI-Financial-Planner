import type { Metadata } from "next";
import { IBM_Plex_Sans, Outfit, Source_Serif_4 } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { PostHogProvider } from "./components/PostHogProvider";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
  style: ["normal", "italic"],
});

const ibmPlex = IBM_Plex_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-num",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "AI Financial Planner",
  description:
    "A calm planning studio. Claude grounded on real accounts, with honest Monte Carlo ranges.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${outfit.variable} ${sourceSerif.variable} ${ibmPlex.variable}`}>
      <body className="font-sans">
        {children}
        <Analytics />
        <SpeedInsights />
        <PostHogProvider />
      </body>
    </html>
  );
}
