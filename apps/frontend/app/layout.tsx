import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "CV Chat",
  description: "Grounded CV assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full min-h-0" suppressHydrationWarning>
      <body className="h-full min-h-0 overflow-hidden" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
