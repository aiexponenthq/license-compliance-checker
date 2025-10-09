'use client';

import { ReactNode } from 'react';
import { Theme, ThemePanel } from '@radix-ui/themes';
import { QueryClientProvider } from '@tanstack/react-query';
import { getQueryClient } from '../lib/queryClient';
import { AuthProvider } from '../lib/auth';

export function Providers({ children }: { children: ReactNode }) {
  const queryClient = getQueryClient();
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <Theme appearance="light" accentColor="blue">
          {children}
          {process.env.NODE_ENV === 'development' ? <ThemePanel defaultOpen={false} /> : null}
        </Theme>
      </QueryClientProvider>
    </AuthProvider>
  );
}
