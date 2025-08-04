import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface HomePageProps {
  messages: any[];
  setMessages: React.Dispatch<React.SetStateAction<any[]>>;
}

const HomePage: React.FC<HomePageProps> = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to salon dashboard as the main page
    navigate('/salon');
  }, [navigate]);

  return null;
};

export default HomePage; 