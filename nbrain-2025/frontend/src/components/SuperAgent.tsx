import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  Flex, 
  IconButton, 
  ScrollArea, 
  Text, 
  TextField,
  Badge,
  Heading,
  Avatar,
  Separator
} from '@radix-ui/themes';
import { 
  Cross2Icon, 
  PaperPlaneIcon, 
  MagicWandIcon,
  ChatBubbleIcon,
  FileTextIcon,
  CheckCircledIcon,
  EnvelopeClosedIcon,
  CalendarIcon,
  DotsHorizontalIcon,
  VideoIcon,
  RocketIcon
} from '@radix-ui/react-icons';
import ReactMarkdown from 'react-markdown';
import api from '../api';

// Add microphone icon since Radix doesn't have one
const MicrophoneIcon = ({ width = 20, height = 20, ...props }) => (
  <svg width={width} height={height} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
    <line x1="12" y1="19" x2="12" y2="23"></line>
    <line x1="8" y1="23" x2="16" y2="23"></line>
  </svg>
);

// Add send icon to match the design
const SendIcon = ({ width = 20, height = 20, ...props }) => (
  <svg width={width} height={height} viewBox="0 0 24 24" fill="currentColor" {...props}>
    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
  </svg>
);

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  workflow?: string;
  actions?: any[];
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  keywords: string[];
  handler: (context: any) => Promise<any>;
}

