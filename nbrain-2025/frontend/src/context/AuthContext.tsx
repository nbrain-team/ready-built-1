import { createContext, useState, useContext, useEffect, type ReactNode } from 'react';
import api from '../api';

interface UserProfile {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  website_url?: string;
  role: string;
  permissions: Record<string, boolean>;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  userProfile: UserProfile | null;
  login: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
  refreshProfile: () => Promise<void>;
  hasPermission: (module: string) => boolean;
  isAdmin: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshProfile = async () => {
    if (token) {
      try {
        const response = await api.get('/user/profile');
        console.log('AuthContext - Profile fetched:', response.data);
        setUserProfile(response.data);
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
        // If profile fetch fails, user might be logged out
        if ((error as any)?.response?.status === 401) {
          logout();
        }
      }
    }
  };

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      refreshProfile();
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      refreshProfile();
    } else {
      setUserProfile(null);
      delete api.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const login = (newToken: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    // Add a small delay to ensure token is properly set
    setTimeout(() => {
      refreshProfile();
    }, 100);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUserProfile(null);
    delete api.defaults.headers.common['Authorization'];
    window.location.href = '/login';
  };

  const hasPermission = (module: string): boolean => {
    if (!userProfile) return false;
    if (userProfile.role === 'admin') return true;
    return userProfile.permissions[module] === true;
  };

  const isAdmin = (): boolean => {
    return userProfile?.role === 'admin';
  };

  return (
    <AuthContext.Provider value={{ 
      token, 
      isAuthenticated: !!token, 
      userProfile,
      login, 
      logout, 
      isLoading,
      refreshProfile,
      hasPermission,
      isAdmin
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 