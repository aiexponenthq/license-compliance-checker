'use client';

import { QueryClient } from '@tanstack/react-query';

let client: QueryClient | undefined;

export function getQueryClient() {
  if (!client) {
    client = new QueryClient({
      defaultOptions: {
        queries: {
          refetchOnWindowFocus: false,
          staleTime: 60_000,
        },
      },
    });
  }
  return client;
}
