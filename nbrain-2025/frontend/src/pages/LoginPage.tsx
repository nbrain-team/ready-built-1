import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button, Card, Flex, Heading, Text, TextField, Box } from '@radix-ui/themes';
import api from '../api';
import { InfoCircledIcon } from '@radix-ui/react-icons';
import { Callout } from '@radix-ui/themes';

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        
        // Retry logic for connection issues
        let retries = 3;
        while (retries > 0) {
            try {
                const params = new URLSearchParams();
                params.append('username', email);
                params.append('password', password);

                const response = await api.post('/login', params, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    timeout: 10000 // 10 second timeout
                });

                if (response.data.access_token) {
                    localStorage.setItem('token', response.data.access_token);
                    login(response.data.access_token);
                    navigate('/start');
                    return;
                }
                break;
            } catch (err: any) {
                if (err.response?.status === 503 || err.code === 'ECONNABORTED') {
                    // Service unavailable or timeout - retry
                    retries--;
                    if (retries === 0) {
                        setError('Server is temporarily unavailable. Please try again in a moment.');
                    } else {
                        // Wait a bit before retrying
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        continue;
                    }
                } else {
                    setError(err.response?.data?.detail || 'Failed to login. Please check your credentials.');
                    break;
                }
            }
        }
        setIsLoading(false);
    };

    return (
        <Flex direction="column" align="center" justify="center" style={{ minHeight: '100vh', background: 'white' }}>
            {/* Logo */}
            <Box mb="4" style={{ paddingTop: '50px', paddingBottom: '50px' }}>
                <img 
                    src="/new-icons/nbrain-logo.png" 
                    alt="nBrain Logo" 
                    style={{ height: '50px', objectFit: 'contain' }} 
                />
            </Box>

            <Card size="4" style={{ width: '400px', border: '1px solid #e5e5e5', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)', background: 'white' }}>
                <Flex direction="column" gap="4">
                    <Box>
                        <Heading align="center" size="7" mb="2">Welcome to nBrain</Heading>
                        <Text align="center" size="3" color="gray">
                            Turn scattered data into clear insights
                        </Text>
                    </Box>
                    
                    {error && <Callout.Root color="red" role="alert"><Callout.Icon><InfoCircledIcon /></Callout.Icon><Callout.Text>{error}</Callout.Text></Callout.Root>}
                    
                    <form onSubmit={handleSubmit}>
                        <Flex direction="column" gap="3">
                            <TextField.Root
                                placeholder="Email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                size="3"
                                style={{ background: 'white' }}
                            />
                            <TextField.Root
                                placeholder="Password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                size="3"
                                style={{ background: 'white' }}
                            />
                            <Button type="submit" size="3" disabled={isLoading}>
                                {isLoading ? 'Logging In...' : 'Log In'}
                            </Button>
                        </Flex>
                    </form>
                    
                    <Flex mt="2" justify="center">
                        <Text size="2" color="gray">
                            Don't have an account? <Link to="/signup" style={{ color: 'var(--accent-9)' }}>Sign up</Link>
                        </Text>
                    </Flex>
                </Flex>
            </Card>

            {/* Footer */}
            <Box as="div" role="contentinfo" style={{ marginTop: 'auto', paddingTop: '2rem', textAlign: 'center' }}>
                <Text as="p" size="2" color="gray">© {new Date().getFullYear()} nBrain. All Rights Reserved.</Text>
            </Box>
        </Flex>
    );
};

export default LoginPage;