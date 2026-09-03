import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KisanSetu AI — Smart Farming Platform",
  description:
    "AI-powered cotton and groundnut market linkage platform for Gujarat farmers. Powered by IBM Granite.",
  keywords: ["farmer", "cotton", "groundnut", "mandi prices", "Gujarat", "AI", "IBM Granite"],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
