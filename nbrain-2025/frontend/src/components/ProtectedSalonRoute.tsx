import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

interface ProtectedSalonRouteProps {
  children: React.ReactNode;
}

const ProtectedSalonRoute: React.FC<ProtectedSalonRouteProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    // Check if user is authenticated for salon
    const salonAuth = sessionStorage.getItem('salonAuth');
    setIsAuthenticated(salonAuth === 'true');
  }, []);

  // Show loading state while checking auth
  if (isAuthenticated === null) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/salon-login" replace />;
  }

  // Render children if authenticated
  return <>{children}</>;
};

export default ProtectedSalonRoute; 