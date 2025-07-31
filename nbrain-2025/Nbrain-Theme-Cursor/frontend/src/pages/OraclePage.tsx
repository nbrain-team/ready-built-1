import React, { useState, useEffect } from 'react';
import { Box, Heading, Text, Card, Flex, Button, TextField, Tabs, Badge, ScrollArea, IconButton, Dialog, Separator } from '@radix-ui/themes';
import { MagnifyingGlassIcon, EnvelopeClosedIcon, CalendarIcon, FileTextIcon, ReloadIcon, CheckCircledIcon, ExclamationTriangleIcon, LightningBoltIcon } from '@radix-ui/react-icons';
import api from '../api';

interface Email {
  id: string;
  subject: string;
  from: string;
  to: string[];
  date: string;
  snippet: string;
  thread_id: string;
}

interface ActionItem {
  id: string;
  title: string;
  source: string;
  sourceType: string;
  dueDate?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'completed';
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
}

const OraclePage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [emails, setEmails] = useState<Email[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  const [suggestedTasks, setSuggestedTasks] = useState<SuggestedTask[]>([]);
  const [activeTab, setActiveTab] = useState('communications');
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [needsEmailConnection, setNeedsEmailConnection] = useState(false);
  // Fetch initial data
  useEffect(() => {
    fetchEmails();
    fetchActionItems();
    fetchSentiment();
    fetchSuggestedTasks();
  }, []);

  const fetchEmails = async () => {
    try {
      const response = await api.get('/oracle/emails');
      setEmails(response.data || []);
    } catch (error: any) {
      console.error('Error fetching emails:', error);
    }
      // Handle 503 error specifically - table not initialized
      if (error.response?.status === 503) {
        setNeedsEmailConnection(true);
        setEmails([]);
      }  };

  const syncEmailsAndCalendar = async () => {
    setIsLoading(true);
    try {
      // Sync emails
      await api.post('/oracle/sync/email');
      // Sync calendar
      await api.post('/oracle/sync/calendar');
      // Refresh emails list
      await fetchEmails();
    } catch (error) {
      console.error('Error syncing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchActionItems = async () => {
    try {
      const response = await api.get('/oracle/action-items');
      setActionItems(response.data || []);
    } catch (error) {
      console.error('Error fetching action items:', error);
    }
  };

  const generateActionItems = async () => {
    setIsLoading(true);
    try {
      await api.post('/oracle/generate-action-items');
      await fetchActionItems();
    } catch (error) {
      console.error('Error generating action items:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSentiment = async () => {
    try {
      const response = await api.get('/oracle/sentiment');
      setSentimentData(response.data);
    } catch (error) {
      console.error('Error fetching sentiment:', error);
    }
  };

  const generateSentiment = async () => {
    setIsLoading(true);
    try {
      await api.post('/oracle/generate-sentiment');
      await fetchSentiment();
    } catch (error) {
      console.error('Error generating sentiment:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSuggestedTasks = async () => {
    try {
      const response = await api.get('/oracle/suggested-tasks');
      setSuggestedTasks(response.data || []);
    } catch (error) {
      console.error('Error fetching suggested tasks:', error);
    }
  };

  const generateSuggestedTasks = async () => {
    setIsLoading(true);
    try {
      await api.post('/oracle/generate-suggested-tasks');
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
      const response = await api.post('/oracle/search', {
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

  const toggleActionItemStatus = async (itemId: string) => {
    try {
      const item = actionItems.find(a => a.id === itemId);
      if (!item) return;
      
      await api.put(`/oracle/action-items/${itemId}`, {
        status: item.status === 'completed' ? 'pending' : 'completed'
      });
      
      setActionItems(prev => prev.map(a => 
        a.id === itemId ? { ...a, status: a.status === 'completed' ? 'pending' : 'completed' } : a
      ));
    } catch (error) {
      console.error('Error updating action item:', error);
    }
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
        <Heading size="7" style={{ color: 'var(--gray-12)' }}>The Oracle</Heading>
        <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
          Your all-knowing AI assistant that captures and understands everything
        </Text>
      </div>

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
                        <Text size="3" color="gray">
                          No emails synced yet. Click "Sync Email & Calendar" to get started.
                        </Text>
                      </Card>
                    ) : (
                      emails.map((email) => (
                        <Card 
                          key={email.id} 
                          variant="surface" 
                          style={{ cursor: 'pointer' }}
                          onClick={() => {
                            setSelectedEmail(email);
                            setShowEmailDialog(true);
                          }}
                        >
                          <Flex direction="column" gap="2">
                            <Flex justify="between" align="center">
                              <Text weight="bold" size="2">{email.subject || 'No Subject'}</Text>
                              <Text size="1" color="gray">
                                {new Date(email.date).toLocaleDateString()}
                              </Text>
                            </Flex>
                            <Flex gap="2" align="center">
                              <Badge color="blue" variant="soft">From: {email.from}</Badge>
                              {email.to && email.to.length > 0 && (
                                <Badge color="green" variant="soft">To: {email.to[0]}</Badge>
                              )}
                            </Flex>
                            <Text size="1" color="gray" style={{ 
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}>
                              {email.snippet}
                            </Text>
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
                        <Card key={item.id} variant="surface">
                          <Flex justify="between" align="center">
                            <Flex direction="column" gap="1" style={{ flex: 1 }}>
                              <Text weight="bold">{item.title}</Text>
                              <Flex gap="2" align="center">
                                <Badge color={item.priority === 'high' ? 'red' : item.priority === 'medium' ? 'orange' : 'gray'}>
                                  {item.priority}
                                </Badge>
                                <Text size="1" color="gray">from {item.source}</Text>
                                {item.dueDate && <Text size="1" color="red">Due: {new Date(item.dueDate).toLocaleDateString()}</Text>}
                              </Flex>
                            </Flex>
                            <Button 
                              variant={item.status === 'completed' ? 'solid' : 'soft'}
                              size="1"
                              onClick={() => toggleActionItemStatus(item.id)}
                            >
                              {item.status === 'completed' ? '✓ Done' : 'Mark Done'}
                            </Button>
                          </Flex>
                        </Card>
                      ))
                    )}
                  </Flex>
                </ScrollArea>
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
                        <Card key={index} variant="surface">
                          <Flex direction="column" gap="2">
                            <Flex justify="between" align="start">
                              <Text weight="bold" size="2">{task.title}</Text>
                              <Badge color={task.priority === 'high' ? 'red' : task.priority === 'medium' ? 'orange' : 'gray'}>
                                {task.priority}
                              </Badge>
                            </Flex>
                            <Text size="2" color="gray">{task.reason}</Text>
                            {task.estimated_time && (
                              <Flex align="center" gap="1">
                                <Text size="1" color="gray">Estimated time:</Text>
                                <Text size="1" weight="medium">{task.estimated_time}</Text>
                              </Flex>
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
        <Dialog.Content style={{ maxWidth: '600px' }}>
          <Dialog.Title>{selectedEmail?.subject || 'Email Details'}</Dialog.Title>
          <Flex direction="column" gap="3" mt="4">
            <Box>
              <Text size="2" weight="bold">From:</Text>
              <Text size="2">{selectedEmail?.from}</Text>
            </Box>
            <Box>
              <Text size="2" weight="bold">To:</Text>
              <Text size="2">{selectedEmail?.to?.join(', ')}</Text>
            </Box>
            <Box>
              <Text size="2" weight="bold">Date:</Text>
              <Text size="2">{selectedEmail?.date ? new Date(selectedEmail.date).toLocaleString() : ''}</Text>
            </Box>
            <Separator size="4" />
            <Box>
              <Text size="2">{selectedEmail?.snippet}</Text>
            </Box>
          </Flex>
          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">Close</Button>
            </Dialog.Close>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    </div>
  );
};

export default OraclePage; 