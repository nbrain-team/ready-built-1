import React, { useState, useEffect } from 'react';
import { Box, Heading, Text, Card, Flex, Button, Tabs, Badge, Avatar, IconButton, TextField, ScrollArea, Dialog } from '@radix-ui/themes';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, EyeOpenIcon, ChatBubbleIcon, FileTextIcon, CheckCircledIcon, PersonIcon, ActivityLogIcon, EnvelopeClosedIcon, CalendarIcon, TrashIcon, ClockIcon, InfoCircledIcon, RocketIcon, ExclamationTriangleIcon, LightningBoltIcon, ReloadIcon } from '@radix-ui/react-icons';
import api from '../api';
import ViewProfileDialog from '../components/ViewProfileDialog';
import ClientAvatar from '../components/ClientAvatar';
import ClientAIInsights from '../components/ClientAIInsights';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ClientDetail = () => {
  const { clientId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [client, setClient] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showProfileDialog, setShowProfileDialog] = useState(false);

  useEffect(() => {
    fetchClientData();
  }, [clientId]);

  const fetchClientData = async () => {
    try {
      const response = await api.get(`/clients/${clientId}`);
      setClient(response.data);
    } catch (error) {
      console.error('Error fetching client:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !client) {
    return <div>Loading...</div>;
  }

  return (
    <div key={clientId} className="page-container" style={{ maxWidth: '100%', padding: '1rem', height: '100vh', overflow: 'auto' }}>
      {/* Header */}
      <Flex justify="between" align="center" mb="4">
        <Flex align="center" gap="3">
          <IconButton 
            variant="soft" 
            onClick={() => navigate('/clients')}
            style={{ cursor: 'pointer' }}
          >
            <ArrowLeftIcon />
          </IconButton>
          <ClientAvatar
            name={client.name}
            domain={client.domain}
            website={client.companyWebsite}
            size="4"
            color="blue"
          />
          <Box>
            <Heading size="6">{client.name}</Heading>
            <Text size="2" color="gray">{client.primaryContactEmail}</Text>
          </Box>
          <Badge size="2" color="green">{client.status}</Badge>
        </Flex>
        <Button variant="soft" onClick={() => setShowProfileDialog(true)}>
          <EyeOpenIcon /> View Profile
        </Button>
      </Flex>

      {/* Profile Dialog */}
      <ViewProfileDialog
        open={showProfileDialog}
        onOpenChange={setShowProfileDialog}
        client={client}
        onUpdate={fetchClientData}
      />

      {/* Tabs */}
      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List size="2">
          <Tabs.Trigger value="overview">
            <Flex align="center" gap="2">
              <ActivityLogIcon />
              <Text>Overview</Text>
            </Flex>
          </Tabs.Trigger>
          <Tabs.Trigger value="communications">
            <Flex align="center" gap="2">
              <ChatBubbleIcon />
              <Text>Communications</Text>
            </Flex>
          </Tabs.Trigger>
          <Tabs.Trigger value="tasks">
            <Flex align="center" gap="2">
              <CheckCircledIcon />
              <Text>Tasks</Text>
            </Flex>
          </Tabs.Trigger>
          <Tabs.Trigger value="documents">
            <Flex align="center" gap="2">
              <FileTextIcon />
              <Text>Documents</Text>
            </Flex>
          </Tabs.Trigger>
          <Tabs.Trigger value="team">
            <Flex align="center" gap="2">
              <PersonIcon />
              <Text>Team</Text>
            </Flex>
          </Tabs.Trigger>
        </Tabs.List>

        <Box mt="4">
          <Tabs.Content value="overview">
            <OverviewTab client={client} />
          </Tabs.Content>
          <Tabs.Content value="communications">
            <CommunicationsTab clientId={clientId!} clientName={client.name} />
          </Tabs.Content>
          <Tabs.Content value="tasks">
            <TasksTab clientId={clientId!} />
          </Tabs.Content>
          <Tabs.Content value="documents">
            <DocumentsTab clientId={clientId!} />
          </Tabs.Content>
          <Tabs.Content value="team">
            <TeamTab clientId={clientId!} />
          </Tabs.Content>
        </Box>
      </Tabs.Root>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ client }: { client: any }) => {
  const [activities, setActivities] = useState<any[]>([]);
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [selectedChat, setSelectedChat] = useState<any>(null);
  const [upcomingMeetings, setUpcomingMeetings] = useState<any[]>([]);
  
  useEffect(() => {
    fetchActivities();
    fetchChatHistory();
    fetchUpcomingMeetings();
  }, [client.id]);
  
  const fetchActivities = async () => {
    try {
      const response = await api.get(`/clients/${client.id}/activities`);
      setActivities(response.data);
    } catch (error) {
      console.error('Error fetching activities:', error);
    }
  };
  
  const fetchChatHistory = async () => {
    try {
      const response = await api.get(`/clients/${client.id}/chat-history`);
      setChatHistory(response.data);
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };
  
  const fetchUpcomingMeetings = async () => {
    try {
      const response = await api.get(`/clients/${client.id}/upcoming-meetings`);
      setUpcomingMeetings(response.data);
    } catch (error) {
      console.error('Error fetching upcoming meetings:', error);
    }
  };
  
  const deleteChat = async (chatId: string) => {
    try {
      await api.delete(`/clients/${client.id}/chat-history/${chatId}`);
      fetchChatHistory();
      setSelectedChat(null);
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };
  
  const getActivityIcon = (type: string) => {
    switch(type) {
      case 'client_created': return '🎉';
      case 'task_created': return '✅';
      case 'task_status_changed': return '🔄';
      case 'document_uploaded': return '📄';
      case 'team_member_added': return '👤';
      case 'communication_added': return '💬';
      case 'client_updated': return '✏️';
      default: return '📌';
    }
  };
  
  const formatMeetingTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const isToday = date.toDateString() === today.toDateString();
    const isTomorrow = date.toDateString() === tomorrow.toDateString();
    
    if (isToday) {
      return `Today at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    } else if (isTomorrow) {
      return `Tomorrow at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      });
    }
  };
  
  return (
    <Box>
      {/* AI Insights Section and Metrics Summary */}
      <Box mb="4" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
        <ClientAIInsights clientId={client.id} clientName={client.name} />
        
        {/* Right Column - Stats and Meetings */}
        <Flex direction="column" gap="3" style={{ height: '100%' }}>
          {/* Metrics Summary Card */}
          <Card style={{ flex: '1' }}>
            <Heading size="4" mb="3">Quick Stats</Heading>
            <Flex direction="column" gap="3">
              <Box>
                <Flex justify="between" align="center">
                  <Flex align="center" gap="2">
                    <EnvelopeClosedIcon color="blue" />
                    <Text size="2" weight="medium">Total Emails</Text>
                  </Flex>
                  <Text size="3" weight="bold">{client.totalEmails || 0}</Text>
                </Flex>
              </Box>
              
              <Box>
                <Flex justify="between" align="center">
                  <Flex align="center" gap="2">
                    <CalendarIcon color="green" />
                    <Text size="2" weight="medium">Meetings Scheduled</Text>
                  </Flex>
                  <Text size="3" weight="bold">{client.totalMeetings || 0}</Text>
                </Flex>
              </Box>
              
              <Box>
                <Flex justify="between" align="center">
                  <Flex align="center" gap="2">
                    <CheckCircledIcon color="purple" />
                    <Text size="2" weight="medium">Tasks Completed</Text>
                  </Flex>
                  <Text size="3" weight="bold">{client.completedTasks || 0}/{client.totalTasks || 0}</Text>
                </Flex>
              </Box>
              
              <Box>
                <Flex justify="between" align="center">
                  <Flex align="center" gap="2">
                    <FileTextIcon color="orange" />
                    <Text size="2" weight="medium">Documents</Text>
                  </Flex>
                  <Text size="3" weight="bold">{client.totalDocuments || 0}</Text>
                </Flex>
              </Box>
              
              <Box>
                <Flex justify="between" align="center">
                  <Flex align="center" gap="2">
                    <ActivityLogIcon color="gray" />
                    <Text size="2" weight="medium">Last Activity</Text>
                  </Flex>
                  <Text size="2" color="gray">
                    {client.lastCommunication ? 
                      new Date(client.lastCommunication).toLocaleDateString() : 
                      'No activity'}
                  </Text>
                </Flex>
              </Box>
            </Flex>
          </Card>
          
          {/* Upcoming Meetings Card */}
          <Card style={{ flex: '1', display: 'flex', flexDirection: 'column' }}>
            <Flex justify="between" align="center" mb="3">
              <Heading size="4">Upcoming Meetings</Heading>
              <Button 
                size="1" 
                variant="soft"
                onClick={async () => {
                  try {
                    await api.post(`/clients/${client.id}/sync-all`);
                    // Wait a moment then refresh meetings
                    setTimeout(() => {
                      fetchUpcomingMeetings();
                    }, 3000);
                  } catch (error) {
                    console.error('Error syncing calendar:', error);
                  }
                }}
              >
                <ReloadIcon /> Sync Calendar
              </Button>
            </Flex>
            <Box style={{ flex: '1', overflow: 'auto' }}>
              {upcomingMeetings.length > 0 ? (
                <Flex direction="column" gap="2">
                  {upcomingMeetings.map((meeting) => (
                    <Box
                      key={meeting.id}
                      style={{
                        padding: '0.75rem',
                        border: '1px solid var(--gray-4)',
                        borderRadius: '6px',
                        backgroundColor: 'var(--gray-1)'
                      }}
                    >
                      <Flex direction="column" gap="1">
                        <Text size="2" weight="medium" style={{ 
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {meeting.title}
                        </Text>
                        <Flex align="center" gap="2">
                          <ClockIcon color="blue" width="14" height="14" />
                          <Text size="1" color="blue">
                            {formatMeetingTime(meeting.startTime)}
                          </Text>
                        </Flex>
                        {meeting.location && meeting.location !== 'N/A' && (
                          <Text size="1" color="gray" style={{ 
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            📍 {meeting.location}
                          </Text>
                        )}
                        <Text size="1" color="gray">
                          {meeting.attendees.length} attendee{meeting.attendees.length !== 1 ? 's' : ''}
                        </Text>
                      </Flex>
                    </Box>
                  ))}
                </Flex>
              ) : (
                <Text size="2" color="gray">
                  No upcoming meetings scheduled. Connect your calendar to see your meetings here.
                </Text>
              )}
            </Box>
          </Card>
        </Flex>
      </Box>
      
      {/* Chat History and Activity Timeline */}
      <Box style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
        <Card>
          <Heading size="4" mb="3">Chat History</Heading>
          <ScrollArea style={{ height: '300px' }}>
            <Flex direction="column" gap="2">
              {chatHistory.length > 0 ? (
                chatHistory.map((chat) => (
                  <Box
                    key={chat.id}
                    onClick={() => setSelectedChat(chat)}
                    style={{
                      padding: '0.75rem',
                      border: '1px solid var(--gray-4)',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      backgroundColor: selectedChat?.id === chat.id ? 'var(--gray-2)' : 'transparent',
                      transition: 'background-color 0.2s'
                    }}
                  >
                    {chat.query && (
                      <Text size="1" color="gray" style={{ 
                        display: 'block',
                        marginBottom: '4px',
                        fontStyle: 'italic'
                      }}>
                        Q: {chat.query.substring(0, 50)}...
                      </Text>
                    )}
                    <Text size="2" style={{ 
                      display: 'block',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {chat.message.substring(0, 100)}...
                    </Text>
                    <Text size="1" color="gray" style={{ 
                      display: 'block',
                      marginTop: '4px'
                    }}>
                      {new Date(chat.created_at).toLocaleDateString()}
                    </Text>
                  </Box>
                ))
              ) : (
                <Text size="2" color="gray">
                  No saved chat messages yet. Use the AI Chat with this client selected and click the + button on responses to save them here.
                </Text>
              )}
            </Flex>
          </ScrollArea>
        </Card>

        <Card>
          <Heading size="4" mb="3">Activity Timeline</Heading>
          <ScrollArea style={{ height: '300px' }}>
            <Flex direction="column" gap="2">
              {activities.length > 0 ? (
                activities.map((activity) => (
                  <Box
                    key={activity.id}
                    style={{
                      padding: '0.75rem',
                      borderLeft: '3px solid var(--accent-9)',
                      backgroundColor: 'var(--gray-2)',
                      borderRadius: '4px'
                    }}
                  >
                    <Flex align="center" gap="2" mb="1">
                      <Text size="3">{getActivityIcon(activity.activity_type)}</Text>
                      <Text size="2" weight="medium">{activity.description}</Text>
                    </Flex>
                    <Text size="1" color="gray">
                      {new Date(activity.created_at).toLocaleString()}
                    </Text>
                  </Box>
                ))
              ) : (
                <Text size="2" color="gray">No recent activity</Text>
              )}
            </Flex>
          </ScrollArea>
        </Card>
      </Box>

      {/* Chat Detail Dialog */}
      <Dialog.Root open={!!selectedChat} onOpenChange={(open) => !open && setSelectedChat(null)}>
        <Dialog.Content style={{ maxWidth: 700 }}>
          <Dialog.Title>
            <Flex justify="between" align="center">
              <Heading size="4">Chat Message</Heading>
              <Flex gap="2">
                <IconButton
                  size="2"
                  color="red"
                  variant="soft"
                  onClick={() => deleteChat(selectedChat?.id)}
                >
                  <TrashIcon />
                </IconButton>
                <Dialog.Close>
                  <Button variant="ghost" size="2">✕</Button>
                </Dialog.Close>
              </Flex>
            </Flex>
          </Dialog.Title>
          
          {selectedChat && (
            <Box mt="3">
              {selectedChat.query && (
                <Box mb="3">
                  <Text size="2" color="gray" weight="medium">Question:</Text>
                  <Text size="2" style={{ marginTop: '4px' }}>{selectedChat.query}</Text>
                </Box>
              )}
              
              <Box mb="3">
                <Text size="2" color="gray" weight="medium">Response:</Text>
                <Box mt="2" style={{ 
                  padding: '1rem',
                  backgroundColor: 'var(--gray-2)',
                  borderRadius: '6px',
                  maxHeight: '400px',
                  overflow: 'auto'
                }}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {selectedChat.message}
                  </ReactMarkdown>
                </Box>
              </Box>
              
              {selectedChat.sources && selectedChat.sources.length > 0 && (
                <Box>
                  <Text size="2" color="gray" weight="medium">Sources:</Text>
                  <Flex gap="2" wrap="wrap" mt="2">
                    {selectedChat.sources.map((source: any, i: number) => (
                      <Badge key={i} variant="soft" color="gray">
                        {typeof source === 'string' ? source : source.source}
                      </Badge>
                    ))}
                  </Flex>
                </Box>
              )}
              
              <Text size="1" color="gray" mt="3">
                Saved on {new Date(selectedChat.created_at).toLocaleString()}
              </Text>
            </Box>
          )}
        </Dialog.Content>
      </Dialog.Root>
    </Box>
  );
};

// Communications Tab (Slack-like)
const CommunicationsTab = ({ clientId, clientName }: { clientId: string; clientName: string }) => {
  const [message, setMessage] = useState('');
  const [communications, setCommunications] = useState<any[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'email' | 'calendar_event' | 'internal_chat' | 'transcripts' | 'industry'>('all');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchCommunications();
  }, [clientId]);

  const fetchCommunications = async () => {
    try {
      const response = await api.get(`/clients/${clientId}/communications`);
      setCommunications(response.data);
    } catch (error) {
      console.error('Error fetching communications:', error);
    }
  };

  const syncAll = async () => {
    setIsSyncing(true);
    try {
      await api.post(`/clients/${clientId}/sync-all`);
      // Wait a bit and refresh
      setTimeout(() => {
        fetchCommunications();
        setIsSyncing(false);
      }, 5000);
    } catch (error) {
      console.error('Error syncing data:', error);
      setIsSyncing(false);
    }
  };

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    try {
      const response = await api.post(`/clients/${clientId}/communications`, {
        content: message,
        type: 'internal_chat'
      });
      
      // Add the new message to the list
      setCommunications([...communications, response.data]);
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const getCommIcon = (type: string) => {
    switch(type) {
      case 'email': return <EnvelopeClosedIcon />;
      case 'calendar_event': return <CalendarIcon />;
      case 'internal_chat': return <ChatBubbleIcon />;
      default: return <ActivityLogIcon />;
    }
  };

  const getCommColor = (type: string) => {
    switch(type) {
      case 'email': return 'blue';
      case 'calendar_event': return 'green';
      case 'internal_chat': return 'gray';
      default: return 'gray';
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const cleanEmailContent = (content: string) => {
    if (!content) return '';
    
    // Remove [image: icon] type placeholders
    let cleaned = content.replace(/\[image:[^\]]+\]/g, '');
    
    // Convert bare URLs to links
    cleaned = cleaned.replace(/<(https?:\/\/[^\s>]+)>/g, (match, url) => {
      const domain = new URL(url).hostname.replace('www.', '');
      return `[${domain}]`;
    });
    
    // Remove excessive whitespace
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n');
    
    // Trim
    return cleaned.trim();
  };

  const filteredCommunications = communications.filter(comm => {
    if (filter === 'all' || filter === 'transcripts' || filter === 'industry') return true;
    return comm.type === filter;
  });

  // Render different content based on filter
  if (filter === 'transcripts') {
    return (
      <Card style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
        <Box style={{ borderBottom: '1px solid var(--gray-4)', padding: '1rem', flexShrink: 0 }}>
          <Flex justify="between" align="center" mb="3">
            <Heading size="4">Communications</Heading>
            <Button
              size="2"
              variant="soft"
              onClick={syncAll}
              disabled={isSyncing}
            >
              {isSyncing ? 'Syncing...' : 'Sync Email & Calendar'}
            </Button>
          </Flex>
          
          <Flex gap="2">
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('all')}
            >
              All
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('email')}
            >
              <EnvelopeClosedIcon /> Emails
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('calendar_event')}
            >
              <CalendarIcon /> Calendar
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('internal_chat')}
            >
              <ChatBubbleIcon /> Chat
            </Button>
            <Button
              size="1"
              variant="solid"
              onClick={() => setFilter('transcripts')}
            >
              <FileTextIcon /> Transcripts
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('industry')}
            >
              <ActivityLogIcon /> Industry
            </Button>
          </Flex>
        </Box>
        
        <Box style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
          <MeetingTranscriptsContent clientId={clientId} clientName={clientName} />
        </Box>
      </Card>
    );
  }

  if (filter === 'industry') {
    return (
      <Card style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
        <Box style={{ borderBottom: '1px solid var(--gray-4)', padding: '1rem', flexShrink: 0 }}>
          <Flex justify="between" align="center" mb="3">
            <Heading size="4">Communications</Heading>
            <Button
              size="2"
              variant="soft"
              onClick={syncAll}
              disabled={isSyncing}
            >
              {isSyncing ? 'Syncing...' : 'Sync Email & Calendar'}
            </Button>
          </Flex>
          
          <Flex gap="2">
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('all')}
            >
              All
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('email')}
            >
              <EnvelopeClosedIcon /> Emails
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('calendar_event')}
            >
              <CalendarIcon /> Calendar
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('internal_chat')}
            >
              <ChatBubbleIcon /> Chat
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('transcripts')}
            >
              <FileTextIcon /> Transcripts
            </Button>
            <Button
              size="1"
              variant="solid"
              onClick={() => setFilter('industry')}
            >
              <ActivityLogIcon /> Industry
            </Button>
          </Flex>
        </Box>
        
        <Box style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
          <IndustryPulseContent clientId={clientId} clientName={clientName} />
        </Box>
      </Card>
    );
  }

  return (
    <Card style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
      <Flex direction="column" style={{ flex: 1, minWidth: 0, height: '100%' }}>
        <Box style={{ borderBottom: '1px solid var(--gray-4)', padding: '1rem', flexShrink: 0 }}>
          <Flex justify="between" align="center" mb="3">
            <Heading size="4">Communications</Heading>
            <Button
              size="2"
              variant="soft"
              onClick={syncAll}
              disabled={isSyncing}
            >
              {isSyncing ? 'Syncing...' : 'Sync Email & Calendar'}
            </Button>
          </Flex>
          
          <Flex gap="2">
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('all')}
            >
              All
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('email')}
            >
              <EnvelopeClosedIcon /> Emails
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('calendar_event')}
            >
              <CalendarIcon /> Calendar
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('internal_chat')}
            >
              <ChatBubbleIcon /> Chat
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('transcripts')}
            >
              <FileTextIcon /> Transcripts
            </Button>
            <Button
              size="1"
              variant="soft"
              onClick={() => setFilter('industry')}
            >
              <ActivityLogIcon /> Industry
            </Button>
          </Flex>
        </Box>
        
        <Box style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
          <ScrollArea style={{ height: '100%', padding: '1rem' }}>
            <Flex direction="column" gap="2">
              {filteredCommunications.map((comm) => (
                <Box 
                  key={comm.id} 
                  style={{ 
                    borderRadius: '6px',
                    border: '1px solid var(--gray-4)',
                    backgroundColor: expandedItems.has(comm.id) ? 'var(--gray-2)' : 'var(--gray-1)',
                    overflow: 'hidden'
                  }}
                >
                  {/* Email/Calendar Header Row */}
                  {(comm.type === 'email' || comm.type === 'calendar_event') ? (
                    <>
                      <Box
                        onClick={() => toggleExpanded(comm.id)}
                        style={{ 
                          padding: '0.75rem', 
                          cursor: 'pointer',
                          borderBottom: expandedItems.has(comm.id) ? '1px solid var(--gray-4)' : 'none'
                        }}
                      >
                        <Flex align="center" gap="3">
                          <Box style={{ color: `var(--${getCommColor(comm.type)}-9)`, flexShrink: 0 }}>
                            {getCommIcon(comm.type)}
                          </Box>
                          
                          <Box style={{ flex: 1, minWidth: 0 }}>
                            <Flex justify="between" align="center" gap="2">
                              <Flex direction="column" style={{ flex: 1, minWidth: 0 }}>
                                <Flex align="center" gap="2">
                                  <Text size="2" weight="medium" style={{ 
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {comm.fromUser}
                                  </Text>
                                  <Badge size="1" color={getCommColor(comm.type)}>
                                    {comm.type === 'calendar_event' ? 'Calendar' : 'Email'}
                                  </Badge>
                                  {comm.syncedBy && (
                                    <Badge size="1" color="gray" variant="soft">
                                      via {comm.syncedBy}
                                    </Badge>
                                  )}
                                </Flex>
                                
                                {comm.subject && (
                                  <Text size="2" style={{ 
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    color: 'var(--gray-11)'
                                  }}>
                                    {comm.subject}
                                  </Text>
                                )}
                                
                                {!expandedItems.has(comm.id) && comm.content && (
                                  <Text size="1" color="gray" style={{ 
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    maxWidth: '100%'
                                  }}>
                                    {cleanEmailContent(comm.content).substring(0, 100)}...
                                  </Text>
                                )}
                              </Flex>
                              
                              <Text size="1" color="gray" style={{ flexShrink: 0 }}>
                                {formatDate(comm.timestamp)}
                              </Text>
                            </Flex>
                          </Box>
                        </Flex>
                      </Box>
                      
                      {/* Expanded Content */}
                      {expandedItems.has(comm.id) && (
                        <Box style={{ padding: '1rem' }}>
                          {comm.toUsers && comm.toUsers.length > 0 && (
                            <Text size="1" color="gray" mb="2">
                              {comm.type === 'email' ? 'To: ' : 'Attendees: '}
                              {comm.toUsers.join(', ')}
                            </Text>
                          )}
                          
                          <Text size="2" style={{ 
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            overflowWrap: 'break-word'
                          }}>
                            {cleanEmailContent(comm.content)}
                          </Text>
                        </Box>
                      )}
                    </>
                  ) : (
                    /* Chat Message Style */
                    <Box style={{ padding: '0.75rem' }}>
                      <Flex gap="3">
                        <Box style={{ color: `var(--${getCommColor(comm.type)}-9)`, flexShrink: 0 }}>
                          {getCommIcon(comm.type)}
                        </Box>
                        <Box style={{ flex: 1, minWidth: 0 }}>
                          <Flex justify="between" mb="1">
                            <Text size="2" weight="bold">{comm.fromUser}</Text>
                            <Text size="1" color="gray">
                              {formatDate(comm.timestamp)}
                            </Text>
                          </Flex>
                          
                          <Text size="2" style={{ 
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            overflowWrap: 'break-word'
                          }}>
                            {comm.content}
                          </Text>
                        </Box>
                      </Flex>
                    </Box>
                  )}
                </Box>
              ))}
            </Flex>
          </ScrollArea>
        </Box>

        {filter !== 'email' && filter !== 'calendar_event' && (
          <Box style={{ borderTop: '1px solid var(--gray-4)', padding: '1rem', flexShrink: 0 }}>
            <Flex gap="2">
              <TextField.Root
                placeholder="Type a message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                style={{ flex: 1 }}
              />
              <Button onClick={sendMessage}>Send</Button>
            </Flex>
          </Box>
        )}
      </Flex>
    </Card>
  );
};

