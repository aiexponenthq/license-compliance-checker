'use client';

import { createContext, ReactNode, useContext, useMemo, useState } from 'react';

type User = {
  name: string;
  email: string;
};

type AuthContextValue = {
  user: User | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      signIn: async (email: string) => {
        // Placeholder for real auth API call
        setUser({ name: email.split('@')[0] || 'User', email });
      },
      signOut: () => setUser(null),
    }),
    [user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
