import React, { useState, useEffect } from 'react';
import { Box, Heading, Text, Card, Flex, Button, TextField, Badge, Avatar, Progress, IconButton, ScrollArea, Separator } from '@radix-ui/themes';
import { useNavigate, useLocation } from 'react-router-dom';
import { PlusIcon, MagnifyingGlassIcon, ActivityLogIcon, EnvelopeClosedIcon, CheckCircledIcon, CalendarIcon, ExclamationTriangleIcon, LightningBoltIcon } from '@radix-ui/react-icons';
import api from '../api';
import ClientAvatar from '../components/ClientAvatar';

interface ClientData {
  id: string;
  name: string;
  status: string;
  primaryContactName: string;
  primaryContactEmail: string;
  projectValue: number;
  healthScore: number;
  lastCommunication: string;
  totalTasks: number;
  completedTasks: number;
  teamMembers: number;
  companyWebsite?: string;
  domain?: string;
}

interface AggregatedSummary {
  upcomingMeetings: Array<{
    id: string;
    clientId: string;
    clientName: string;
    clientDomain?: string;
    clientWebsite?: string;
    title: string;
    startTime: string;
    attendees: string[];
  }>;
  sentimentIssues: Array<{
    clientId: string;
    clientName: string;
    clientDomain?: string;
    clientWebsite?: string;
    concerns: string[];
    sentiment: string;
    trend: string;
  }>;
  suggestedTasks: Array<{
    clientId: string;
    clientName: string;
    clientDomain?: string;
    clientWebsite?: string;
    task: string;
    priority: string;
    reason: string;
  }>;
}

