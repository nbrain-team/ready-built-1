import { useState, useRef, useEffect } from 'react';
import { Box, Flex, Text, TextField, IconButton, Card, Heading, Badge, Button, Progress } from '@radix-ui/themes';
import { PaperPlaneIcon, Cross2Icon, BookmarkIcon } from '@radix-ui/react-icons';
import api from '../api';
import ReactMarkdown from 'react-markdown';

interface ConversationMessage {
    role: 'user' | 'assistant';
    content: string;
}

interface AgentSpec {
    title: string;
    summary: string;
    steps: string[];
    agent_stack: any;
    client_requirements: string[];
    agent_type?: string;
}

interface AgentIdeatorProps {
    onClose: () => void;
    onComplete: (spec: AgentSpec, conversation: ConversationMessage[]) => void;
}

export const AgentIdeator = ({ onClose, onComplete }: AgentIdeatorProps) => {
    const [conversation, setConversation] = useState<ConversationMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const chatEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Check for saved session
        const savedSessionId = localStorage.getItem('agentIdeatorSessionId');
        if (savedSessionId) {
            loadSession(savedSessionId);
        } else {
            startConversation();
        }
    }, []);

    useEffect(() => {
        // Scroll to bottom when new messages are added
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [conversation]);

    useEffect(() => {
        // Save session after first AI response
        if (conversation.length >= 1 && conversation[0].role === 'assistant' && !sessionId) {
            saveSession();
        }
    }, [conversation, sessionId]);

    useEffect(() => {
        // Update progress based on conversation length
        const messageCount = conversation.filter(m => m.role === 'user').length;
        const estimatedProgress = Math.min((messageCount / 5) * 100, 90); // Assume ~5 exchanges needed
        setProgress(estimatedProgress);
        
        // Update saved session with new progress
        if (sessionId) {
            localStorage.setItem(`agentIdeatorSession_${sessionId}`, JSON.stringify({
                conversation,
                progress: estimatedProgress,
                timestamp: new Date().toISOString()
            }));
        }
    }, [conversation]);

    const saveSession = async () => {
        try {
            const newSessionId = Date.now().toString();
            setSessionId(newSessionId);
            localStorage.setItem('agentIdeatorSessionId', newSessionId);
            localStorage.setItem(`agentIdeatorSession_${newSessionId}`, JSON.stringify({
                conversation,
                progress,
                timestamp: new Date().toISOString()
            }));
        } catch (error) {
            console.error('Error saving session:', error);
        }
    };

    const loadSession = async (savedSessionId: string) => {
        try {
            const savedData = localStorage.getItem(`agentIdeatorSession_${savedSessionId}`);
            if (savedData) {
                const { conversation: savedConversation, progress: savedProgress } = JSON.parse(savedData);
                setConversation(savedConversation);
                setProgress(savedProgress);
                setSessionId(savedSessionId);
            } else {
                startConversation();
            }
        } catch (error) {
            console.error('Error loading session:', error);
            startConversation();
        }
    };

    const clearSession = () => {
        if (sessionId) {
            localStorage.removeItem('agentIdeatorSessionId');
            localStorage.removeItem(`agentIdeatorSession_${sessionId}`);
        }
    };

    const startConversation = async () => {
        try {
            setIsLoading(true);
            const response = await fetch(`${api.defaults.baseURL}/agent-ideator/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    message: '',
                    conversation_history: []
                })
            });

            if (response.headers.get('content-type')?.includes('text/event-stream')) {
                // Handle streaming response
                const reader = response.body?.getReader();
                const decoder = new TextDecoder();
                let assistantMessage = '';

                // Add empty assistant message to start
                setConversation([{ role: 'assistant', content: '' }]);

                if (reader) {
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    if (data.content) {
                                        assistantMessage += data.content;
                                        // Update the message
                                        setConversation([{
                                            role: 'assistant',
                                            content: assistantMessage
                                        }]);
                                    }
                                } catch (e) {
                                    console.error('Error parsing streaming data:', e);
                                }
                            }
                        }
                    }
                }
            } else {
                // Handle non-streaming response
                const data = await response.json();
                if (data.response) {
                    const assistantMessage: ConversationMessage = {
                        role: 'assistant',
                        content: data.response
                    };
                    setConversation([assistantMessage]);
                }
            }
        } catch (error) {
            console.error('Error starting conversation:', error);
            setConversation([{
                role: 'assistant',
                content: 'Sorry, I encountered an error starting the conversation. Please refresh and try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: ConversationMessage = {
            role: 'user',
            content: input
        };

        setConversation(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch(`${api.defaults.baseURL}/agent-ideator/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    message: input,
                    conversation_history: conversation
                })
            });

            if (response.headers.get('content-type')?.includes('text/event-stream')) {
                // Handle streaming response
                const reader = response.body?.getReader();
                const decoder = new TextDecoder();
                let assistantMessage = '';

                // Add empty assistant message to start
                setConversation(prev => [...prev, { role: 'assistant', content: '' }]);

                if (reader) {
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    if (data.content) {
                                        assistantMessage += data.content;
                                        // Update the last message
                                        setConversation(prev => {
                                            const newConv = [...prev];
                                            newConv[newConv.length - 1] = {
                                                role: 'assistant',
                                                content: assistantMessage
                                            };
                                            return newConv;
                                        });
                                    }
                                } catch (e) {
                                    // Skip invalid JSON
                                }
                            }
                        }
                    }
                }
            } else {
                // Handle non-streaming response
                const data = await response.json();
                
                if (data.response) {
                    const assistantMessage: ConversationMessage = {
                        role: 'assistant',
                        content: data.response
                    };
                    setConversation(prev => [...prev, assistantMessage]);
                }

                if (data.complete && data.specification) {
                    console.log('Ideation complete! Specification:', data.specification);
                    setProgress(100);
                    setIsComplete(true);
                    // Clear session when complete
                    clearSession();
                    // Call onComplete with the full conversation including the final response
                    const finalConversation = [...conversation, userMessage, { role: 'assistant' as const, content: data.response }];
                    // Wait a moment to let the UI update before calling onComplete
                    setTimeout(() => {
                        console.log('Calling onComplete with spec:', data.specification);
                        onComplete(data.specification, finalConversation);
                    }, 100);
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setConversation(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <Flex direction="column" style={{ height: '100vh', width: '100%', maxWidth: '800px', margin: '0 auto', position: 'relative' }}>
            {/* Header */}
            <Flex justify="between" align="center" p="4" style={{ borderBottom: '1px solid var(--gray-4)', flexShrink: 0 }}>
                <Flex align="center" gap="3">
                    <Heading size="5">Agent Ideator</Heading>
                    <Badge color="blue" variant="soft">AI Assistant</Badge>
                </Flex>
                <Flex gap="2">
                    {sessionId && (
                        <Button variant="soft" size="1" onClick={saveSession}>
                            <BookmarkIcon />
                            Save Progress
                        </Button>
                    )}
                    <IconButton variant="ghost" onClick={() => {
                        clearSession();
                        onClose();
                    }}>
                        <Cross2Icon />
                    </IconButton>
                </Flex>
            </Flex>

            {/* Progress Bar */}
            <Box px="4" py="2" style={{ flexShrink: 0 }}>
                <Flex align="center" gap="3">
                    <Text size="2" color="gray">Progress</Text>
                    <Box style={{ flex: 1 }}>
                        <Progress value={progress} />
                    </Box>
                    <Text size="2" color="gray">{Math.round(progress)}%</Text>
                </Flex>
            </Box>

            {/* Chat Area - Now full page scroll */}
            <Box style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
                <Flex direction="column" gap="3">
                    {conversation.map((msg, index) => (
                        <Box key={index}>
                            <Flex 
                                justify={msg.role === 'user' ? 'end' : 'start'}
                                style={{ marginBottom: '0.5rem' }}
                            >
                                <Card 
                                    style={{
                                        maxWidth: '70%',
                                        backgroundColor: msg.role === 'user' ? 'var(--accent-3)' : 'var(--gray-3)'
                                    }}
                                >
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </Card>
                            </Flex>
                        </Box>
                    ))}

                    {isLoading && (
                        <Flex justify="start">
                            <Card style={{ backgroundColor: 'var(--gray-3)' }}>
                                <Flex align="center" gap="2">
                                    <div className="thinking-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </Flex>
                            </Card>
                        </Flex>
                    )}
                    
                    <div ref={chatEndRef} />
                </Flex>
            </Box>

            {/* Input Area */}
            <Box p="4" style={{ borderTop: '1px solid var(--gray-4)', flexShrink: 0, backgroundColor: 'var(--color-background)' }}>
                {!isComplete ? (
                    <Flex gap="2">
                        <TextField.Root
                            placeholder="Type your message..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            style={{ flex: 1 }}
                            disabled={isLoading}
                        />
                        <IconButton 
                            onClick={sendMessage} 
                            disabled={!input.trim() || isLoading}
                        >
                            <PaperPlaneIcon />
                        </IconButton>
                    </Flex>
                ) : (
                    <Flex justify="center" gap="3">
                        <Button variant="soft" onClick={() => {
                            clearSession();
                            onClose();
                        }}>
                            Close
                        </Button>
                        <Button onClick={() => {
                            // The specification should already be saved by this point
                            // Just close the ideator to return to the agents page where it will be displayed
                            onClose();
                        }}>
                            View Agent Specification
                        </Button>
                    </Flex>
                )}
            </Box>

            <style>{`
                .thinking-indicator {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                .thinking-indicator span {
                    height: 8px;
                    width: 8px;
                    background-color: var(--gray-8);
                    border-radius: 50%;
                    display: inline-block;
                    animation: thinking 1.4s infinite ease-in-out both;
                }
                .thinking-indicator span:nth-child(1) {
                    animation-delay: -0.32s;
                }
                .thinking-indicator span:nth-child(2) {
                    animation-delay: -0.16s;
                }
                @keyframes thinking {
                    0%, 80%, 100% {
                        transform: scale(0);
                    }
                    40% {
                        transform: scale(1.0);
                    }
                }
            `}</style>
        </Flex>
    );
}; 