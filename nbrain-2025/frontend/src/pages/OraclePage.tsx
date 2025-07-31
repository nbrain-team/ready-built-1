import React, { useState, useEffect } from 'react';
import { Box, Heading, Text, Card, Flex, Button, Tabs, Badge, TextField, ScrollArea, Dialog, Separator, IconButton, Grid, AlertDialog, TextArea } from '@radix-ui/themes';
import { MagnifyingGlassIcon, EnvelopeClosedIcon, CalendarIcon, FileTextIcon, ReloadIcon, CheckCircledIcon, ExclamationTriangleIcon, LightningBoltIcon, SpeakerLoudIcon, ChevronRightIcon, PlusIcon, TrashIcon, ClipboardIcon, CheckIcon, PaperPlaneIcon } from '@radix-ui/react-icons';
import api from '../api';
// import EmailDetailDialog from '../components/EmailDetailDialog';
import { AudioRecorder } from '../components/AudioRecorder';
import { RecordingsList } from '../components/RecordingsList';

interface Email {
  id: string;
  subject: string;
  from: string;
  to: string[];
  date: string;
  snippet: string;
  thread_id: string;
  content?: string;
}

interface ActionItem {
  id: string;
  title: string;
  source: string;
  sourceType: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'completed' | 'converted';
  createdAt: string;
  dueDate?: string;
  category: string;
  context: string;
  metaData?: {
    subject?: string;
    date?: string;
    from_email?: string;
    to_email?: string;
    thread_id?: string;
    description?: string;
    emailContent?: string;
    body?: string;
    [key: string]: any;
  };
}

interface Task {
  id: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  dueDate?: string;
  category: string;
  createdAt: string;
}

interface SentimentData {
  current_sentiment: {
    sentiment: string;
    confidence: number;
  };
  trend: string;
  concerns: string[];
  positive_aspects: string[];
}

interface SuggestedTask {
  title: string;
  priority: string;
  reason: string;
  estimated_time?: string;
  source?: string;
  context?: string;
  related_emails?: string[];
  metadata?: {
    [key: string]: any;
  };
}