const SuperAgent: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentWorkflow, setCurrentWorkflow] = useState<string | null>(null);
  const [workflowContext, setWorkflowContext] = useState<any>({});
  const [isListening, setIsListening] = useState(false);
  const [speechRecognition, setSpeechRecognition] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Available workflows
  const workflows: Workflow[] = [
    {
      id: 'social_media',
      name: 'Create and Post to Social Media',
      description: 'Create and publish social media content',
      icon: <ChatBubbleIcon />,
      keywords: ['facebook', 'linkedin', 'twitter', 'social media', 'post', 'share'],
      handler: async (context) => {
        // Social media workflow handler
        return { success: true };
      }
    },
    {
      id: 'google_docs_content',
      name: 'Create Content & Save to Google Docs',
      description: 'Create any content and save it as a Google Doc',
      icon: <FileTextIcon />,
      keywords: ['google doc', 'google docs', 'gdoc', 'save to doc', 'create doc', 'document'],
      handler: async (context) => {
        // Google Docs workflow handler
        return { success: true };
      }
    },
    {
      id: 'document_generation',
      name: 'Generate Documents',
      description: 'Create proposals, reports, and other documents',
      icon: <FileTextIcon />,
      keywords: ['document', 'proposal', 'report', 'create', 'generate', 'write'],
      handler: async (context) => {
        // Document generation handler
        return { success: true };
      }
    },
    {
      id: 'task_management',
      name: 'Manage Tasks',
      description: 'Create and manage tasks for clients',
      icon: <CheckCircledIcon />,
      keywords: ['task', 'todo', 'assign', 'create task', 'update task'],
      handler: async (context) => {
        // Task management handler
        return { success: true };
      }
    },
    {
      id: 'communication',
      name: 'Send Communications',
      description: 'Send emails and schedule meetings',
      icon: <EnvelopeClosedIcon />,
      keywords: ['email', 'send', 'message', 'meeting', 'schedule', 'calendar'],
      handler: async (context) => {
        // Communication handler
        return { success: true };
      }
    }
  ];

  // Auto-focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      // Small delay to ensure the component is fully rendered
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Keyboard shortcut to open/close
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(!isOpen);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isOpen]);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognitionClass = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognitionClass();
      
      recognition.continuous = true;  // Changed to true for continuous recording
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsListening(true);
      };
      
      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0])
          .map((result: any) => result.transcript)
          .join('');
        
        setInput(transcript);
      };
      
      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        
        if (event.error === 'not-allowed') {
          alert('Microphone permission denied. Please allow microphone access to use voice input.');
        }
      };
      
      recognition.onend = () => {
        // If still listening, restart recognition for continuous mode
        if (isListening) {
          try {
            recognition.start();
          } catch (e) {
            console.error('Failed to restart recognition:', e);
            setIsListening(false);
          }
        } else {
          setIsListening(false);
        }
      };
      
      setSpeechRecognition(recognition);
    }
  }, [isListening]);

  const toggleVoiceInput = () => {
    if (!speechRecognition) {
      alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }
    
    if (isListening) {
      speechRecognition.stop();
    } else {
      speechRecognition.start();
    }
  };

  const addMessage = (text: string, sender: 'user' | 'agent', workflow?: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      text,
      sender,
      timestamp: new Date(),
      workflow
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage = input.trim();
    setInput('');
    addMessage(userMessage, 'user');
    setIsProcessing(true);

    try {
      // Get current client ID if on client page
      const clientId = window.location.pathname.includes('/client/') 
        ? window.location.pathname.split('/client/')[1] 
        : null;

      // Call the Super Agent API
      const response = await api.post('/super-agent/chat', {
        message: userMessage,
        workflow_id: currentWorkflow,
        context: workflowContext,
        client_id: clientId
      });

      const data = response.data;

      // Handle workflow detection
      if (data.workflow_detected && !currentWorkflow) {
        setCurrentWorkflow(data.workflow_detected.id);
        // Only add the response, don't append first_question if context was already set
        addMessage(
          data.response,
          'agent',
          data.workflow_detected.id
        );
      } else {
        // Regular response
        addMessage(data.response, 'agent', currentWorkflow || undefined);
        
        // Update context if provided
        if (data.context_update) {
          setWorkflowContext((prev: any) => ({ ...prev, ...data.context_update }));
        }
        
        // Check if workflow is complete
        if (data.workflow_complete) {
          setCurrentWorkflow(null);
          setWorkflowContext({});
          
          // Handle any actions (e.g., social media posting)
          if (data.action) {
            // In a real implementation, this would trigger actual API calls
            console.log('Action to perform:', data.action);
          }
        }
      }
    } catch (error) {
      console.error('Error processing message:', error);
      addMessage(
        "I encountered an error. Please try again or rephrase your request.",
        'agent'
      );
    } finally {
      setIsProcessing(false);
      // Keep focus on input after sending
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Button */}
      <Button
        size="3"
        variant="solid"
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          zIndex: 999,
          display: isOpen ? 'none' : 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          background: '#bc4a4b',
          color: 'white',
          border: 'none',
          borderRadius: '50px',
          padding: '0.75rem 1.5rem',
          boxShadow: '0 4px 12px rgba(188, 74, 75, 0.3)',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          fontSize: '15px',
          fontWeight: '500'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.05)';
          e.currentTarget.style.boxShadow = '0 6px 20px rgba(188, 74, 75, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(188, 74, 75, 0.3)';
        }}
      >
        <img 
          src="/new-icons/13.png" 
          alt="Super Agent" 
          style={{ width: '24px', height: '24px', filter: 'brightness(0) invert(1)' }}
        />
        Super Agent
      </Button>

      {/* Chat Window */}
      {isOpen && (
        <Card
          style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            width: '380px',
            height: '600px',
            maxHeight: '80vh',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
            backgroundColor: '#FFFFFF',
            border: 'none',
            borderRadius: '20px',
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <Box
            style={{
              backgroundColor: '#6B7280',
              color: 'white',
              padding: '1rem 1.25rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Flex align="center" gap="3">
              <Box
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '8px'
                }}
              >
                <img 
                  src="/new-icons/13.png" 
                  alt="Super Agent" 
                  style={{ width: '100%', height: '100%' }}
                />
              </Box>
              <Text size="3" weight="medium">
                Super Agent
              </Text>
            </Flex>
            <Flex gap="2" align="center">
              {messages.length > 0 && (
                <Button
                  size="1"
                  variant="ghost"
                  onClick={() => {
                    setMessages([]);
                    setCurrentWorkflow(null);
                    setWorkflowContext({});
                    setInput('');
                    // Focus input after clearing
                    setTimeout(() => {
                      inputRef.current?.focus();
                    }, 100);
                  }}
                  style={{
                    color: 'white',
                    backgroundColor: 'transparent',
                    cursor: 'pointer',
                    fontSize: '12px',
                    padding: '4px 8px',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    borderRadius: '4px'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)';
                  }}
                >
                  New Chat
                </Button>
              )}
              <IconButton 
                size="2" 
                variant="ghost" 
                onClick={() => setIsOpen(false)}
                style={{
                  color: 'white',
                  backgroundColor: 'transparent',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <Cross2Icon width={20} height={20} />
              </IconButton>
            </Flex>
          </Box>
          
          {/* Messages Area */}
          <ScrollArea 
            style={{ 
              flex: 1, 
              padding: '1rem',
              backgroundColor: '#FFFFFF'
            }}
          >
            <Flex direction="column" gap="3">
              {messages.length === 0 && (
                <Box>
                  {/* Show intro message as agent chat bubble */}
                  <Flex gap="2" align="start" style={{ marginBottom: '0.5rem' }}>
                    <Box
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        backgroundColor: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        padding: '6px'
                      }}
                    >
                      <img 
                        src="/new-icons/13.png" 
                        alt="Super Agent" 
                        style={{ width: '100%', height: '100%' }}
                      />
                    </Box>
                    <Box
                      style={{ 
                        backgroundColor: 'white',
                        padding: '0.75rem 1rem',
                        borderRadius: '18px',
                        borderTopLeftRadius: '4px',
                        maxWidth: '70%',
                        wordBreak: 'break-word',
                        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                      }}
                    >
                      <Text size="2" style={{ color: '#1F2937', lineHeight: '1.4', whiteSpace: 'pre-line' }}>
                        {`What would you like me to do today?

-Create a post?
-New Email To Send?
-Video Message?

Just ask!`}
                      </Text>
                    </Box>
                  </Flex>
                  {/* Timestamp */}
                  <Text 
                    size="1" 
                    style={{ 
                      color: '#9CA3AF',
                      textAlign: 'left',
                      marginBottom: '0.5rem',
                      paddingLeft: '40px'
                    }}
                  >
                    {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Text>
                </Box>
              )}
              
              {messages.map((msg, index) => (
                <Box key={index}>
                  {msg.sender === 'user' ? (
                    // User message - aligned right
                    <Flex justify="end" style={{ marginBottom: '0.5rem' }}>
                      <Box
                        style={{ 
                          backgroundColor: '#1F3A36',
                          color: 'white',
                          padding: '0.75rem 1rem',
                          borderRadius: '18px',
                          borderBottomRightRadius: '4px',
                          maxWidth: '70%',
                          wordBreak: 'break-word'
                        }}
                      >
                        <Text size="2" style={{ lineHeight: '1.4' }}>
                          {msg.text}
                        </Text>
                      </Box>
                    </Flex>
                  ) : (
                    // Agent message - aligned left
                    <Flex gap="2" align="start" style={{ marginBottom: '0.5rem' }}>
                      <Box
                        style={{
                          width: '32px',
                          height: '32px',
                          borderRadius: '50%',
                          backgroundColor: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          padding: '6px'
                        }}
                      >
                        <img 
                          src="/new-icons/13.png" 
                          alt="Super Agent" 
                          style={{ width: '100%', height: '100%' }}
                        />
                      </Box>
                      <Box
                        style={{ 
                          backgroundColor: 'white',
                          padding: '0.75rem 1rem',
                          borderRadius: '18px',
                          borderTopLeftRadius: '4px',
                          maxWidth: '70%',
                          wordBreak: 'break-word',
                          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                        }}
                      >
                        <Text size="2" style={{ color: '#1F2937', lineHeight: '1.4' }}>
                          {msg.text}
                        </Text>
                      </Box>
                    </Flex>
                  )}
                  
                  {/* Timestamp */}
                  {index === messages.length - 1 || 
                   messages[index + 1]?.sender !== msg.sender ? (
                    <Text 
                      size="1" 
                      style={{ 
                        color: '#9CA3AF',
                        textAlign: msg.sender === 'user' ? 'right' : 'left',
                        marginBottom: '0.5rem',
                        paddingLeft: msg.sender === 'agent' ? '40px' : '0',
                        paddingRight: msg.sender === 'user' ? '8px' : '0'
                      }}
                    >
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Text>
                  ) : null}
                </Box>
              ))}
              
              {isProcessing && (
                <Flex gap="2" align="center">
                  <Box
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      backgroundColor: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      padding: '6px'
                    }}
                  >
                    <img 
                      src="/new-icons/13.png" 
                      alt="Super Agent" 
                      style={{ width: '100%', height: '100%' }}
                    />
                  </Box>
                  <Box style={{ 
                    backgroundColor: 'white',
                    padding: '0.75rem 1rem',
                    borderRadius: '18px',
                    borderTopLeftRadius: '4px',
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                  }}>
                    <Flex gap="1" align="center">
                      <Box className="typing-dot" />
                      <Box className="typing-dot" style={{ animationDelay: '0.2s' }} />
                      <Box className="typing-dot" style={{ animationDelay: '0.4s' }} />
                    </Flex>
                  </Box>
                </Flex>
              )}
              <div ref={messagesEndRef} />
            </Flex>
          </ScrollArea>
          
          {/* Input Area */}
          <Box 
            style={{ 
              padding: '1rem',
              backgroundColor: '#FFFFFF',
              borderTop: '1px solid rgba(0, 0, 0, 0.05)'
            }}
          >
            <form onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}>
              <Flex gap="2" align="center">
                <TextField.Root
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={isProcessing}
                  style={{ 
                    flex: 1,
                    backgroundColor: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '25px',
                    padding: '0.75rem 1rem',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = '#1F3A36';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = '#E5E7EB';
                  }}
                />
                
                {/* Send Button */}
                <IconButton 
                  type="submit" 
                  disabled={isProcessing || !input.trim()}
                  size="3"
                  style={{
                    background: isProcessing || !input.trim() 
                      ? '#E5E7EB' 
                      : '#bc4a4b',
                    color: 'white',
                    border: 'none',
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    cursor: isProcessing || !input.trim() ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s',
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  onMouseEnter={(e) => {
                    if (!isProcessing && input.trim()) {
                      e.currentTarget.style.transform = 'scale(1.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scale(1)';
                  }}
                >
                  <SendIcon width={20} height={20} />
                </IconButton>
              </Flex>
            </form>
          </Box>
          
          <style>
            {`
              .typing-dot {
                width: 8px;
                height: 8px;
                background-color: #6B7280;
                border-radius: 50%;
                animation: typing 1.4s infinite;
              }
              
              @keyframes typing {
                0%, 60%, 100% {
                  opacity: 0.3;
                  transform: translateY(0);
                }
                30% {
                  opacity: 1;
                  transform: translateY(-10px);
                }
              }
            `}
          </style>
        </Card>
      )}
    </>
  );
};

export default SuperAgent; 