// Tasks Tab
const TasksTab = ({ clientId }: { clientId: string }) => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [showNewTaskDialog, setShowNewTaskDialog] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', description: '', priority: 'medium' });

  useEffect(() => {
    fetchTasks();
  }, [clientId]);

  const fetchTasks = async () => {
    try {
      const response = await api.get(`/clients/${clientId}/tasks`);
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const createTask = async () => {
    if (!newTask.title) return;
    
    try {
      await api.post(`/clients/${clientId}/tasks`, newTask);
      setShowNewTaskDialog(false);
      setNewTask({ title: '', description: '', priority: 'medium' });
      await fetchTasks();
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };

  const updateTaskStatus = async (taskId: string, newStatus: string) => {
    try {
      await api.put(`/clients/${clientId}/tasks/${taskId}/status`, null, {
        params: { status: newStatus }
      });
      await fetchTasks();
    } catch (error) {
      console.error('Error updating task status:', error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch(priority) {
      case 'urgent': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'blue';
      case 'low': return 'gray';
      default: return 'gray';
    }
  };

  const tasksByStatus = {
    todo: tasks.filter(t => t.status === 'todo'),
    in_progress: tasks.filter(t => t.status === 'in_progress'),
    completed: tasks.filter(t => t.status === 'completed')
  };

  return (
    <Box>
      <Flex justify="between" mb="4">
        <Heading size="4">Tasks</Heading>
        <Button size="2" onClick={() => setShowNewTaskDialog(true)}>
          <CheckCircledIcon /> New Task
        </Button>
      </Flex>
      
      <Box style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
        {/* To Do Column */}
        <Card>
          <Heading size="3" mb="3">To Do ({tasksByStatus.todo.length})</Heading>
          <Flex direction="column" gap="2">
            {tasksByStatus.todo.map(task => (
              <Card key={task.id} variant="surface" style={{ cursor: 'pointer' }}>
                <Flex direction="column" gap="2">
                  <Flex justify="between" align="start">
                    <Text size="2" weight="medium">{task.title}</Text>
                    <Badge size="1" color={getPriorityColor(task.priority)}>
                      {task.priority}
                    </Badge>
                  </Flex>
                  {task.description && (
                    <Text size="1" color="gray">{task.description}</Text>
                  )}
                  {task.dueDate && (
                    <Text size="1" color="gray">Due: {new Date(task.dueDate).toLocaleDateString()}</Text>
                  )}
                  <Flex gap="2" mt="2">
                    <Button
                      size="1"
                      variant="soft"
                      onClick={() => updateTaskStatus(task.id, 'in_progress')}
                    >
                      Start
                    </Button>
                  </Flex>
                </Flex>
              </Card>
            ))}
          </Flex>
        </Card>

        {/* In Progress Column */}
        <Card>
          <Heading size="3" mb="3">In Progress ({tasksByStatus.in_progress.length})</Heading>
          <Flex direction="column" gap="2">
            {tasksByStatus.in_progress.map(task => (
              <Card key={task.id} variant="surface">
                <Flex direction="column" gap="2">
                  <Flex justify="between" align="start">
                    <Text size="2" weight="medium">{task.title}</Text>
                    <Badge size="1" color={getPriorityColor(task.priority)}>
                      {task.priority}
                    </Badge>
                  </Flex>
                  {task.description && (
                    <Text size="1" color="gray">{task.description}</Text>
                  )}
                  <Flex gap="2" mt="2">
                    <Button
                      size="1"
                      variant="soft"
                      onClick={() => updateTaskStatus(task.id, 'todo')}
                    >
                      Back
                    </Button>
                    <Button
                      size="1"
                      variant="soft"
                      color="green"
                      onClick={() => updateTaskStatus(task.id, 'completed')}
                    >
                      Complete
                    </Button>
                  </Flex>
                </Flex>
              </Card>
            ))}
          </Flex>
        </Card>

        {/* Completed Column */}
        <Card>
          <Heading size="3" mb="3">Completed ({tasksByStatus.completed.length})</Heading>
          <Flex direction="column" gap="2">
            {tasksByStatus.completed.map(task => (
              <Card key={task.id} variant="surface" style={{ opacity: 0.7 }}>
                <Flex direction="column" gap="2">
                  <Text size="2" weight="medium" style={{ textDecoration: 'line-through' }}>
                    {task.title}
                  </Text>
                  <Flex gap="2" mt="2">
                    <Button
                      size="1"
                      variant="soft"
                      onClick={() => updateTaskStatus(task.id, 'todo')}
                    >
                      Reopen
                    </Button>
                  </Flex>
                </Flex>
              </Card>
            ))}
          </Flex>
        </Card>
      </Box>

      {/* New Task Dialog */}
      {showNewTaskDialog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <Card style={{ width: '400px', padding: '2rem' }}>
            <Heading size="4" mb="4">Create New Task</Heading>
            <Flex direction="column" gap="3">
              <TextField.Root
                placeholder="Task title"
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
              />
              <TextField.Root
                placeholder="Description (optional)"
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
              />
              <Flex gap="2">
                <label>Priority:</label>
                <select
                  value={newTask.priority}
                  onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                  style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--gray-6)' }}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </Flex>
              <Flex gap="2" justify="end">
                <Button variant="soft" onClick={() => setShowNewTaskDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={createTask}>
                  Create Task
                </Button>
              </Flex>
            </Flex>
          </Card>
        </div>
      )}
    </Box>
  );
};

// Documents Tab
const DocumentsTab = ({ clientId }: { clientId: string }) => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [driveDocuments, setDriveDocuments] = useState<any[]>([]);
  const [driveFolderLink, setDriveFolderLink] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [vectorizationStatus, setVectorizationStatus] = useState<any>(null);
  const [isVectorizing, setIsVectorizing] = useState(false);
  const [showVectorizeProgress, setShowVectorizeProgress] = useState(false);

  useEffect(() => {
    fetchDocuments();
    fetchDriveDocuments();
    fetchVectorizationStatus();
  }, [clientId]);

  const fetchDocuments = async () => {
    try {
      const response = await api.get(`/clients/${clientId}/documents`);
      // Separate local and Drive documents
      const allDocs = response.data;
      const localDocs = allDocs.filter((doc: any) => !doc.id.startsWith('gdrive_'));
      const gDriveDocs = allDocs.filter((doc: any) => doc.id.startsWith('gdrive_'));
      setDocuments(localDocs);
      setDriveDocuments(gDriveDocs);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchDriveDocuments = async () => {
    try {
      const response = await api.get(`/clients/${clientId}/drive-documents`);
      if (response.data.documents) {
        setDriveDocuments(response.data.documents);
      }
      if (response.data.folderLink) {
        setDriveFolderLink(response.data.folderLink);
      }
    } catch (error) {
      console.error('Error fetching Drive documents:', error);
    }
  };

  const fetchVectorizationStatus = async () => {
    try {
      const response = await api.get(`/clients/${clientId}/vectorization-status`);
      setVectorizationStatus(response.data);
    } catch (error) {
      console.error('Error fetching vectorization status:', error);
    }
  };

  const handleVectorizeDocuments = async () => {
    setIsVectorizing(true);
    setShowVectorizeProgress(true);
    
    try {
      await api.post(`/clients/${clientId}/process-documents`);
      
      // Poll for status updates
      const pollInterval = setInterval(async () => {
        try {
          const response = await api.get(`/clients/${clientId}/vectorization-status`);
          setVectorizationStatus(response.data);
          
          // Stop polling when all documents are processed
          if (response.data.summary.percentage_complete === 100) {
            clearInterval(pollInterval);
            setIsVectorizing(false);
            setTimeout(() => setShowVectorizeProgress(false), 3000);
          }
        } catch (error) {
          console.error('Error polling vectorization status:', error);
        }
      }, 2000); // Poll every 2 seconds
      
      // Stop polling after 5 minutes (safety measure)
      setTimeout(() => {
        clearInterval(pollInterval);
        setIsVectorizing(false);
      }, 300000);
      
    } catch (error) {
      console.error('Error starting vectorization:', error);
      setIsVectorizing(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', 'other');

    try {
      await api.post(`/clients/${clientId}/documents`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      await fetchDocuments();
    } catch (error) {
      console.error('Error uploading document:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = async (documentId: string, documentName: string) => {
    try {
      const response = await api.get(`/clients/${clientId}/documents/${documentId}/download`, {
        responseType: 'blob',
      });
      
      // Create a download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', documentName);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading document:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.includes('Google Doc')) return '📄';
    if (type.includes('Google Sheet')) return '📊';
    if (type.includes('Google Slides')) return '📊';
    if (type.includes('PDF')) return '📕';
    if (type.includes('Image')) return '🖼️';
    if (type.includes('Video')) return '🎥';
    return '📎';
  };

  const isDocumentVectorized = (docId: string) => {
    if (!vectorizationStatus) return false;
    const doc = vectorizationStatus.documents.find((d: any) => d.id === docId);
    return doc?.vectorized || false;
  };

  return (
    <Box>
      <Flex justify="between" mb="4">
        <Heading size="4">Documents</Heading>
        <Flex gap="2">
          {driveFolderLink && (
            <Button
              size="2"
              variant="soft"
              onClick={() => window.open(driveFolderLink, '_blank')}
            >
              <FileTextIcon /> Open Google Drive Folder
            </Button>
          )}
          <Button
            size="2"
            variant="soft"
            color="purple"
            onClick={handleVectorizeDocuments}
            disabled={isVectorizing || vectorizationStatus?.summary?.percentage_complete === 100}
          >
            {isVectorizing ? 'Vectorizing...' : 'Vectorize Documents'}
          </Button>
          <label htmlFor="file-upload">
            <div style={{ display: 'inline-block' }}>
              <Button size="2" disabled={isUploading} style={{ cursor: 'pointer' }}>
                <FileTextIcon /> {isUploading ? 'Uploading...' : 'Upload Document'}
              </Button>
            </div>
            <input
              id="file-upload"
              type="file"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              disabled={isUploading}
            />
          </label>
        </Flex>
      </Flex>

      {/* Vectorization Progress */}
      {showVectorizeProgress && vectorizationStatus && (
        <Card mb="4" variant="surface">
          <Flex direction="column" gap="2">
            <Flex justify="between" align="center">
              <Text size="2" weight="medium">
                Vectorization Progress
              </Text>
              <Text size="2" color="gray">
                {vectorizationStatus.summary.vectorized_count} / {vectorizationStatus.summary.total_documents} documents
              </Text>
            </Flex>
            <Box style={{ width: '100%', height: '8px', backgroundColor: 'var(--gray-4)', borderRadius: '4px', overflow: 'hidden' }}>
              <Box 
                style={{ 
                  width: `${vectorizationStatus.summary.percentage_complete}%`, 
                  height: '100%', 
                  backgroundColor: 'var(--purple-9)',
                  transition: 'width 0.3s ease'
                }}
              />
            </Box>
            {vectorizationStatus.summary.percentage_complete === 100 && (
              <Text size="2" color="green" weight="medium">
                ✓ All documents vectorized successfully!
              </Text>
            )}
          </Flex>
        </Card>
      )}
      
      {/* Google Drive Documents Section */}
      {driveDocuments.length > 0 && (
        <Box mb="4">
          <Heading size="3" mb="3">Google Drive Files</Heading>
          <Box style={{ display: 'grid', gap: '0.5rem' }}>
            {driveDocuments.map((doc) => (
              <Card key={doc.id} variant="surface">
                <Flex justify="between" align="center">
                  <Flex align="center" gap="3">
                    <Text size="4">{getFileIcon(doc.type)}</Text>
                    <Box>
                      <Flex align="center" gap="2">
                        <Text size="2" weight="medium">{doc.name}</Text>
                        {isDocumentVectorized(doc.id) && (
                          <Badge size="1" color="purple" variant="soft">
                            Vectorized
                          </Badge>
                        )}
                      </Flex>
                      <Text size="1" color="gray">
                        {doc.type} • {formatFileSize(doc.size || 0)} • 
                        {' ' + new Date(doc.modifiedTime || doc.uploadedAt).toLocaleDateString()}
                      </Text>
                    </Box>
                  </Flex>
                  <Button
                    size="1"
                    variant="soft"
                    onClick={() => window.open(doc.webViewLink, '_blank')}
                  >
                    Open
                  </Button>
                </Flex>
              </Card>
            ))}
          </Box>
        </Box>
      )}
      
      {/* Local Documents Section */}
      {documents.length > 0 && (
        <Box>
          <Heading size="3" mb="3">Uploaded Files</Heading>
          <Box style={{ display: 'grid', gap: '0.5rem' }}>
            {documents.map((doc) => (
              <Card key={doc.id} variant="surface">
                <Flex justify="between" align="center">
                  <Flex align="center" gap="3">
                    <FileTextIcon style={{ width: '24px', height: '24px', color: 'var(--accent-9)' }} />
                    <Box>
                      <Text size="2" weight="medium">{doc.name}</Text>
                      <Text size="1" color="gray">
                        {formatFileSize(doc.fileSize || 0)} • Version {doc.version} • 
                        {' ' + new Date(doc.uploadedAt).toLocaleDateString()}
                      </Text>
                    </Box>
                  </Flex>
                  <Button
                    size="1"
                    variant="soft"
                    onClick={() => handleDownload(doc.id, doc.name)}
                  >
                    Download
                  </Button>
                </Flex>
              </Card>
            ))}
          </Box>
        </Box>
      )}
      
      {documents.length === 0 && driveDocuments.length === 0 && (
        <Card>
          <Text size="2" color="gray">No documents yet</Text>
        </Card>
      )}
    </Box>
  );
};

// Team Tab
const TeamTab = ({ clientId }: { clientId: string }) => {
  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [showAddMemberDialog, setShowAddMemberDialog] = useState(false);
  const [newMember, setNewMember] = useState({
    user_id: '',
    role: 'member',
    can_view_financials: false,
    can_edit_tasks: true,
    can_upload_documents: true
  });

  useEffect(() => {
    fetchTeamMembers();
    fetchUsers();
  }, [clientId]);

  const fetchTeamMembers = async () => {
    try {
      const response = await api.get(`/clients/${clientId}/team-members`);
      setTeamMembers(response.data);
    } catch (error) {
      console.error('Error fetching team members:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      // This would need an endpoint to get all users
      // For now, we'll use a placeholder
      setUsers([]);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const addTeamMember = async () => {
    if (!newMember.user_id) return;
    
    try {
      await api.post(`/clients/${clientId}/team-members`, newMember);
      setShowAddMemberDialog(false);
      setNewMember({
        user_id: '',
        role: 'member',
        can_view_financials: false,
        can_edit_tasks: true,
        can_upload_documents: true
      });
      await fetchTeamMembers();
    } catch (error) {
      console.error('Error adding team member:', error);
    }
  };

  const removeTeamMember = async (memberId: string) => {
    if (confirm('Are you sure you want to remove this team member?')) {
      try {
        await api.delete(`/clients/${clientId}/team-members/${memberId}`);
        await fetchTeamMembers();
      } catch (error) {
        console.error('Error removing team member:', error);
      }
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch(role) {
      case 'account_manager': return 'purple';
      case 'project_lead': return 'blue';
      case 'developer': return 'green';
      case 'designer': return 'orange';
      default: return 'gray';
    }
  };

  return (
    <Box>
      <Flex justify="between" mb="4">
        <Heading size="4">Team Members</Heading>
        <Button size="2" onClick={() => setShowAddMemberDialog(true)}>
          <PersonIcon /> Add Team Member
        </Button>
      </Flex>
      
      <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
        {teamMembers.map((member) => (
          <Card key={member.id}>
            <Flex direction="column" gap="3">
              <Flex justify="between" align="start">
                <Flex align="center" gap="2">
                  <Avatar
                    size="3"
                    fallback={member.email?.charAt(0) || 'U'}
                    variant="solid"
                  />
                  <Box>
                    <Text size="2" weight="medium">{member.email}</Text>
                    <Badge size="1" color={getRoleBadgeColor(member.role)}>
                      {member.role.replace('_', ' ')}
                    </Badge>
                  </Box>
                </Flex>
                <IconButton
                  size="1"
                  variant="ghost"
                  color="red"
                  onClick={() => removeTeamMember(member.id)}
                >
                  ×
                </IconButton>
              </Flex>
              
              <Box>
                <Text size="1" weight="medium" mb="1">Permissions:</Text>
                <Flex direction="column" gap="1">
                  <Text size="1" color={member.can_view_financials ? 'green' : 'gray'}>
                    {member.can_view_financials ? '✓' : '×'} View Financials
                  </Text>
                  <Text size="1" color={member.can_edit_tasks ? 'green' : 'gray'}>
                    {member.can_edit_tasks ? '✓' : '×'} Edit Tasks
                  </Text>
                  <Text size="1" color={member.can_upload_documents ? 'green' : 'gray'}>
                    {member.can_upload_documents ? '✓' : '×'} Upload Documents
                  </Text>
                </Flex>
              </Box>
              
              <Text size="1" color="gray">
                Added {new Date(member.added_date).toLocaleDateString()}
              </Text>
            </Flex>
          </Card>
        ))}
      </Box>

      {teamMembers.length === 0 && (
        <Card style={{ textAlign: 'center', padding: '2rem' }}>
          <Text size="2" color="gray">No team members assigned yet</Text>
        </Card>
      )}

      {/* Add Team Member Dialog */}
      {showAddMemberDialog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <Card style={{ width: '400px', padding: '2rem' }}>
            <Heading size="4" mb="4">Add Team Member</Heading>
            <Flex direction="column" gap="3">
              <TextField.Root
                placeholder="Enter user email or ID"
                value={newMember.user_id}
                onChange={(e) => setNewMember({ ...newMember, user_id: e.target.value })}
              />
              
              <Flex gap="2">
                <label>Role:</label>
                <select
                  value={newMember.role}
                  onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                  style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--gray-6)' }}
                >
                  <option value="member">Member</option>
                  <option value="account_manager">Account Manager</option>
                  <option value="project_lead">Project Lead</option>
                  <option value="developer">Developer</option>
                  <option value="designer">Designer</option>
                </select>
              </Flex>
              
              <Box>
                <Text size="2" weight="medium" mb="2">Permissions:</Text>
                <Flex direction="column" gap="2">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                      type="checkbox"
                      checked={newMember.can_view_financials}
                      onChange={(e) => setNewMember({ ...newMember, can_view_financials: e.target.checked })}
                    />
                    View Financials
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                      type="checkbox"
                      checked={newMember.can_edit_tasks}
                      onChange={(e) => setNewMember({ ...newMember, can_edit_tasks: e.target.checked })}
                    />
                    Edit Tasks
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                      type="checkbox"
                      checked={newMember.can_upload_documents}
                      onChange={(e) => setNewMember({ ...newMember, can_upload_documents: e.target.checked })}
                    />
                    Upload Documents
                  </label>
                </Flex>
              </Box>
              
              <Flex gap="2" justify="end">
                <Button variant="soft" onClick={() => setShowAddMemberDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={addTeamMember}>
                  Add Member
                </Button>
              </Flex>
            </Flex>
          </Card>
        </div>
      )}
    </Box>
  );
};

// Meeting Transcripts Tab
const MeetingTranscriptsContent = ({ clientId, clientName }: { clientId: string; clientName: string }) => {
  // clientId will be used for API calls in the future
  console.log('Meeting transcripts for client:', clientId);
  
  const mockTranscripts = [
    {
      id: '1',
      title: 'Q4 Strategy Review',
      date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
      duration: '45 min',
      attendees: ['John Smith', 'Sarah Johnson', 'Mike Chen'],
      keyTopics: ['Budget allocation', 'Q1 roadmap', 'Team expansion'],
      actionItems: 3,
      sentiment: 'positive'
    },
    {
      id: '2',
      title: 'Product Demo & Feedback Session',
      date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 1 week ago
      duration: '1h 15min',
      attendees: ['John Smith', 'Emily Davis', 'Tech Team'],
      keyTopics: ['Feature requests', 'UI improvements', 'Integration needs'],
      actionItems: 5,
      sentiment: 'neutral'
    },
    {
      id: '3',
      title: 'Weekly Sync-up',
      date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000), // 2 weeks ago
      duration: '30 min',
      attendees: ['John Smith', 'Sarah Johnson'],
      keyTopics: ['Progress update', 'Blockers', 'Next steps'],
      actionItems: 2,
      sentiment: 'positive'
    }
  ];

  const getSentimentColor = (sentiment: string) => {
    switch(sentiment) {
      case 'positive': return 'green';
      case 'negative': return 'red';
      default: return 'gray';
    }
  };

  return (
    <Box>
      <Flex justify="between" mb="4">
        <Box>
          <Heading size="4">Meeting Transcripts</Heading>
          <Text size="2" color="gray" mt="1">
            AI-powered meeting summaries and insights
          </Text>
        </Box>
        <Flex gap="2">
          <Button size="2" variant="soft" disabled>
            <CalendarIcon /> Schedule Meeting
          </Button>
          <Button size="2" variant="soft" disabled>
            Upload Recording
          </Button>
        </Flex>
      </Flex>

      <Box style={{ display: 'grid', gap: '1rem' }}>
        {mockTranscripts.map((transcript) => (
          <Card key={transcript.id}>
            <Flex direction="column" gap="3">
              <Flex justify="between" align="start">
                <Box>
                  <Flex align="center" gap="2" mb="1">
                    <Heading size="3">{transcript.title}</Heading>
                    <Badge size="1" color={getSentimentColor(transcript.sentiment)}>
                      {transcript.sentiment}
                    </Badge>
                  </Flex>
                  <Flex gap="3" align="center">
                    <Text size="2" color="gray">
                      <CalendarIcon style={{ display: 'inline', marginRight: '4px' }} />
                      {transcript.date.toLocaleDateString()}
                    </Text>
                    <Text size="2" color="gray">
                      <ClockIcon style={{ display: 'inline', marginRight: '4px' }} />
                      {transcript.duration}
                    </Text>
                    <Text size="2" color="gray">
                      <PersonIcon style={{ display: 'inline', marginRight: '4px' }} />
                      {transcript.attendees.length} attendees
                    </Text>
                  </Flex>
                </Box>
                <Button size="1" variant="soft">
                  View Full Transcript
                </Button>
              </Flex>

              <Box>
                <Text size="2" weight="medium" mb="1">Key Topics Discussed:</Text>
                <Flex gap="2" wrap="wrap">
                  {transcript.keyTopics.map((topic, i) => (
                    <Badge key={i} variant="soft" color="blue">
                      {topic}
                    </Badge>
                  ))}
                </Flex>
              </Box>

              <Flex justify="between" align="center">
                <Text size="2" color="gray">
                  Attendees: {transcript.attendees.join(', ')}
                </Text>
                <Badge color="orange" variant="soft">
                  {transcript.actionItems} Action Items
                </Badge>
              </Flex>
            </Flex>
          </Card>
        ))}
      </Box>

      <Card mt="4" style={{ backgroundColor: 'var(--gray-2)' }}>
        <Flex align="center" gap="3">
          <InfoCircledIcon color="blue" />
          <Text size="2" color="gray">
            Meeting transcripts are automatically generated from your calendar events and uploaded recordings. 
            Connect your calendar or upload audio files to get started.
          </Text>
        </Flex>
      </Card>
    </Box>
  );
};

// Industry Pulse Tab
const IndustryPulseContent = ({ clientId, clientName }: { clientId: string; clientName: string }) => {
  // Log clientId for future API integration
  console.log('Industry Pulse for client:', clientId);
  
  const mockIndustryData = {
    industry: 'Technology / SaaS',
    lastUpdated: new Date(),
    trends: [
      {
        id: '1',
        title: 'AI Integration Becoming Standard',
        impact: 'high',
        description: 'Major competitors are rapidly integrating AI features into their core offerings.',
        relevance: 95,
        source: 'Industry Report Q4 2024'
      },
      {
        id: '2',
        title: 'Shift to Usage-Based Pricing',
        impact: 'medium',
        description: 'Industry moving away from seat-based to consumption-based pricing models.',
        relevance: 78,
        source: 'Market Analysis'
      },
      {
        id: '3',
        title: 'Increased Focus on Security Compliance',
        impact: 'high',
        description: 'New regulations requiring enhanced data protection measures by Q2 2025.',
        relevance: 88,
        source: 'Regulatory Update'
      }
    ],
    competitors: [
      { name: 'CompetitorA', marketShare: 28, growth: '+12%', status: 'growing' },
      { name: 'CompetitorB', marketShare: 22, growth: '+5%', status: 'stable' },
      { name: 'CompetitorC', marketShare: 15, growth: '-3%', status: 'declining' }
    ],
    opportunities: [
      'Expand AI capabilities to match market expectations',
      'Consider flexible pricing model transition',
      'Strengthen security certifications before Q2'
    ],
    risks: [
      'Falling behind in AI feature parity',
      'Customer churn due to pricing model preferences',
      'Compliance gaps with upcoming regulations'
    ]
  };

  const getImpactColor = (impact: string) => {
    switch(impact) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'gray';
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'growing': return 'green';
      case 'declining': return 'red';
      default: return 'gray';
    }
  };

  return (
    <Box>
      <Flex justify="between" align="center" mb="4">
        <Box>
          <Heading size="4">Industry Pulse</Heading>
          <Text size="2" color="gray" mt="1">
            Real-time industry insights and competitive intelligence for {clientName}
          </Text>
        </Box>
        <Flex align="center" gap="3">
          <Badge size="2" variant="soft">
            {mockIndustryData.industry}
          </Badge>
          <Text size="1" color="gray">
            Updated {mockIndustryData.lastUpdated.toLocaleDateString()}
          </Text>
        </Flex>
      </Flex>

      {/* Key Trends */}
      <Card mb="4">
        <Heading size="3" mb="3">Key Industry Trends</Heading>
        <Flex direction="column" gap="3">
          {mockIndustryData.trends.map((trend) => (
            <Box key={trend.id} style={{ borderLeft: '3px solid var(--accent-9)', paddingLeft: '1rem' }}>
              <Flex justify="between" align="start" mb="1">
                <Flex align="center" gap="2">
                  <Text weight="medium">{trend.title}</Text>
                  <Badge size="1" color={getImpactColor(trend.impact)}>
                    {trend.impact} impact
                  </Badge>
                </Flex>
                <Text size="1" color="gray">{trend.relevance}% relevant</Text>
              </Flex>
              <Text size="2" color="gray" mb="1">{trend.description}</Text>
              <Text size="1" color="gray">Source: {trend.source}</Text>
            </Box>
          ))}
        </Flex>
      </Card>

      {/* Competitive Landscape */}
      <Box style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }} mb="4">
        <Card>
          <Heading size="3" mb="3">Competitive Landscape</Heading>
          <Flex direction="column" gap="2">
            {mockIndustryData.competitors.map((comp, i) => (
              <Flex key={i} justify="between" align="center" style={{ padding: '0.5rem 0' }}>
                <Flex align="center" gap="2">
                  <Text weight="medium">{comp.name}</Text>
                  <Badge size="1" color={getStatusColor(comp.status)} variant="soft">
                    {comp.growth}
                  </Badge>
                </Flex>
                <Text size="2" color="gray">{comp.marketShare}% market share</Text>
              </Flex>
            ))}
          </Flex>
          <Box mt="3" style={{ height: '8px', backgroundColor: 'var(--gray-4)', borderRadius: '4px' }}>
            <Box style={{ 
              width: `${mockIndustryData.competitors[0].marketShare}%`, 
              height: '100%', 
              backgroundColor: 'var(--accent-9)',
              borderRadius: '4px'
            }} />
          </Box>
          <Text size="1" color="gray" mt="1">Market leader share</Text>
        </Card>

        <Card>
          <Heading size="3" mb="3">Strategic Insights</Heading>
          <Box mb="3">
            <Text size="2" weight="medium" color="green" mb="2">
              <RocketIcon style={{ display: 'inline', marginRight: '4px' }} />
              Opportunities
            </Text>
            <Flex direction="column" gap="1">
              {mockIndustryData.opportunities.map((opp, i) => (
                <Text key={i} size="2" style={{ paddingLeft: '1rem' }}>
                  • {opp}
                </Text>
              ))}
            </Flex>
          </Box>
          
          <Box>
            <Text size="2" weight="medium" color="red" mb="2">
              <ExclamationTriangleIcon style={{ display: 'inline', marginRight: '4px' }} />
              Risks to Monitor
            </Text>
            <Flex direction="column" gap="1">
              {mockIndustryData.risks.map((risk, i) => (
                <Text key={i} size="2" style={{ paddingLeft: '1rem' }}>
                  • {risk}
                </Text>
              ))}
            </Flex>
          </Box>
        </Card>
      </Box>

      {/* AI Recommendations */}
      <Card style={{ backgroundColor: 'var(--accent-2)' }}>
        <Flex align="start" gap="3">
          <LightningBoltIcon color="purple" style={{ marginTop: '2px' }} />
          <Box>
            <Text size="2" weight="medium" mb="1">AI Recommendations for {clientName}</Text>
            <Text size="2">
              Based on current industry trends and competitive analysis, consider prioritizing AI feature development 
              in Q1 2025 to maintain competitive parity. The shift to usage-based pricing presents an opportunity 
              to increase revenue from power users while attracting smaller customers.
            </Text>
          </Box>
        </Flex>
      </Card>
    </Box>
  );
};

export default ClientDetail; 