const ClientPortal = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [clients, setClients] = useState<ClientData[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncingAll, setIsSyncingAll] = useState(false);
  const [syncProgress, setSyncProgress] = useState({ current: 0, total: 0 });
  const [aggregatedSummary, setAggregatedSummary] = useState<AggregatedSummary>({
    upcomingMeetings: [],
    sentimentIssues: [],
    suggestedTasks: []
  });

  // Force component to remount by using location key
  useEffect(() => {
    setIsLoading(true);
    fetchClients();
    fetchAggregatedSummary();
  }, [location.key]); // Use location.key instead of pathname

  // Refetch clients when the page gains focus (user navigates back)
  useEffect(() => {
    const handleFocus = () => {
      fetchClients();
      fetchAggregatedSummary();
    };

    window.addEventListener('focus', handleFocus);
    
    // Also listen for visibility change
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchClients();
        fetchAggregatedSummary();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const fetchClients = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error: any) {
      console.error('Error fetching clients:', error);
      // If there's a 404, it might be an API URL issue
      if (error.response?.status === 404) {
        console.error('API endpoint not found. Check VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
      }
      // Don't clear clients on error - keep showing previous data
      if (clients.length === 0) {
        setClients([]); // Only clear if we have no data
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAggregatedSummary = async () => {
    try {
      const response = await api.get('/clients/aggregated-summary');
      setAggregatedSummary(response.data);
    } catch (error: any) {
      console.error('Error fetching aggregated summary:', error.message || error);
      // Log more details if available
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'green';
      case 'ongoing': return 'blue';
      case 'completed': return 'gray';
      case 'prospect': return 'orange';
      default: return 'gray';
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'orange';
    return 'red';
  };

  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         client.primaryContactEmail?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || client.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const handleClientClick = (clientId: string) => {
    navigate(`/client/${clientId}`);
  };

  const handleSyncAll = async () => {
    if (isSyncingAll || clients.length === 0) return;
    
    const confirmed = window.confirm(
      `This will sync all data for ${clients.length} clients including:\n` +
      '• Emails & Calendar events\n' +
      '• AI Analysis (Commitments, Weekly Summary, Sentiment)\n' +
      '• Suggested Tasks\n' +
      '• Meeting Transcripts\n' +
      '• Industry Pulse\n\n' +
      'This may take several minutes. Continue?'
    );
    
    if (!confirmed) return;
    
    setIsSyncingAll(true);
    setSyncProgress({ current: 0, total: clients.length });
    
    try {
      // Call the sync all endpoint
      const response = await api.post('/clients/sync-all-clients');
      
      // If the backend returns a task ID, we could poll for progress
      // For now, we'll just show a success message after completion
      
      // Refresh clients data after sync
      await fetchClients();
      await fetchAggregatedSummary();
      
      alert('All clients synced successfully!');
    } catch (error) {
      console.error('Error syncing all clients:', error);
      alert('Error syncing clients. Check console for details.');
    } finally {
      setIsSyncingAll(false);
      setSyncProgress({ current: 0, total: 0 });
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
      return `Today at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return `Tomorrow at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    } else {
      return date.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      });
    }
  };

  return (
    <div className="page-container" style={{ height: '100vh', overflow: 'auto' }}>
      <Box style={{ padding: '2rem' }}>
        {/* Header */}
        <Flex justify="between" align="center" mb="6">
          <Box>
            <Heading size="7" style={{ color: 'var(--gray-12)' }}>Client Portal</Heading>
            <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
              Manage all your client relationships in one place
            </Text>
          </Box>
          <Flex gap="3">
            <Button 
              size="3" 
              variant="soft"
              onClick={handleSyncAll}
              disabled={isSyncingAll || clients.length === 0}
            >
              {isSyncingAll ? (
                <>
                  Syncing... {syncProgress.current > 0 && `(${syncProgress.current}/${syncProgress.total})`}
                </>
              ) : (
                <>
                  <ActivityLogIcon /> Sync All
                </>
              )}
            </Button>
            <Button size="3" onClick={() => navigate('/client/new')}>
              <PlusIcon /> New Client
            </Button>
          </Flex>
        </Flex>

        {/* Aggregated Summary Section */}
        <Card mb="6" style={{ background: 'var(--gray-2)' }}>
          <Heading size="5" mb="4">Client Activity Summary</Heading>
          
          <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Upcoming Meetings */}
            <Box>
              <Flex align="center" gap="2" mb="3">
                <CalendarIcon width="20" height="20" />
                <Heading size="3">Next Week's Meetings</Heading>
              </Flex>
              <ScrollArea style={{ height: '150px' }}>
                {aggregatedSummary.upcomingMeetings.length > 0 ? (
                  <Flex direction="column" gap="2">
                    {aggregatedSummary.upcomingMeetings.map((meeting) => (
                      <Card key={meeting.id} style={{ padding: '0.75rem', cursor: 'pointer' }} onClick={() => handleClientClick(meeting.clientId)}>
                        <Flex align="center" gap="2">
                          <ClientAvatar
                            name={meeting.clientName}
                            domain={meeting.clientDomain}
                            website={meeting.clientWebsite}
                            size="1"
                          />
                          <Box style={{ flex: 1 }}>
                            <Text size="2" weight="medium">{meeting.title}</Text>
                            <Text size="1" color="gray">{meeting.clientName} • {formatDate(meeting.startTime)}</Text>
                          </Box>
                        </Flex>
                      </Card>
                    ))}
                  </Flex>
                ) : (
                  <Text size="2" color="gray">No upcoming meetings this week</Text>
                )}
              </ScrollArea>
            </Box>

            {/* Sentiment Issues */}
            <Box>
              <Flex align="center" gap="2" mb="3">
                <ExclamationTriangleIcon width="20" height="20" color="orange" />
                <Heading size="3">Client Sentiment</Heading>
              </Flex>
              <ScrollArea style={{ height: '150px' }}>
                {aggregatedSummary.sentimentIssues.length > 0 ? (
                  <Flex direction="column" gap="2">
                    {aggregatedSummary.sentimentIssues.map((issue, index) => (
                      <Card key={`${issue.clientId}-${index}`} style={{ padding: '0.75rem', cursor: 'pointer' }} onClick={() => handleClientClick(issue.clientId)}>
                        <Flex align="center" gap="2">
                          <ClientAvatar
                            name={issue.clientName}
                            domain={issue.clientDomain}
                            website={issue.clientWebsite}
                            size="1"
                          />
                          <Box style={{ flex: 1 }}>
                            <Text size="2" weight="medium">{issue.clientName}</Text>
                            <Text size="1" color="gray">
                              {issue.concerns[0]}
                              {issue.concerns.length > 1 && ` (+${issue.concerns.length - 1} more)`}
                            </Text>
                          </Box>
                          <Badge color={issue.sentiment === 'negative' ? 'red' : 'orange'} size="1">
                            {issue.trend}
                          </Badge>
                        </Flex>
                      </Card>
                    ))}
                  </Flex>
                ) : (
                  <Text size="2" color="gray">No sentiment issues detected</Text>
                )}
              </ScrollArea>
            </Box>

            {/* Suggested Tasks */}
            <Box>
              <Flex align="center" gap="2" mb="3">
                <LightningBoltIcon width="20" height="20" color="blue" />
                <Heading size="3">Suggested Tasks</Heading>
              </Flex>
              <ScrollArea style={{ height: '150px' }}>
                {aggregatedSummary.suggestedTasks.length > 0 ? (
                  <Flex direction="column" gap="2">
                    {aggregatedSummary.suggestedTasks.map((task, index) => (
                      <Card key={`${task.clientId}-${index}`} style={{ padding: '0.75rem', cursor: 'pointer' }} onClick={() => handleClientClick(task.clientId)}>
                        <Flex align="center" gap="2">
                          <ClientAvatar
                            name={task.clientName}
                            domain={task.clientDomain}
                            website={task.clientWebsite}
                            size="1"
                          />
                          <Box style={{ flex: 1 }}>
                            <Text size="2" weight="medium">{task.task}</Text>
                            <Text size="1" color="gray">{task.clientName}</Text>
                          </Box>
                          <Badge color={task.priority === 'high' ? 'red' : task.priority === 'medium' ? 'orange' : 'gray'} size="1">
                            {task.priority}
                          </Badge>
                        </Flex>
                      </Card>
                    ))}
                  </Flex>
                ) : (
                  <Text size="2" color="gray">No suggested tasks</Text>
                )}
              </ScrollArea>
            </Box>
          </Box>
        </Card>

        {/* Filters and Search */}
        <Card mb="4">
          <Flex gap="3" align="center">
            <TextField.Root
              placeholder="Search clients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ flex: 1 }}
              size="3"
            >
              <TextField.Slot>
                <MagnifyingGlassIcon />
              </TextField.Slot>
            </TextField.Root>

            <Flex gap="2">
              <Button
                variant={filterStatus === 'all' ? 'solid' : 'soft'}
                onClick={() => setFilterStatus('all')}
              >
                All
              </Button>
              <Button
                variant={filterStatus === 'active' ? 'solid' : 'soft'}
                onClick={() => setFilterStatus('active')}
                color="green"
              >
                Active
              </Button>
              <Button
                variant={filterStatus === 'ongoing' ? 'solid' : 'soft'}
                onClick={() => setFilterStatus('ongoing')}
                color="blue"
              >
                Ongoing
              </Button>
              <Button
                variant={filterStatus === 'completed' ? 'solid' : 'soft'}
                onClick={() => setFilterStatus('completed')}
                color="gray"
              >
                Completed
              </Button>
            </Flex>
          </Flex>
        </Card>

        {/* Client Cards - Smaller Square Format */}
        <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {isLoading ? (
            <Card style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '2rem' }}>
              <Text size="3" color="gray">Loading clients...</Text>
            </Card>
          ) : filteredClients.length > 0 ? (
            filteredClients.map((client) => (
            <Card
              key={client.id}
              style={{ 
                cursor: 'pointer', 
                transition: 'all 0.2s', 
                position: 'relative',
                height: 'fit-content',
                minHeight: '140px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '';
              }}
              onClick={() => handleClientClick(client.id)}
            >
              <Flex direction="column" gap="3">
                {/* Header */}
                <Flex justify="between" align="start">
                  <Flex align="center" gap="2">
                    <ClientAvatar
                      name={client.name}
                      domain={client.domain}
                      website={client.companyWebsite}
                      size="2"
                      color={getStatusColor(client.status)}
                    />
                    <Box>
                      <Heading size="3">{client.name}</Heading>
                      <Text size="1" color="gray">{client.primaryContactEmail}</Text>
                    </Box>
                  </Flex>
                  <Badge color={getStatusColor(client.status)} size="1">
                    {client.status}
                  </Badge>
                </Flex>

                {/* Stats Grid */}
                <Box style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <Flex align="center" gap="1">
                    <CheckCircledIcon width="14" height="14" color="gray" />
                    <Text size="1" color="gray">
                      {client.completedTasks}/{client.totalTasks} tasks
                    </Text>
                  </Flex>
                  <Flex align="center" gap="1">
                    <EnvelopeClosedIcon width="14" height="14" color="gray" />
                    <Text size="1" color="gray">
                      {client.lastCommunication ? 
                        new Date(client.lastCommunication).toLocaleDateString() : 
                        'No comm'}
                    </Text>
                  </Flex>
                </Box>

                {/* Project Value */}
                {client.projectValue > 0 && (
                  <Flex justify="between" align="center" pt="2" style={{ borderTop: '1px solid var(--gray-4)' }}>
                    <Text size="1" weight="medium">Value</Text>
                    <Text size="2" weight="bold" color="green">
                      ${client.projectValue.toLocaleString()}
                    </Text>
                  </Flex>
                )}
              </Flex>
            </Card>
          ))
          ) : null}
        </Box>

        {/* Empty State */}
        {filteredClients.length === 0 && !isLoading && (
          <Card style={{ textAlign: 'center', padding: '4rem' }}>
            <Text size="3" color="gray">
              {searchQuery || filterStatus !== 'all' 
                ? 'No clients found matching your criteria' 
                : 'No clients yet. Create your first client to get started!'}
            </Text>
          </Card>
        )}
      </Box>
    </div>
  );
};

export default ClientPortal; 