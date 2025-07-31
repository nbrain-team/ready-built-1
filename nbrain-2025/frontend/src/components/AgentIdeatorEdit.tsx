import { useState, useRef, useEffect } from 'react';
import { Box, Flex, Text, TextField, IconButton, ScrollArea, Card, Heading, Badge, Button } from '@radix-ui/themes';
import { PaperPlaneIcon, Cross2Icon } from '@radix-ui/react-icons';
import api from '../api';
import ReactMarkdown from 'react-markdown';

interface ConversationMessage {
    role: 'user' | 'assistant';
    content: string;
}

interface AgentSpec {
    id: string;
    title: string;
    summary: string;
    steps: string[];
    agent_stack: any;
    client_requirements: string[];
    agent_type?: string;
    status: string;
    created_at: string;
    updated_at?: string;
    conversation_history?: ConversationMessage[];
}

interface AgentIdeatorEditProps {
    spec: AgentSpec;
    onClose: () => void;
    onUpdate: (updatedSpec: AgentSpec) => void;
}

export const AgentIdeatorEdit = ({ spec, onClose, onUpdate }: AgentIdeatorEditProps) => {
    const [conversation, setConversation] = useState<ConversationMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollAreaRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Start with a message about editing
        const initialMessage: ConversationMessage = {
            role: 'assistant',
            content: `I see you want to edit the "${spec.title}" agent specification. What would you like to change? You can ask me to:
            
- Modify the title or summary
- Add, remove, or edit implementation steps
- Update the technical stack
- Change client requirements
- Adjust any other aspect of the specification

Just tell me what you'd like to modify!`
        };
        setConversation([initialMessage]);
    }, [spec.title]);

    useEffect(() => {
        // Scroll to bottom when new messages are added
        if (scrollAreaRef.current) {
            scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
        }
    }, [conversation]);

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
            const response = await fetch(`${api.defaults.baseURL}/agent-ideator/edit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    message: input,
                    current_spec: spec,
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
                
                const assistantMessage: ConversationMessage = {
                    role: 'assistant',
                    content: data.response
                };

                setConversation(prev => [...prev, assistantMessage]);

                // Check if the edit is complete
                if (data.complete && data.updated_spec) {
                    // Update the spec and save it
                    const updatedSpec = data.updated_spec;
                    await api.put(`/agent-ideas/${spec.id}`, updatedSpec);
                    onUpdate(updatedSpec);
                }
            }
        } catch (error) {
            console.error('Error during edit:', error);
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

    const handleSaveAndClose = async () => {
        // Save the conversation history with the spec
        if (spec.id) {
            await api.put(`/agent-ideas/${spec.id}`, {
                conversation_history: [...(spec.conversation_history || []), ...conversation]
            });
        }
        onClose();
    };

    return (
        <Flex direction="column" style={{ height: '100vh', width: '100%', maxWidth: '800px', margin: '0 auto' }}>
            {/* Header */}
            <Flex justify="between" align="center" p="4" style={{ borderBottom: '1px solid var(--gray-4)', flexShrink: 0 }}>
                <Flex align="center" gap="3">
                    <Heading size="5">Edit Agent Specification</Heading>
                    <Badge color="amber" variant="soft">Editing Mode</Badge>
                </Flex>
                <IconButton variant="ghost" onClick={handleSaveAndClose}>
                    <Cross2Icon />
                </IconButton>
            </Flex>

            {/* Current Spec Summary */}
            <Box p="4" style={{ borderBottom: '1px solid var(--gray-4)', backgroundColor: 'var(--gray-2)', flexShrink: 0 }}>
                <Text size="2" weight="bold">Currently Editing:</Text>
                <Text size="3">{spec.title}</Text>
            </Box>

            {/* Chat Area */}
            <ScrollArea 
                ref={scrollAreaRef}
                style={{ flex: 1, padding: '1rem', overflow: 'auto' }}
            >
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
                </Flex>
            </ScrollArea>

            {/* Input Area */}
            <Box p="4" style={{ borderTop: '1px solid var(--gray-4)', flexShrink: 0, backgroundColor: 'var(--color-background)' }}>
                <Flex gap="2">
                    <TextField.Root
                        placeholder="Describe what you'd like to change..."
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