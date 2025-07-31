import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button, Card, Flex, Heading, Text, TextField, Callout, Box } from '@radix-ui/themes';
import api from '../api';
import { InfoCircledIcon, CheckCircledIcon } from '@radix-ui/react-icons';

const SignupPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            const response = await api.post('/signup', { email, password });
            if (response.data.access_token) {
                login(response.data.access_token);
                navigate('/start');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to sign up. Please try again.');
        }
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
                        <Heading align="center" size="7" mb="2">Create nBrain Account</Heading>
                        <Text align="center" size="3" color="gray">
                            Start turning data into insights today
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
                            <Button type="submit" size="3">Sign Up</Button>
                        </Flex>
                    </form>
                    
                    <Flex mt="2" justify="center">
                        <Text size="2" color="gray">
                            Already have an account? <Link to="/login" style={{ color: 'var(--accent-9)' }}>Log in</Link>
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

export default SignupPage;