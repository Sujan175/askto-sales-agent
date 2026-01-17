import type { Metadata } from 'next';

import './globals.css';
import { Toaster } from '@/components/ui/sonner';

export const metadata: Metadata = {
  title: 'HDFC Sales Agent',
  description: 'Your AI-powered relationship manager for credit card conversations',
  icons: { icon: '/xcelerator-logo.png' },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Toaster theme='system' />
        {children}
      </body>
    </html>
  );
}
