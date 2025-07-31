import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Text, Spinner } from '@radix-ui/themes';
import api from '../api';

const OracleAuthCallback = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('Connecting your account...');

  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (error) {
        console.error('OAuth error:', error);
        setStatus('Authentication cancelled');
        setTimeout(() => {
          navigate('/oracle', { state: { error: 'Authentication was cancelled or failed' } });
        }, 1000);
        return;
      }

      if (code && state) {
        try {
          const response = await api.get(`/oracle/auth/callback?code=${code}&state=${state}`);
          // Check for various success indicators
          if (response.data.status === 'success' || 
              response.data.message?.includes('Successfully') ||
              response.status === 200) {
            setStatus('Successfully connected! Redirecting...');
            // Add a small delay to show success message
            setTimeout(() => {
              navigate('/oracle', { state: { message: 'Successfully connected!' } });
            }, 1000);
          } else {
            setStatus('Connection failed');
            setTimeout(() => {
              navigate('/oracle', { state: { error: 'Failed to connect' } });
            }, 1500);
          }
        } catch (error: any) {
          console.error('OAuth callback error:', error);
          // Only show error if it's actually an error response
          if (error.response?.status >= 400) {
            setStatus('Connection failed');
            setTimeout(() => {
              navigate('/oracle', { state: { error: 'Failed to connect. Please try again.' } });
            }, 1500);
          } else {
            // Assume success if we can't determine the status
            setStatus('Finalizing connection...');
            setTimeout(() => {
              navigate('/oracle', { state: { message: 'Connection completed!' } });
            }, 1000);
          }
        }
      } else {
        setStatus('Invalid response');
        setTimeout(() => {
          navigate('/oracle', { state: { error: 'Invalid authentication response' } });
        }, 1500);
      }
    };

    handleCallback();
  }, [navigate]);

  return (
    <Box style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100vh',
      gap: '1rem'
    }}>
      <Spinner size="3" />
      <Text size="3">{status}</Text>
    </Box>
  );
};

export default OracleAuthCallback; 