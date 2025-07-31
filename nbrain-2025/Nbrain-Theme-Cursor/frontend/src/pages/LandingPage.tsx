import { Box, Flex, Text, Heading, Card, Button } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';

const LandingPage = () => {
    const navigate = useNavigate();

    const modules = [
        {
            title: 'Ask Your Data',
            description: 'Engage with your documents.',
            icon: '/new-icons/chat.svg',
            path: '/chat',
        },
        {
            title: 'Generate Content',
            description: 'Create content from data.',
            icon: '/new-icons/generator.svg',
            path: '/generator',
        },
        {
            title: 'Manage Knowledge',
            description: 'Manage your documents.',
            icon: '/new-icons/kb.svg',
            path: '/documents',
        },
         {
            title: 'Login',
            description: 'Access your account.',
            icon: '/new-icons/login.svg',
            path: '/login',
        },
    ];

    return (
        <Flex direction="column" align="center" justify="center" style={{ minHeight: '100vh', padding: '2rem', background: 'var(--gray-1)' }}>
            <Card size="4" style={{ maxWidth: '600px', textAlign: 'center' }}>
                <Flex direction="column" align="center" gap="4">
                    <Heading size="8" weight="bold">Turn scattered data into clear insights.</Heading>
                    
                    <Text as="p" size="4" color="gray">
                        nBrain unifies your documents, data, and business knowledge into a single, secure AI platform. Ask questions, get answers, and make smarter decisions—in minutes.
                    </Text>

                    <Flex gap="3" mt="4" justify="center" wrap="wrap">
                         {modules.map(module => (
                             <Button 
                                 key={module.title} 
                                 className="module-card" 
                                 onClick={() => navigate(module.path)}
                                 variant="soft"
                                 size="3"
                             >
                                 <Flex direction="column" align="center" gap="2">
                                    <img src={module.icon} alt={`${module.title} icon`} style={{ width: '32px', height: '32px' }} />
                                    <Text size="2">{module.title}</Text>
                                 </Flex>
                             </Button>
                         ))}
                     </Flex>
                </Flex>
            </Card>

            <Box as="div" role="contentinfo" style={{ marginTop: '4rem', textAlign: 'center' }}>
                <Text as="p" size="2" color="gray">© {new Date().getFullYear()} nBrain. All Rights Reserved.</Text>
            </Box>

            <style>{`
                .module-card {
                    cursor: pointer;
                    min-width: 120px;
                }
            `}</style>
        </Flex>
    );
};

export default LandingPage; 