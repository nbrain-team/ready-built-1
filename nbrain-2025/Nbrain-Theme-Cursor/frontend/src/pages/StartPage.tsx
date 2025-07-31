import { Box, Flex, Text, Heading, Card, Grid } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';

const StartPage = () => {
    const navigate = useNavigate();

    const navigationItems = [
        {
            title: 'New Chat',
            description: 'Start a conversation with AI to get insights from your data',
            icon: '/new-icons/13.png',
            path: '/',
        },
        {
            title: 'Chat History',
            description: 'View and continue your previous conversations and insights',
            icon: '/new-icons/2.png',
            path: '/history',
        },
        {
            title: '1-2-1 Email Personalizer',
            description: 'Generate personalized emails at scale using AI automation',
            icon: '/new-icons/3.png',
            path: '/email-personalizer',
        },
        {
            title: 'Agent Ideas',
            description: 'Design and build custom AI agents for your workflows',
            icon: '/new-icons/7.png',
            path: '/agent-ideas',
        },
        {
            title: 'Knowledge Base',
            description: 'Manage documents and data sources for AI processing',
            icon: '/new-icons/4.png',
            path: '/knowledge',
        },
        {
            title: 'Sales Pipeline',
            description: 'Track opportunities and manage your sales pipeline with AI agents',
            icon: '/new-icons/14.png',
            path: '/crm',
        },
    ];

    return (
        <Box style={{ 
            background: 'white', 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            overflow: 'hidden'
        }}>
            <Box style={{ 
                flex: '1', 
                overflowY: 'auto',
                paddingBottom: '2rem'
            }}>
                <Flex direction="column" align="center" style={{ padding: '3rem 2rem 2rem 2rem' }}>
                    {/* Logo */}
                    <Box style={{ paddingTop: '3rem', marginBottom: '4rem' }}>
                        <img 
                            src="/new-icons/nbrain-logo.png" 
                            alt="nBrain Logo" 
                            style={{ height: '70px', objectFit: 'contain' }} 
                        />
                    </Box>

                    {/* Main content */}
                    <Box style={{ maxWidth: '1200px', width: '100%' }}>
                        <Flex direction="column" align="center" style={{ marginBottom: '5rem' }}>
                            <Heading 
                                size="9" 
                                weight="bold" 
                                mb="5" 
                                style={{ 
                                    letterSpacing: '-0.02em',
                                    fontSize: '3.5rem',
                                    fontWeight: 'bold',
                                    textAlign: 'center',
                                    width: '100%'
                                }}
                            >
                                nBrain Command Center
                            </Heading>
                            
                            <Text as="p" size="4" color="gray" style={{ maxWidth: '700px', textAlign: 'center', lineHeight: '1.6' }}>
                                Your staff-centralized AI platform that unifies documents, data, and business knowledge. 
                                Empower your team to ask questions, get instant answers, and make smarter decisions together.
                            </Text>
                        </Flex>

                        {/* Navigation Grid - 3x2 grid */}
                        <Box style={{ marginTop: '5rem' }}>
                            <Flex 
                                wrap="wrap"
                                justify="center"
                                gap="20px"
                                style={{ marginBottom: '4rem' }}
                            >
                                {navigationItems.map(item => (
                                    <Card 
                                        key={item.title}
                                        size="4"
                                        onClick={() => navigate(item.path)}
                                        style={{ 
                                            cursor: 'pointer', 
                                            transition: 'all 0.2s',
                                            minHeight: '240px',
                                            width: '350px',
                                            border: '1px solid #e5e5e5',
                                            background: 'white',
                                            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)'
                                        }}
                                        className="navigation-card"
                                    >
                                        <Flex direction="column" align="center" justify="center" gap="4" style={{ height: '100%', textAlign: 'center', padding: '2.5rem 2rem' }}>
                                            <Box style={{ marginBottom: '0.5rem' }}>
                                                <img 
                                                    src={item.icon} 
                                                    alt={item.title} 
                                                    style={{ width: '56px', height: '56px', objectFit: 'contain' }} 
                                                />
                                            </Box>
                                            <Box>
                                                <Heading 
                                                    size="5" 
                                                    mb="3" 
                                                    style={{ 
                                                        fontWeight: 'bold',
                                                        textAlign: 'center'
                                                    }}
                                                >
                                                    {item.title}
                                                </Heading>
                                                <Text size="2" color="gray" style={{ lineHeight: '1.6', textAlign: 'center' }}>{item.description}</Text>
                                            </Box>
                                        </Flex>
                                    </Card>
                                ))}
                            </Flex>
                        </Box>
                    </Box>
                </Flex>

                {/* Footer - now inside the scrollable area */}
                <Box style={{ marginTop: '4rem', paddingBottom: '2rem', textAlign: 'center' }}>
                    <Text as="p" size="2" color="gray">© {new Date().getFullYear()} nBrain. All Rights Reserved.</Text>
                </Box>
            </Box>

            <style>{`
                .navigation-card:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1) !important;
                    border-color: #d5d5d5 !important;
                }
            `}</style>
        </Box>
    );
};

export default StartPage; 