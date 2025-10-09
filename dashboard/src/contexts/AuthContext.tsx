// Copyright 2025 Ajay Pundhir
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface User {
  username: string;
  email: string | null;
  full_name: string | null;
  role: string;
  disabled: boolean;
  must_change_password?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Fetch user profile
  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      // Token might be invalid, clear it
      localStorage.removeItem('token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // Login function
  const login = async (token: string) => {
    localStorage.setItem('token', token);
    await fetchUserProfile();
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    router.push('/login');
  };

  // Check authentication on mount
  useEffect(() => {
    fetchUserProfile();
  }, []);

  // Redirect logic
  useEffect(() => {
    if (!loading) {
      const currentPath = window.location.pathname;

      if (!user) {
        // Not authenticated
        const publicPaths = ['/login'];
        if (!publicPaths.includes(currentPath)) {
          router.push('/login');
        }
      } else {
        // Authenticated
        if (user.must_change_password && currentPath !== '/change-password') {
          router.push('/change-password');
        } else if (!user.must_change_password && currentPath === '/change-password') {
          // If password change not required, don't stay on change-password page unless explicitly navigating there?
          // Actually, users might want to change password voluntarily. 
          // But for now, let's just ensure they ARE redirected if they MUST change it.
          // We won't force them OUT of change-password if they don't have to.
        }
      }
    }
  }, [loading, user, router]);

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
