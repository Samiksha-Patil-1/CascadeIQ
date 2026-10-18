import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CascadeIQ - Predict the Blast Radius of Failure",
  description: "Quantitative risk modeling, failure cascading, and mitigation optimization.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0B0F17] text-[#E5E7EB] antialiased">
        {children}
      </body>
    </html>
  );
}
