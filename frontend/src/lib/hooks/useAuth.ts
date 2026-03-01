'use client';

import { useContext } from 'react';
import { AuthContext } from '@/components/providers/AuthProvider';

/**
 * Custom hook to access auth context
 * Must be used within AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
