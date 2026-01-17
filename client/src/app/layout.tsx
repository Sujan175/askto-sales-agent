import type { Metadata } from 'next';

import './globals.css';
import { Toaster } from '@/components/ui/sonner';

export const metadata: Metadata = {
  title: 'askto - xcelerator',
  description: 'Your friendly digital interviewer who never sleeps, never judges, and definitely never forgets a question',
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