const OraclePage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [emails, setEmails] = useState<Email[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  const [suggestedTasks, setSuggestedTasks] = useState<SuggestedTask[]>([]);
  const [activeTab, setActiveTab] = useState('communications');
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [needsEmailConnection, setNeedsEmailConnection] = useState(false);
  const [showRecordingDialog, setShowRecordingDialog] = useState(false);
  const [deleteConfirmItem, setDeleteConfirmItem] = useState<ActionItem | null>(null);
  const [deleteConfirmEmail, setDeleteConfirmEmail] = useState<Email | null>(null);
  
  // Add state for expanded items
  const [expandedActionItems, setExpandedActionItems] = useState<Set<string>>(new Set());
  const [expandedSuggestedTasks, setExpandedSuggestedTasks] = useState<Set<number>>(new Set());
  
  // Add state for suggested responses
  const [suggestedResponses, setSuggestedResponses] = useState<{ [key: string]: string }>({});

  // Fetch initial data
  useEffect(() => {
    fetchEmails();
    fetchActionItems();
    fetchSentiment();
    fetchSuggestedTasks();
    fetchTasks();
  }, []);

  const fetchEmails = async () => {
    try {
      const response = await api.get('/api/oracle/emails');
      setEmails(response.data || []);
    } catch (error: any) {
      console.error('Error fetching emails:', error);
      // Handle 503 error specifically - table not initialized
      if (error.response?.status === 503) {
        setNeedsEmailConnection(true);
        setEmails([]);
      }
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await api.get('/api/oracle/tasks');
      setTasks(response.data || []);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const syncEmailsAndCalendar = async () => {
    setIsLoading(true);
    try {
      // First check if user has connected their email
      const sourcesResponse = await api.get('/api/oracle/sources');
      const emailSource = sourcesResponse.data.find((source: any) => source.type === 'email');
      
      if (!emailSource || emailSource.status !== 'connected') {
        // User needs to connect email first - get OAuth URL
        const connectResponse = await api.post('/api/oracle/connect/email');
        if (connectResponse.data.authUrl) {
          // Redirect to Google OAuth
          window.location.href = connectResponse.data.authUrl;
          return;
        }
      }
      
      // If connected, sync emails
      await api.post('/api/oracle/sync/email');
      // Sync calendar
      await api.post('/api/oracle/sync/calendar');
      // Refresh emails list
      await fetchEmails();
      // Refresh other data
      await fetchActionItems();
      await fetchTasks();
    } catch (error: any) {
      console.error('Error syncing:', error);
      // If sync fails with 400, it means user needs to connect
      if (error.response?.status === 400) {
        try {
          const connectResponse = await api.post('/api/oracle/connect/email');
          if (connectResponse.data.authUrl) {
            window.location.href = connectResponse.data.authUrl;
          }
        } catch (connectError) {
          console.error('Error getting auth URL:', connectError);
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchActionItems = async () => {
    try {
      const response = await api.get('/api/oracle/action-items');
      setActionItems(response.data || []);
    } catch (error) {
      console.error('Error fetching action items:', error);
    }
  };

  const generateActionItems = async () => {
    setIsLoading(true);
    try {
      const response = await api.post('/api/oracle/generate-action-items');
      if (response.data.action_items_count > 0) {
        await fetchActionItems();
      } else if (response.data.message.includes('connect your email')) {
        // User needs to connect email first
        alert('Please connect your email first by clicking "Sync Email & Calendar"');
      }
    } catch (error: any) {
      console.error('Error generating action items:', error);
      if (error.response?.data?.message?.includes('connect your email')) {
        alert('Please connect your email first by clicking "Sync Email & Calendar"');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSentiment = async () => {
    try {
      const response = await api.get('/api/oracle/sentiment');
      setSentimentData(response.data);
    } catch (error) {
      console.error('Error fetching sentiment:', error);
    }
  };

  const generateSentiment = async () => {
    setIsLoading(true);
    try {
      await api.post('/api/oracle/generate-sentiment');
      await fetchSentiment();
    } catch (error) {
      console.error('Error generating sentiment:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSuggestedTasks = async () => {
    try {
      const response = await api.get('/api/oracle/suggested-tasks');
      setSuggestedTasks(response.data || []);
    } catch (error) {
      console.error('Error fetching suggested tasks:', error);
    }
  };

  const generateSuggestedTasks = async () => {
    setIsLoading(true);
    try {
      await api.post('/api/oracle/generate-suggested-tasks');
      await fetchSuggestedTasks();
    } catch (error) {
      console.error('Error generating suggested tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const response = await api.post('/api/oracle/search', {
        query: searchQuery
      });
      // Handle search results - could filter emails or show in a dialog
      console.log('Search results:', response.data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const deleteActionItem = async (item: ActionItem) => {
    try {
      await api.delete(`/api/oracle/action-items/${item.id}`);
      setActionItems(actionItems.filter(i => i.id !== item.id));
      setDeleteConfirmItem(null);
    } catch (error) {
      console.error('Error deleting action item:', error);
    }
  };

  const deleteEmail = async (email: Email) => {
    try {
      await api.delete(`/api/oracle/emails/${email.thread_id || email.id}`);
      setEmails(emails.filter(e => e.id !== email.id));
      setDeleteConfirmEmail(null);
    } catch (error) {
      console.error('Error deleting email:', error);
    }
  };

  const convertToTask = async (itemId: string) => {
    try {
      const response = await api.post(`/api/oracle/action-items/${itemId}/convert-to-task`);
      
      // Update the action item status
      setActionItems(actionItems.map(i => 
        i.id === itemId ? { ...i, status: 'converted' as const } : i
      ));
      
      // Refresh tasks
      await fetchTasks();
      
      // Show success message (you could add a toast notification here)
      console.log('Task created:', response.data);
    } catch (error) {
      console.error('Error converting to task:', error);
    }
  };

  const fetchFullEmail = async (threadId: string) => {
    try {
      const response = await api.get(`/api/oracle/emails/${threadId}/full`);
      setSelectedEmail(response.data);
      setShowEmailDialog(true);
    } catch (error) {
      console.error('Error fetching full email:', error);
    }
  };

  const toggleActionItemStatus = async (itemId: string) => {
    try {
      const item = actionItems.find(i => i.id === itemId);
      if (!item) return;

      const newStatus = item.status === 'completed' ? 'pending' : 'completed';
      await api.put(`/api/oracle/action-items/${itemId}`, { status: newStatus });
      
      setActionItems(actionItems.map(i => 
        i.id === itemId ? { ...i, status: newStatus } : i
      ));
    } catch (error) {
      console.error('Error updating action item:', error);
    }
  };

  const markActionItemComplete = async (itemId: string) => {
    try {
      await api.post(`/api/oracle/action-items/${itemId}/mark-complete`);
      setActionItems(actionItems.map(i => 
        i.id === itemId ? { ...i, status: 'completed' as const } : i
      ));
      // Refresh tasks
      await fetchTasks();
    } catch (error) {
      console.error('Error marking action item complete:', error);
    }
  };

  const getSuggestedResponse = async (itemId: string) => {
    setSuggestedResponses(prev => ({
      ...prev,
      [itemId]: 'Loading...'
    }));
    try {
      const response = await api.post(`/api/oracle/action-items/${itemId}/get-suggested-response`);
      setSuggestedResponses(prev => ({
        ...prev,
        [itemId]: response.data.suggested_response
      }));
    } catch (error) {
      console.error('Error getting suggested response:', error);
      setSuggestedResponses(prev => ({
        ...prev,
        [itemId]: 'Failed to generate response.'
      }));
    }
  };

  const sendEmailReply = async (item: ActionItem, response: string) => {
    if (!item.metaData?.thread_id || !item.metaData?.from_email) {
      alert('Cannot send reply: Missing email thread ID or sender.');
      return;
    }

    try {
      await api.post('/api/oracle/send-email-reply', {
        thread_id: item.metaData.thread_id,
        from_email: item.metaData.from_email,
        reply_content: response
      });
      alert('Reply sent successfully!');
      // Refresh emails list to show new replies
      await fetchEmails();
    } catch (error: any) {
      console.error('Error sending email reply:', error);
      alert('Failed to send reply. Please try again.');
    }
  };

  // Add toggle functions for expanding items
  const toggleActionItemExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedActionItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedActionItems(newExpanded);
  };

  const toggleSuggestedTaskExpanded = (index: number) => {
    const newExpanded = new Set(expandedSuggestedTasks);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSuggestedTasks(newExpanded);
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'green';
      case 'negative': return 'red';
      case 'neutral': return 'gray';
      default: return 'gray';
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <Flex justify="between" align="center">
          <Box>
            <Heading size="7" style={{ color: 'var(--gray-12)' }}>The Oracle</Heading>
            <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
              Your all-knowing AI assistant that captures and understands everything
            </Text>
          </Box>
          <Button 
            size="3" 
            variant="soft"
            onClick={() => setShowRecordingDialog(true)}
          >
            <SpeakerLoudIcon /> Record Meeting
          </Button>
        </Flex>
      </div>

      {/* Recording Dialog */}
      <Dialog.Root open={showRecordingDialog} onOpenChange={setShowRecordingDialog}>
        <Dialog.Content style={{ maxWidth: '850px' }}>
          <Dialog.Title>Record Meeting or Call</Dialog.Title>
          <Dialog.Description>
            Start recording to capture meeting notes, action items, and recommendations.
          </Dialog.Description>
          
          <Box mt="4">
            <AudioRecorder
              context="oracle"
              onSave={(recording) => {
                console.log('Recording saved:', recording);
                setShowRecordingDialog(false);
                // Refresh action items and data
                fetchActionItems();
                fetchSuggestedTasks();
              }}
            />
          </Box>
          
          {/* Show past recordings */}
          <Box mt="6">
            <Separator size="4" mb="4" />
            <RecordingsList 
              context="oracle"
              onPlayRecording={(recordingId) => {
                // Open audio in new tab or handle playback
                window.open(`/api/recordings/${recordingId}/audio`, '_blank');
              }}
            />
          </Box>
        </Dialog.Content>
      </Dialog.Root>

      <div className="page-content">
        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
          <Tabs.List style={{ marginBottom: '20px' }}>
            <Tabs.Trigger value="communications">
              Communications
              <Badge color="gray" ml="2">{emails.length}</Badge>
            </Tabs.Trigger>
            <Tabs.Trigger value="action-items">
              Action Items
              {actionItems.filter(a => a.status === 'pending').length > 0 && (
                <Badge color="red" ml="2">{actionItems.filter(a => a.status === 'pending').length}</Badge>
              )}
            </Tabs.Trigger>
            <Tabs.Trigger value="tasks">
              Tasks
              <Badge color="blue" ml="2">{tasks.filter(t => t.status === 'pending').length}</Badge>
            </Tabs.Trigger>
            <Tabs.Trigger value="recordings">
              Recordings
            </Tabs.Trigger>
            <Tabs.Trigger value="sentiment">Sentiment</Tabs.Trigger>
            <Tabs.Trigger value="suggested-tasks">Suggested Tasks</Tabs.Trigger>
          </Tabs.List>

          {/* Communications Tab */}
          <Tabs.Content value="communications">
            <Card>
              <Flex direction="column" gap="4">
                {/* Search and Sync */}
                <Flex justify="between" align="center">
                  <Flex gap="2" style={{ flex: 1 }}>
                    <TextField.Root
                      placeholder="Search emails or ask a question..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                      style={{ flex: 1 }}
                      size="3"
                    />
                    <Button 
                      onClick={handleSearch} 
                      disabled={isSearching}
                      size="3"
                    >
                      {isSearching ? <ReloadIcon className="animate-spin" /> : <MagnifyingGlassIcon />}
                      Search
                    </Button>
                  </Flex>
                  <Button 
                    onClick={syncEmailsAndCalendar}
                    disabled={isLoading}
                    variant="soft"
                    size="3"
                    ml="3"
                  >
                    <ReloadIcon className={isLoading ? "animate-spin" : ""} />
                    Sync Email & Calendar
                  </Button>
                </Flex>

                {/* Email List */}
                <ScrollArea style={{ height: '500px' }}>
                  <Flex direction="column" gap="2">
                    {needsEmailConnection ? (
                      <Card variant="surface" style={{ textAlign: "center", padding: "3rem" }}>
                        <Text size="3" color="gray">
                          Email integration not set up. Please go to your{" "}
                          <a href="/profile" style={{ color: "var(--blue-9)", textDecoration: "underline" }}>
                            Profile page
                          </a>{" "}
                          and connect your Gmail account first.
                        </Text>
                      </Card>
                    ) : emails.length === 0 ? (
                      <Card variant="surface" style={{ textAlign: 'center', padding: '3rem' }}>
                        <Text size="3" color="gray" style={{ display: 'block', marginBottom: '1rem' }}>
                          No emails found. Make sure to:
                        </Text>
                        <Text size="2" color="gray" style={{ display: 'block', lineHeight: '1.8' }}>
                          1. Create a label called "nBrain+Priority" or "nBrain Priority" in Gmail<br/>
                          2. Apply this label to emails you want Oracle to analyze<br/>
                          3. Click "Sync Email & Calendar" to fetch labeled emails
                        </Text>
                        <Text size="1" color="gray" style={{ display: 'block', marginTop: '1rem' }}>
                          Only emails with the "nBrain+Priority" or "nBrain Priority" label will be synced for privacy.
                        </Text>
                        <Button 
                          size="2" 
                          variant="soft"
                          color="blue"
                          style={{ marginTop: '1.5rem' }}
                          onClick={async () => {
                            setIsLoading(true);
                            try {
                              const response = await api.post('/api/oracle/sync/email-no-label');
                              if (response.data.emails_processed > 0) {
                                await fetchEmails();
                              }
                              alert(`Synced ${response.data.emails_processed} recent emails. For privacy, please create a 'nBrain Priority' label in Gmail for future syncs.`);
                            } catch (error) {
                              console.error('Error syncing emails:', error);
                              alert('Failed to sync emails. Please try again.');
                            } finally {
                              setIsLoading(false);
                            }
                          }}
                          disabled={isLoading}
                        >
                          {isLoading ? <ReloadIcon className="animate-spin" /> : null}
                          Sync Recent Emails (One Time)
                        </Button>
                      </Card>
                    ) : (
                      emails.sort((a, b) => {
                        // Sort by date descending (newest first)
                        const dateA = new Date(a.date).getTime();
                        const dateB = new Date(b.date).getTime();
                        return dateB - dateA;
                      }).map((email) => (
                        <Card 
                          key={email.id} 
                          variant="surface" 
                          style={{ cursor: 'pointer' }}
                        >
                          <Flex direction="column" gap="2">
                            <Flex justify="between" align="start">
                              <Box 
                                style={{ flex: 1, marginRight: '1rem', cursor: 'pointer' }}
                                onClick={() => {
                                  setSelectedEmail(email);
                                  setShowEmailDialog(true);
                                }}
                              >
                                <Text weight="bold" size="2" style={{ wordBreak: 'break-word' }}>
                                  {email.subject || 'No Subject'}
                                </Text>
                              </Box>
                              <Flex gap="2" align="center">
                                <Text size="1" color="gray" style={{ whiteSpace: 'nowrap' }}>
                                  {new Date(email.date).toLocaleString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: 'numeric',
                                    minute: '2-digit',
                                    hour12: true
                                  })}
                                </Text>
                                <IconButton
                                  size="1"
                                  variant="ghost"
                                  color="red"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setDeleteConfirmEmail(email);
                                  }}
                                >
                                  <TrashIcon />
                                </IconButton>
                              </Flex>
                            </Flex>
                            <Box
                              onClick={() => {
                                setSelectedEmail(email);
                                setShowEmailDialog(true);
                              }}
                              style={{ cursor: 'pointer' }}
                            >
                              <Flex gap="2" align="center" style={{ flexWrap: 'wrap' }}>
                                <Badge color="blue" variant="soft">From: {email.from}</Badge>
                                {email.to && email.to.length > 0 && (
                                  <Badge color="green" variant="soft">To: {email.to[0]}</Badge>
                                )}
                              </Flex>
                              <Text size="1" color="gray" style={{ 
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                marginTop: '0.5rem'
                              }}>
                                {email.snippet}
                              </Text>
                            </Box>
                          </Flex>
                        </Card>
                      ))
                    )}
                  </Flex>
                </ScrollArea>
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Action Items Tab */}
          <Tabs.Content value="action-items">
            <Card>
              <Flex direction="column" gap="3">
                <Flex justify="between" align="center">
                  <Heading size="4">Action Items</Heading>
                  <Button 
                    onClick={generateActionItems}
                    disabled={isLoading}
                    variant="soft"
                    size="2"
                  >
                    <ReloadIcon className={isLoading ? "animate-spin" : ""} />
                    Generate New Items
                  </Button>
                </Flex>

                <ScrollArea style={{ height: '500px' }}>
                  <Flex direction="column" gap="2">
                    {actionItems.length === 0 ? (
                      <Card variant="surface" style={{ textAlign: 'center', padding: '3rem' }}>
                        <Text size="3" color="gray">
                          No action items yet. Click "Generate New Items" after syncing emails.
                        </Text>
                      </Card>
                    ) : (
                      actionItems.map((item) => (
                        <Card 
                          key={item.id} 
                          variant="surface"
                          style={{ 
                            cursor: 'pointer',
                            opacity: item.status === 'completed' ? 0.7 : 1
                          }}
                        >
                          <Flex direction="column" gap="2">
                            {/* Collapsed View */}
                            <Flex 
                              direction="column" 
                              gap="1"
                              onClick={() => toggleActionItemExpanded(item.id)}
                            >
                              {/* Subject and Date on same line */}
                              <Flex justify="between" align="center">
                                <Flex align="center" gap="2" style={{ flex: 1 }}>
                                  <IconButton 
                                    size="1" 
                                    variant="ghost"
                                    style={{ 
                                      transform: expandedActionItems.has(item.id) ? 'rotate(90deg)' : 'rotate(0deg)',
                                      transition: 'transform 0.2s'
                                    }}
                                  >
                                    <ChevronRightIcon />
                                  </IconButton>
                                  <Text weight="bold" size="3" style={{ wordBreak: 'break-word' }}>
                                    {item.metaData?.subject || item.title}
                                  </Text>
                                </Flex>
                                <Text size="2" color="gray" style={{ whiteSpace: 'nowrap' }}>
                                  {item.metaData?.date ? new Date(item.metaData.date).toLocaleDateString() : 
                                   item.createdAt ? new Date(item.createdAt).toLocaleDateString() : 'No date'}
                                </Text>
                              </Flex>
                              
                              {/* People Included */}
                              <Flex gap="1" align="center" style={{ marginLeft: '28px' }}>
                                <Text size="2" color="gray">People Included:</Text>
                                <Text size="2" style={{ wordBreak: 'break-word' }}>
                                  {item.metaData?.from_email || item.source || 'Unknown'}
                                  {item.metaData?.to_email && `, ${item.metaData.to_email}`}
                                </Text>
                              </Flex>
                              
                              {/* Summary */}
                              <Box style={{ marginLeft: '28px' }}>
                                <Text size="2" color="gray">Summary:</Text>
                                <Text size="2" style={{ wordBreak: 'break-word' }}>
                                  {item.context || item.metaData?.description || `Action required: ${item.title}`}
                                </Text>
                              </Box>
                              
                              {/* Priority Badge */}
                              <Flex gap="2" align="center" style={{ marginLeft: '28px' }}>
                                <Badge color={item.priority === 'high' ? 'red' : item.priority === 'medium' ? 'orange' : 'gray'}>
                                  {item.priority} priority
                                </Badge>
                                {item.status === 'completed' && (
                                  <Badge color="green" variant="soft">Completed</Badge>
                                )}
                              </Flex>
                            </Flex>
                            
                            {/* Expanded View */}
                            {expandedActionItems.has(item.id) && (
                              <Box 
                                mt="3" 
                                p="4" 
                                style={{ 
                                  backgroundColor: 'var(--gray-2)', 
                                  borderRadius: '8px',
                                  borderLeft: '4px solid var(--blue-6)'
                                }}
                              >
                                {/* Full Email Content */}
                                <Box mb="4">
                                  <Text size="2" weight="bold" color="gray" mb="2">Full Email Content</Text>
                                  <Box 
                                    p="3" 
                                    style={{ 
                                      backgroundColor: 'var(--gray-1)', 
                                      borderRadius: '4px',
                                      whiteSpace: 'pre-wrap',
                                      wordBreak: 'break-word',
                                      maxHeight: '400px',
                                      overflowY: 'auto'
                                    }}
                                  >
                                    <Text size="2">
                                      {item.metaData?.emailContent || item.metaData?.body || 'Email content not available'}
                                    </Text>
                                  </Box>
                                </Box>
                                
                                {/* Suggested Response */}
                                <Box mb="4">
                                  <Text size="2" weight="bold" color="gray" mb="2">Suggested Response</Text>
                                  <Flex direction="column" gap="2">
                                    <TextArea 
                                      id={`response-${item.id}`}
                                      defaultValue={suggestedResponses[item.id] || 'Loading suggested response...'}
                                      placeholder="Type your response here..."
                                      style={{ minHeight: '120px' }}
                                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                                        setSuggestedResponses(prev => ({
                                          ...prev,
                                          [item.id]: e.target.value
                                        }));
                                      }}
                                    />
                                    <Flex gap="2" justify="end">
                                      <Button 
                                        variant="soft" 
                                        size="2"
                                        onClick={() => {
                                          // Load AI suggestion
                                          getSuggestedResponse(item.id);
                                        }}
                                      >
                                        <ReloadIcon /> Generate AI Response
                                      </Button>
                                      <Button 
                                        variant="solid" 
                                        size="2"
                                        onClick={() => {
                                          const response = suggestedResponses[item.id] || '';
                                          if (response && item.metaData?.from_email) {
                                            // Send email via Gmail
                                            sendEmailReply(item, response);
                                          }
                                        }}
                                      >
                                        <PaperPlaneIcon /> Send Reply
                                      </Button>
                                    </Flex>
                                  </Flex>
                                </Box>
                                
                                {/* Action Buttons */}
                                <Flex gap="2" justify="between">
                                  <Flex gap="2">
                                    <Button 
                                      variant="soft"
                                      size="2"
                                      onClick={() => convertToTask(item.id)}
                                      disabled={item.status === 'completed'}
                                    >
                                      <PlusIcon /> Create Task
                                    </Button>
                                    <Button 
                                      variant="soft"
                                      size="2"
                                      color="green"
                                      onClick={() => markActionItemComplete(item.id)}
                                      disabled={item.status === 'completed'}
                                    >
                                      <CheckIcon /> Mark Complete
                                    </Button>
                                  </Flex>
                                  <IconButton
                                    size="2"
                                    variant="ghost"
                                    color="red"
                                    onClick={() => setDeleteConfirmItem(item)}
                                  >
                                    <TrashIcon />
                                  </IconButton>
                                </Flex>
                              </Box>
                            )}
                          </Flex>
                        </Card>
                      ))
                    )}
                  </Flex>
                </ScrollArea>
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Tasks Tab */}
          <Tabs.Content value="tasks">
            <Card>
              <Flex direction="column" gap="3">
                <Flex justify="between" align="center">
                  <Heading size="4">Tasks</Heading>
                  <Button 
                    onClick={() => {
                      const newTask: Task = {
                        id: `task-${Date.now()}`,
                        title: "New Task",
                        description: "",
                        priority: "medium",
                        status: "pending",
                        category: "general",
                        createdAt: new Date().toISOString(),
                      };
                      setTasks([...tasks, newTask]);
                    }}
                    size="2"
                  >
                    <PlusIcon /> Add New Task
                  </Button>
                </Flex>

                <ScrollArea style={{ height: '500px' }}>
                  <Flex direction="column" gap="2">
                    {tasks.length === 0 ? (
                      <Card variant="surface" style={{ textAlign: 'center', padding: '3rem' }}>
                        <Text size="3" color="gray">
                          No tasks yet. Add a new one to get started.
                        </Text>
                      </Card>
                    ) : (
                      tasks.map((task, index) => (
                        <Card 
                          key={task.id} 
                          variant="surface"
                          style={{ cursor: 'pointer' }}
                        >
                          <Flex direction="column" gap="2">
                            <Flex 
                              justify="between" 
                              align="start"
                            >
                              <Flex direction="column" gap="1" style={{ flex: 1 }}>
                                <Flex align="center" gap="2">
                                  <Text weight="bold" size="2">{task.title}</Text>
                                </Flex>
                                <Box style={{ marginLeft: '28px' }}>
                                  <Text size="2" color="gray">{task.description}</Text>
                                  <Badge color={task.priority === 'high' ? 'red' : task.priority === 'medium' ? 'orange' : 'gray'}>
                                    {task.priority}
                                  </Badge>
                                  {task.dueDate && (
                                    <Text size="1" color="red">Due: {new Date(task.dueDate).toLocaleDateString()}</Text>
                                  )}
                                </Box>
                              </Flex>
                              <Badge color={task.status === 'completed' ? 'green' : task.status === 'pending' ? 'gray' : 'blue'}>
                                {task.status}
                              </Badge>
                            </Flex>
                          </Flex>
                        </Card>
                      ))
                    )}
                  </Flex>
                </ScrollArea>
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Recordings Tab */}
          <Tabs.Content value="recordings">
            <Card>
              <Flex direction="column" gap="3">
                <Flex justify="between" align="center">
                  <Heading size="4">Meeting Recordings</Heading>
                  <Button 
                    onClick={() => setShowRecordingDialog(true)}
                    variant="soft"
                    size="2"
                  >
                    <SpeakerLoudIcon /> New Recording
                  </Button>
                </Flex>

                <Box style={{ height: '500px' }}>
                  <RecordingsList 
                    context="oracle"
                    onPlayRecording={(recordingId) => {
                      // Open audio in new tab or handle playback
                      window.open(`/api/recordings/${recordingId}/audio`, '_blank');
                    }}
                  />
                </Box>
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Sentiment Tab */}
          <Tabs.Content value="sentiment">
            <Card>
              <Flex direction="column" gap="3">
                <Flex justify="between" align="center">
                  <Heading size="4">Sentiment Analysis</Heading>
                  <Button 
                    onClick={generateSentiment}
                    disabled={isLoading}
                    variant="soft"
                    size="2"
                  >
                    <ReloadIcon className={isLoading ? "animate-spin" : ""} />
                    Refresh Analysis
                  </Button>
                </Flex>

                {sentimentData ? (
                  <Flex direction="column" gap="4">
                    {/* Current Sentiment */}
                    <Card variant="surface">
                      <Flex direction="column" gap="3">
                        <Flex justify="between" align="center">
                          <Text size="3" weight="bold">Current Sentiment</Text>
                          <Badge size="2" color={getSentimentColor(sentimentData.current_sentiment?.sentiment)}>
                            {sentimentData.current_sentiment?.sentiment || 'Unknown'}
                          </Badge>
                        </Flex>
                        <Flex align="center" gap="2">
                          <Text size="2">Confidence:</Text>
                          <Text size="2" weight="bold">
                            {sentimentData.current_sentiment?.confidence ? 
                              `${Math.round(sentimentData.current_sentiment.confidence * 100)}%` : 'N/A'}
                          </Text>
                        </Flex>
                        <Flex align="center" gap="2">
                          <Text size="2">Trend:</Text>
                          <Badge variant="soft">
                            {sentimentData.trend || 'Stable'}
                          </Badge>
                        </Flex>
                      </Flex>
                    </Card>

                    {/* Concerns */}
                    {sentimentData.concerns && sentimentData.concerns.length > 0 && (
                      <Card variant="surface">
                        <Flex direction="column" gap="2">
                          <Flex align="center" gap="2">
                            <ExclamationTriangleIcon color="orange" />
                            <Text size="3" weight="bold">Concerns</Text>
                          </Flex>
                          <Separator size="4" />
                          {sentimentData.concerns.map((concern, index) => (
                            <Text key={index} size="2">• {concern}</Text>
                          ))}
                        </Flex>
                      </Card>
                    )}

                    {/* Positive Aspects */}
                    {sentimentData.positive_aspects && sentimentData.positive_aspects.length > 0 && (
                      <Card variant="surface">
                        <Flex direction="column" gap="2">
                          <Flex align="center" gap="2">
                            <CheckCircledIcon color="green" />
                            <Text size="3" weight="bold">Positive Aspects</Text>
                          </Flex>
                          <Separator size="4" />
                          {sentimentData.positive_aspects.map((aspect, index) => (
                            <Text key={index} size="2">• {aspect}</Text>
                          ))}
                        </Flex>
                      </Card>
                    )}
                  </Flex>
                ) : (
                  <Card variant="surface" style={{ textAlign: 'center', padding: '3rem' }}>
                    <Text size="3" color="gray">
                      No sentiment analysis yet. Click "Refresh Analysis" after syncing communications.
                    </Text>
                  </Card>
                )}
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Suggested Tasks Tab */}
          <Tabs.Content value="suggested-tasks">
            <Card>
              <Flex direction="column" gap="3">
                <Flex justify="between" align="center">
                  <Heading size="4">Suggested Tasks</Heading>
                  <Button 
                    onClick={generateSuggestedTasks}
                    disabled={isLoading}
                    variant="soft"
                    size="2"
                  >
                    <ReloadIcon className={isLoading ? "animate-spin" : ""} />
                    Generate Suggestions
                  </Button>
                </Flex>

                <ScrollArea style={{ height: '500px' }}>
                  <Flex direction="column" gap="2">
                    {suggestedTasks.length === 0 ? (
                      <Card variant="surface" style={{ textAlign: 'center', padding: '3rem' }}>
                        <Text size="3" color="gray">
                          No suggested tasks yet. Click "Generate Suggestions" after syncing communications.
                        </Text>
                      </Card>
                    ) : (
                      suggestedTasks.map((task, index) => (
                        <Card 
                          key={index} 
                          variant="surface"
                          style={{ cursor: 'pointer' }}
                        >
                          <Flex direction="column" gap="2">
                            <Flex 
                              justify="between" 
                              align="start"
                              onClick={() => toggleSuggestedTaskExpanded(index)}
                            >
                              <Flex direction="column" gap="1" style={{ flex: 1 }}>
                                <Flex align="center" gap="2">
                                  <IconButton 
                                    size="1" 
                                    variant="ghost"
                                    style={{ 
                                      transform: expandedSuggestedTasks.has(index) ? 'rotate(90deg)' : 'rotate(0deg)',
                                      transition: 'transform 0.2s'
                                    }}
                                  >
                                    <ChevronRightIcon />
                                  </IconButton>
                                  <Text weight="bold" size="2">{task.title}</Text>
                                </Flex>
                                <Box style={{ marginLeft: '28px' }}>
                                  <Text size="2" color="gray">{task.reason}</Text>
                                  {task.estimated_time && (
                                    <Flex align="center" gap="1" mt="1">
                                      <Text size="1" color="gray">Estimated time:</Text>
                                      <Text size="1" weight="medium">{task.estimated_time}</Text>
                                    </Flex>
                                  )}
                                </Box>
                              </Flex>
                              <Badge color={task.priority === 'high' ? 'red' : task.priority === 'medium' ? 'orange' : 'gray'}>
                                {task.priority}
                              </Badge>
                            </Flex>
                            
                            {/* Expanded content */}
                            {expandedSuggestedTasks.has(index) && (
                              <Box style={{ 
                                marginLeft: '28px', 
                                paddingTop: '8px',
                                borderTop: '1px solid var(--gray-4)'
                              }}>
                                <Flex direction="column" gap="2">
                                  {task.source && (
                                    <Box>
                                      <Text size="1" weight="bold" color="gray">Source:</Text>
                                      <Text size="2">{task.source}</Text>
                                    </Box>
                                  )}
                                  
                                  {task.context && (
                                    <Box>
                                      <Text size="1" weight="bold" color="gray">Context:</Text>
                                      <Card variant="surface">
                                        <Text size="1" style={{ whiteSpace: 'pre-wrap' }}>
                                          {task.context}
                                        </Text>
                                      </Card>
                                    </Box>
                                  )}
                                  
                                  {task.related_emails && task.related_emails.length > 0 && (
                                    <Box>
                                      <Text size="1" weight="bold" color="gray">Related Communications:</Text>
                                      <Flex direction="column" gap="1" mt="1">
                                        {task.related_emails.map((emailRef, idx) => (
                                          <Text key={idx} size="1">• {emailRef}</Text>
                                        ))}
                                      </Flex>
                                    </Box>
                                  )}
                                  
                                  {task.metadata && Object.keys(task.metadata).length > 0 && (
                                    <Box>
                                      <Text size="1" weight="bold" color="gray">Additional Details:</Text>
                                      <Flex direction="column" gap="1" mt="1">
                                        {Object.entries(task.metadata).map(([key, value]) => (
                                          <Text key={key} size="1">
                                            <Text weight="medium">{key}:</Text> {String(value)}
                                          </Text>
                                        ))}
                                      </Flex>
                                    </Box>
                                  )}
                                  
                                  <Flex gap="2" mt="2">
                                    <Button 
                                      size="1" 
                                      variant="soft"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        // Convert to action item
                                        generateActionItems();
                                      }}
                                    >
                                      <PlusIcon /> Convert to Action Item
                                    </Button>
                                  </Flex>
                                </Flex>
                              </Box>
                            )}
                          </Flex>
                        </Card>
                      ))
                    )}
                  </Flex>
                </ScrollArea>
              </Flex>
            </Card>
          </Tabs.Content>
        </Tabs.Root>
      </div>

      {/* Email Detail Dialog */}
      <Dialog.Root open={showEmailDialog} onOpenChange={setShowEmailDialog}>
        <Dialog.Content style={{ maxWidth: '700px', maxHeight: '80vh' }}>
          <Dialog.Title>{selectedEmail?.subject || 'Email Details'}</Dialog.Title>
          <ScrollArea style={{ maxHeight: '60vh' }}>
            <Flex direction="column" gap="3" mt="4">
              <Box>
                <Text size="2" weight="bold" color="gray">From:</Text>
                <Text size="2">{selectedEmail?.from}</Text>
              </Box>
              <Box>
                <Text size="2" weight="bold" color="gray">To:</Text>
                <Text size="2">{selectedEmail?.to?.join(', ')}</Text>
              </Box>
              <Box>
                <Text size="2" weight="bold" color="gray">Date:</Text>
                <Text size="2">{selectedEmail?.date ? new Date(selectedEmail.date).toLocaleString() : ''}</Text>
              </Box>
              <Separator size="4" />
              <Box>
                <Text size="2" weight="bold" color="gray">Content:</Text>
                <Card variant="surface" mt="2">
                  <Text size="2" style={{ whiteSpace: 'pre-wrap' }}>
                    {selectedEmail?.content || selectedEmail?.snippet || 'No content available'}
                  </Text>
                </Card>
              </Box>
            </Flex>
          </ScrollArea>
          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">Close</Button>
            </Dialog.Close>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>

      {/* Delete Confirmation Dialog */}
      <AlertDialog.Root open={deleteConfirmItem !== null} onOpenChange={(open) => {
        if (!open) setDeleteConfirmItem(null);
      }}>
        <AlertDialog.Content>
          <AlertDialog.Title>Delete Action Item</AlertDialog.Title>
          <AlertDialog.Description>
            This will mark the action item as deleted. We'll use this to improve our AI's understanding of what constitutes a valid action item.
          </AlertDialog.Description>
          <Flex gap="3" mt="4" justify="end">
            <AlertDialog.Cancel>
              <Button variant="soft" color="gray">Cancel</Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button variant="soft" color="red" onClick={() => {
                if (deleteConfirmItem) {
                  deleteActionItem(deleteConfirmItem);
                }
              }}>
                Delete
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>

      {/* Delete Email Confirmation Dialog */}
      <AlertDialog.Root open={deleteConfirmEmail !== null} onOpenChange={(open) => {
        if (!open) setDeleteConfirmEmail(null);
      }}>
        <AlertDialog.Content>
          <AlertDialog.Title>Delete Email Thread</AlertDialog.Title>
          <AlertDialog.Description>
            This will remove the email thread from your Oracle view. The email will remain in your Gmail account.
          </AlertDialog.Description>
          <Flex gap="3" mt="4" justify="end">
            <AlertDialog.Cancel>
              <Button variant="soft" color="gray">Cancel</Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button variant="soft" color="red" onClick={() => {
                if (deleteConfirmEmail) {
                  deleteEmail(deleteConfirmEmail);
                }
              }}>
                Delete
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>
    </div>
  );
};

export default OraclePage; 