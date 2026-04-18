import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Financial Planner",
  description: "A grounded advisor that actually looks at your accounts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
