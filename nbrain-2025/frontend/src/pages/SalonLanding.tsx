import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

const SalonLanding: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if already authenticated
    const salonAuth = sessionStorage.getItem('salonAuth');
    if (salonAuth === 'true') {
      navigate('/salon');
    } else {
      navigate('/salon-login');
    }
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
      <div className="text-center">
        <Sparkles className="h-12 w-12 text-purple-600 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Redirecting to Salon Dashboard...</p>
      </div>
    </div>
  );
};

export default SalonLanding; 