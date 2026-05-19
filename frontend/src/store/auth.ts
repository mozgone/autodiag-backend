import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types';

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        localStorage.setItem('sellex_token', token);
        set({ token, user });
      },
      logout: () => {
        localStorage.removeItem('sellex_token');
        set({ token: null, user: null });
      },
      isAuthenticated: () => !!get().token,
    }),
    { name: 'sellex-auth', partialize: (s) => ({ token: s.token, user: s.user }) }
  )
);
