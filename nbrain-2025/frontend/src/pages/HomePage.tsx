import React, { useState, useRef, useEffect } from 'react';
import { Box, Heading, Text, TextField, Button, Flex, Select, IconButton } from '@radix-ui/themes';
import { PaperPlaneIcon, PlusIcon, Share2Icon, CalendarIcon, LayersIcon } from '@radix-ui/react-icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '../api';
import './HomePage.css';

// Import popup components
import { DateSelectionPopup } from '../components/DateSelectionPopup';
import { TemplateAgentsPopup } from '../components/TemplateAgentsPopup';
import { ChatModeSelector, ChatMode } from '../components/ChatModeSelector';

interface Message {
    text: string;
    sender: 'user' | 'ai';
    sources?: (string | { source: string; client_specific?: boolean })[];
}

interface HomePageProps {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}

const HomePage = ({ messages, setMessages }: HomePageProps) => {
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedClient, setSelectedClient] = useState<string>('all');
    const [clients, setClients] = useState<any[]>([]);
    const [savingMessage, setSavingMessage] = useState<number | null>(null);
    const [activePopup, setActivePopup] = useState<string | null>(null);
    const [chatMode, setChatMode] = useState<ChatMode>('standard');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchClients();
        // Load saved chat mode preference
        const savedMode = localStorage.getItem('chatMode') as ChatMode;
        if (savedMode && ['standard', 'quick', 'deep'].includes(savedMode)) {
            setChatMode(savedMode);
        }
    }, []);

    const handleChatModeChange = (mode: ChatMode) => {
        setChatMode(mode);
        localStorage.setItem('chatMode', mode);
    };

    const fetchClients = async () => {
        try {
            const response = await api.get('/clients');
            setClients(response.data);
        } catch (error) {
            console.error('Error fetching clients:', error);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = { text: input, sender: 'user' as const };
        setMessages([...messages, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${api.defaults.baseURL}/chat/stream?token=${token}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: input,
                    history: messages.map(msg => ({
                        text: msg.text,
                        sender: msg.sender
                    })),
                    client_id: selectedClient !== 'all' ? selectedClient : undefined,
                    chat_mode: chatMode
                }),
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            if (!response.body) {
                throw new Error("Response body is null");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';
            let sources: any[] = [];

            // Add empty AI message to start
            const aiMessageIndex = messages.length + 1;
            setMessages(prev => [...prev, { text: '', sender: 'ai', sources: [] }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n').filter(line => line.startsWith('data: '));

                for (const line of lines) {
                    const jsonStr = line.replace('data: ', '');
                    try {
                        if (jsonStr.trim() === '[DONE]') continue;
                        const data = JSON.parse(jsonStr);
                        if (data.content) {
                            fullResponse += data.content;
                            // Update the AI message with streaming content
                            setMessages(prev => {
                                const newMessages = [...prev];
                                newMessages[aiMessageIndex] = {
                                    text: fullResponse,
                                    sender: 'ai',
                                    sources: data.sources || sources
                                };
                                return newMessages;
                            });
                        }
                        if (data.sources) {
                            sources = data.sources;
                        }
                    } catch (e) {
                        console.error('Failed to parse stream data chunk:', jsonStr);
                    }
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: Message = {
                text: 'Sorry, I encountered an error. Please try again.',
                sender: 'ai'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const saveToClientHistory = async (messageIndex: number) => {
        if (selectedClient === 'all' || savingMessage === messageIndex) return;
        
        const message = messages[messageIndex];
        const query = messageIndex > 0 ? messages[messageIndex - 1]?.text : undefined;
        
        setSavingMessage(messageIndex);
        
        try {
            const formData = new FormData();
            formData.append('message', message.text);
            if (query) formData.append('query', query);
            if (message.sources) formData.append('sources', JSON.stringify(message.sources));
            
            const response = await fetch(`${api.defaults.baseURL}/clients/${selectedClient}/chat-history`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            
            // Show success feedback
            setTimeout(() => setSavingMessage(null), 1000);
        } catch (error) {
            console.error('Error saving to client history:', error);
            setSavingMessage(null);
        }
    };

    return (
        <div className="chat-page-container">
            <div className="page-header">
                <Heading size="7" style={{ color: 'var(--gray-12)' }}>AI Chat</Heading>
                <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                    Ask questions and get answers from your internal knowledge base, powered by AI.
                </Text>
            </div>

            <div className="chat-messages-area">
                {messages.map((msg, index) => (
                    <div key={index} className="message-container">
                        <div className={`message-bubble ${msg.sender}`} style={{ position: 'relative' }}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {msg.text}
                            </ReactMarkdown>
                            
                            {/* Add + button for AI messages when a client is selected */}
                            {msg.sender === 'ai' && selectedClient !== 'all' && (
                                <IconButton
                                    size="1"
                                    variant="soft"
                                    color={savingMessage === index ? 'green' : 'gray'}
                                    style={{
                                        position: 'absolute',
                                        bottom: '8px',
                                        right: '8px',
                                        opacity: savingMessage === index ? 1 : 0.7,
                                        transition: 'opacity 0.2s'
                                    }}
                                    onClick={() => saveToClientHistory(index)}
                                    disabled={savingMessage === index}
                                >
                                    {savingMessage === index ? '✓' : <PlusIcon />}
                                </IconButton>
                            )}
                        </div>
                        {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && (
                            <div className="citations">
                                <span className="citation-title">Sources:</span>
                                {msg.sources.map((source, i) => {
                                    const sourceText = typeof source === 'string' ? source : source.source;
                                    const isClientSpecific = typeof source === 'object' && 'client_specific' in source && source.client_specific;
                                    return (
                                        <span key={i} className={`citation-source ${isClientSpecific ? 'client-specific' : ''}`}>
                                            {sourceText}
                                        </span>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                ))}
                {isLoading && (
                    <div className="message-container">
                        <div className="message-bubble ai">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
                <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <Select.Root value={selectedClient} onValueChange={setSelectedClient}>
                        <Select.Trigger style={{ minWidth: '200px' }} placeholder="Select a client..." />
                        <Select.Content>
                            <Select.Item value="all">All Clients</Select.Item>
                            {clients.map(client => (
                                <Select.Item key={client.id} value={client.id}>
                                    {client.name}
                                </Select.Item>
                            ))}
                        </Select.Content>
                    </Select.Root>
                    
                    <TextField.Root
                        size="3"
                        placeholder="Ask me anything..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        style={{ flex: 1 }}
                    />
                    
                    {/* Icon buttons with popups */}
                    <Flex gap="2" align="center">
                        <ChatModeSelector value={chatMode} onChange={handleChatModeChange} />
                        
                        <div style={{ position: 'relative' }}>
                            <IconButton 
                                variant="ghost" 
                                onClick={() => setActivePopup(activePopup === 'date' ? null : 'date')} 
                                style={{ cursor: 'pointer', color: 'var(--gray-11)' }}
                                type="button"
                            >
                                <CalendarIcon width={22} height={22} />
                            </IconButton>
                            {activePopup === 'date' && <DateSelectionPopup />}
                        </div>

                        <div style={{ position: 'relative' }}>
                            <IconButton 
                                variant="ghost" 
                                onClick={() => setActivePopup(activePopup === 'agents' ? null : 'agents')} 
                                style={{ cursor: 'pointer', color: 'var(--gray-11)' }}
                                type="button"
                            >
                                <LayersIcon width={22} height={22} />
                            </IconButton>
                            {activePopup === 'agents' && <TemplateAgentsPopup />}
                        </div>
                    </Flex>
                    
                    <Button size="3" type="submit" disabled={isLoading || !input.trim()}>
                        <PaperPlaneIcon />
                        Send
                    </Button>
                </form>
            </div>
        </div>
    );
};

export default HomePage; 