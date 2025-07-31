import React, { useState, useEffect } from 'react';
import { Card, Flex, Heading, Text, Button, TextField, Badge, Tabs, Box, ScrollArea, IconButton } from '@radix-ui/themes';
import { MagnifyingGlassIcon, ReloadIcon, CheckCircledIcon, ExclamationTriangleIcon, RocketIcon, Cross2Icon } from '@radix-ui/react-icons';
import api from '../api';

interface AIInsightsProps {
  clientId: string;
  clientName: string;
}

const ClientAIInsights: React.FC<AIInsightsProps> = ({ clientId, clientName }) => {
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState<string | null>(null); // Track which analysis is loading
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any>(null);
  const [weeklyPulse, setWeeklyPulse] = useState<any>(null);
  const [commitments, setCommitments] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [suggestedTasks, setSuggestedTasks] = useState<any>(null);

  useEffect(() => {
    // Load existing analyses on mount
    loadExistingAnalyses();
  }, [clientId]);

  const loadExistingAnalyses = async () => {
    // Load all existing analyses in parallel
    await Promise.all([
      fetchWeeklySummary(false),
      fetchSentiment(false),
      fetchCommitments(false),
      fetchSuggestedTasks(false)
    ]);
  };

  const fetchWeeklySummary = async (generate: boolean = false) => {
    try {
      const endpoint = generate 
        ? `/clients/${clientId}/ai/weekly-summary/generate`
        : `/clients/${clientId}/ai/weekly-summary`;
      
      if (generate) setLoading('summary');
      
      const response = await api[generate ? 'post' : 'get'](endpoint);
      if (response.data.success) {
        setWeeklyPulse(response.data);
      }
    } catch (error) {
      console.error('Error fetching weekly summary:', error);
    } finally {
      if (generate) setLoading(null);
    }
  };

  const fetchCommitments = async (generate: boolean = false) => {
    try {
      const endpoint = generate 
        ? `/clients/${clientId}/ai/commitments/generate`
        : `/clients/${clientId}/ai/commitments`;
      
      if (generate) setLoading('commitments');
      
      const response = await api[generate ? 'post' : 'get'](endpoint);
      if (response.data.success) {
        // Handle both wrapped and unwrapped formats
        const data = response.data.data;
        if (data && typeof data === 'object' && 'commitments' in data) {
          // Wrapped format from saved analysis
          setCommitments({ ...response.data, data: data.commitments });
        } else {
          // Direct format from generation
          setCommitments(response.data);
        }
      }
    } catch (error) {
      console.error('Error fetching commitments:', error);
    } finally {
      if (generate) setLoading(null);
    }
  };

  const fetchSentiment = async (generate: boolean = false) => {
    try {
      const endpoint = generate 
        ? `/clients/${clientId}/ai/sentiment/generate`
        : `/clients/${clientId}/ai/sentiment`;
      
      if (generate) setLoading('sentiment');
      
      const response = await api[generate ? 'post' : 'get'](endpoint);
      if (response.data.success) {
        setSentiment(response.data);
      }
    } catch (error) {
      console.error('Error fetching sentiment:', error);
    } finally {
      if (generate) setLoading(null);
    }
  };

  const fetchSuggestedTasks = async (generate: boolean = false) => {
    try {
      const endpoint = generate 
        ? `/clients/${clientId}/ai/suggested-tasks/generate`
        : `/clients/${clientId}/ai/suggested-tasks`;
      
      if (generate) setLoading('tasks');
      
      const response = await api[generate ? 'post' : 'get'](endpoint);
      if (response.data.success) {
        // Handle both wrapped and unwrapped formats
        const data = response.data.data;
        if (data && typeof data === 'object' && 'tasks' in data) {
          // Wrapped format from saved analysis
          setSuggestedTasks({ ...response.data, data: data.tasks });
        } else {
          // Direct format from generation
          setSuggestedTasks(response.data);
        }
      }
    } catch (error) {
      console.error('Error fetching suggested tasks:', error);
    } finally {
      if (generate) setLoading(null);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading('search');
    try {
      const response = await api.post(`/clients/${clientId}/ai/search`, {
        query: searchQuery
      });
      if (response.data.success) {
        setSearchResults(response.data.data);
        setActiveTab('search');
      }
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setLoading(null);
    }
  };

  const createTaskFromSuggestion = async (task: any) => {
    try {
      const response = await api.post(`/clients/${clientId}/ai/create-task`, {
        title: task.title,
        description: `AI Suggested: ${task.reason}\n\nSource: ${task.source?.subject || ''}`,
        priority: task.priority,
        due_date: task.due_date
      });
      if (response.data.success) {
        // Remove from suggestions
        if (suggestedTasks?.data) {
          setSuggestedTasks({
            ...suggestedTasks,
            data: suggestedTasks.data.filter((t: any) => t !== task)
          });
        }
      }
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };

  const deleteAnalysis = async (analysisType: string) => {
    try {
      await api.delete(`/clients/${clientId}/ai/${analysisType}`);
      // Clear the state for the deleted analysis
      switch(analysisType) {
        case 'weekly-summary':
          setWeeklyPulse(null);
          break;
        case 'commitments':
          setCommitments(null);
          break;
        case 'sentiment':
          setSentiment(null);
          break;
        case 'suggested-tasks':
          setSuggestedTasks(null);
          break;
      }
    } catch (error) {
      console.error(`Error deleting ${analysisType}:`, error);
    }
  };

  const deleteCommitment = async (index: number) => {
    if (!commitments?.data) return;
    
    const updatedCommitments = {
      ...commitments,
      data: commitments.data.filter((_: any, i: number) => i !== index)
    };
    setCommitments(updatedCommitments);
    
    // Optionally save the updated list back to the server
    try {
      await api.put(`/clients/${clientId}/ai/commitments`, {
        data: updatedCommitments.data
      });
    } catch (error) {
      console.error('Error updating commitments:', error);
    }
  };

  const deleteSuggestedTask = async (index: number) => {
    if (!suggestedTasks?.data) return;
    
    const updatedTasks = {
      ...suggestedTasks,
      data: suggestedTasks.data.filter((_: any, i: number) => i !== index)
    };
    setSuggestedTasks(updatedTasks);
    
    // Optionally save the updated list back to the server
    try {
      await api.put(`/clients/${clientId}/ai/suggested-tasks`, {
        data: updatedTasks.data
      });
    } catch (error) {
      console.error('Error updating suggested tasks:', error);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch(sentiment) {
      case 'positive': return 'green';
      case 'negative': return 'red';
      default: return 'gray';
    }
  };

  const getSentimentIcon = (trend: string) => {
    switch(trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      default: return '➡️';
    }
  };

  const formatGeneratedInfo = (data: any) => {
    if (!data?.generated_at) return null;
    const date = new Date(data.generated_at);
    return (
      <Text size="1" color="gray">
        Generated {date.toLocaleDateString()} at {date.toLocaleTimeString()}
      </Text>
    );
  };

  return (
    <Card>
      <Flex direction="column" gap="4">
        <Heading size="4">AI-Powered Insights</Heading>
        
        {/* Search Bar */}
        <Flex gap="2">
          <TextField.Root 
            style={{ flex: 1 }}
            placeholder="Ask anything about this client..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button 
            onClick={handleSearch} 
            disabled={loading === 'search'}
          >
            {loading === 'search' ? <ReloadIcon className="animate-spin" /> : <MagnifyingGlassIcon />}
            Search
          </Button>
        </Flex>

        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Trigger value="summary">Weekly Pulse</Tabs.Trigger>
            <Tabs.Trigger value="commitments">Commitments</Tabs.Trigger>
            <Tabs.Trigger value="sentiment">Sentiment</Tabs.Trigger>
            <Tabs.Trigger value="tasks">Suggested Tasks</Tabs.Trigger>
            {searchResults && <Tabs.Trigger value="search">Search Results</Tabs.Trigger>}
          </Tabs.List>

          <Box pt="3">
            <Tabs.Content value="summary">
              {weeklyPulse?.data ? (
                <Card style={{ position: 'relative' }}>
                  <Flex direction="column" gap="3">
                    <Flex justify="between" align="center">
                      <Heading size="3">{weeklyPulse.data.title}</Heading>
                      <Button 
                        size="1" 
                        variant="soft" 
                        onClick={() => fetchWeeklySummary(true)}
                        disabled={loading === 'summary'}
                      >
                        {loading === 'summary' ? <ReloadIcon className="animate-spin" /> : <ReloadIcon />}
                        Regenerate
                      </Button>
                    </Flex>
                    {formatGeneratedInfo(weeklyPulse)}
                    <Text>{weeklyPulse.data.summary}</Text>
                    
                    {weeklyPulse.data.key_points && (
                      <Box>
                        <Text weight="bold" size="2">Key Points:</Text>
                        <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                          {weeklyPulse.data.key_points.map((point: string, i: number) => (
                            <li key={i}><Text size="2">{point}</Text></li>
                          ))}
                        </ul>
                      </Box>
                    )}
                    
                    {weeklyPulse.data.action_items && weeklyPulse.data.action_items.length > 0 && (
                      <Box>
                        <Text weight="bold" size="2">Recommended Actions:</Text>
                        <Flex direction="column" gap="2" mt="2">
                          {weeklyPulse.data.action_items.map((item: string, i: number) => (
                            <Badge key={i} color="blue" variant="soft">
                              {item}
                            </Badge>
                          ))}
                        </Flex>
                      </Box>
                    )}
                    
                    {/* Delete button in lower left */}
                    <IconButton
                      size="1"
                      variant="ghost"
                      color="gray"
                      style={{ 
                        position: 'absolute', 
                        bottom: '8px', 
                        left: '8px',
                        opacity: 0.6,
                        transition: 'opacity 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                      onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
                      onClick={() => deleteAnalysis('weekly-summary')}
                    >
                      <Cross2Icon />
                    </IconButton>
                  </Flex>
                </Card>
              ) : (
                <Card>
                  <Flex direction="column" gap="3" align="center" py="4">
                    <Text color="gray">No weekly summary available</Text>
                    <Button 
                      onClick={() => fetchWeeklySummary(true)}
                      disabled={loading === 'summary'}
                    >
                      {loading === 'summary' ? <ReloadIcon className="animate-spin" /> : null}
                      Generate Weekly Summary
                    </Button>
                  </Flex>
                </Card>
              )}
            </Tabs.Content>

            <Tabs.Content value="commitments">
              {commitments?.data ? (
                <ScrollArea style={{ height: '400px' }}>
                  <Flex direction="column" gap="3">
                    <Flex justify="between" align="center">
                      <Heading size="3">Tracked Commitments</Heading>
                      <Button 
                        size="1" 
                        variant="soft" 
                        onClick={() => fetchCommitments(true)}
                        disabled={loading === 'commitments'}
                      >
                        {loading === 'commitments' ? <ReloadIcon className="animate-spin" /> : <ReloadIcon />}
                        Regenerate
                      </Button>
                    </Flex>
                    {formatGeneratedInfo(commitments)}
                    
                    {commitments.data.length > 0 ? (
                      commitments.data.map((commitment: any, i: number) => (
                        <Card key={i} style={{ position: 'relative' }}>
                          <Flex direction="column" gap="2">
                            <Flex justify="between" align="start">
                              <Text weight="bold">{commitment.commitment}</Text>
                              {commitment.is_overdue && (
                                <Badge color="red" variant="soft">Overdue</Badge>
                              )}
                            </Flex>
                            <Flex gap="4">
                              <Text size="2" color="gray">Due: {commitment.due_date}</Text>
                              <Text size="2" color="gray">Who: {commitment.responsible}</Text>
                            </Flex>
                            <Text size="1" color="gray">From: {commitment.source.date}</Text>
                            
                            {/* Delete button in lower left */}
                            <IconButton
                              size="1"
                              variant="ghost"
                              color="gray"
                              style={{ 
                                position: 'absolute', 
                                bottom: '8px', 
                                left: '8px',
                                opacity: 0.6,
                                transition: 'opacity 0.2s'
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                              onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
                              onClick={() => deleteCommitment(i)}
                            >
                              <Cross2Icon />
                            </IconButton>
                          </Flex>
                        </Card>
                      ))
                    ) : (
                      <Text color="gray">No commitments found in recent communications</Text>
                    )}
                  </Flex>
                </ScrollArea>
              ) : (
                <Card>
                  <Flex direction="column" gap="3" align="center" py="4">
                    <Text color="gray">No commitment analysis available</Text>
                    <Button 
                      onClick={() => fetchCommitments(true)}
                      disabled={loading === 'commitments'}
                    >
                      {loading === 'commitments' ? <ReloadIcon className="animate-spin" /> : null}
                      Extract Commitments
                    </Button>
                  </Flex>
                </Card>
              )}
            </Tabs.Content>

            <Tabs.Content value="sentiment">
              {sentiment?.data ? (
                <Card style={{ position: 'relative' }}>
                  <Flex direction="column" gap="3">
                    <Flex justify="between" align="center">
                      <Heading size="3">Client Sentiment Analysis</Heading>
                      <Button 
                        size="1" 
                        variant="soft" 
                        onClick={() => fetchSentiment(true)}
                        disabled={loading === 'sentiment'}
                      >
                        {loading === 'sentiment' ? <ReloadIcon className="animate-spin" /> : <ReloadIcon />}
                        Regenerate
                      </Button>
                    </Flex>
                    {formatGeneratedInfo(sentiment)}
                    
                    {sentiment.data.current_sentiment && (
                      <Flex align="center" gap="3">
                        <Badge 
                          size="2" 
                          color={getSentimentColor(sentiment.data.current_sentiment.sentiment)}
                        >
                          {sentiment.data.current_sentiment.sentiment}
                        </Badge>
                        <Text size="2">
                          {getSentimentIcon(sentiment.data.trend)} Trend: {sentiment.data.trend}
                        </Text>
                        <Text size="2" color="gray">
                          Score: {sentiment.data.average_score.toFixed(1)}/10
                        </Text>
                      </Flex>
                    )}
                    
                    {sentiment.data.concerns && sentiment.data.concerns.length > 0 && (
                      <Box>
                        <Text weight="bold" size="2" color="red">
                          <ExclamationTriangleIcon style={{ display: 'inline', marginRight: '4px' }} />
                          Concerns Detected:
                        </Text>
                        <Flex direction="column" gap="1" mt="2">
                          {sentiment.data.concerns.map((concern: string, i: number) => (
                            <Text key={i} size="2" color="gray">• {concern}</Text>
                          ))}
                        </Flex>
                      </Box>
                    )}
                    
                    {/* Delete button in lower left */}
                    <IconButton
                      size="1"
                      variant="ghost"
                      color="gray"
                      style={{ 
                        position: 'absolute', 
                        bottom: '8px', 
                        left: '8px',
                        opacity: 0.6,
                        transition: 'opacity 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                      onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
                      onClick={() => deleteAnalysis('sentiment')}
                    >
                      <Cross2Icon />
                    </IconButton>
                  </Flex>
                </Card>
              ) : (
                <Card>
                  <Flex direction="column" gap="3" align="center" py="4">
                    <Text color="gray">No sentiment analysis available</Text>
                    <Button 
                      onClick={() => fetchSentiment(true)}
                      disabled={loading === 'sentiment'}
                    >
                      {loading === 'sentiment' ? <ReloadIcon className="animate-spin" /> : null}
                      Analyze Sentiment
                    </Button>
                  </Flex>
                </Card>
              )}
            </Tabs.Content>

            <Tabs.Content value="tasks">
              {suggestedTasks?.data ? (
                <ScrollArea style={{ height: '400px' }}>
                  <Flex direction="column" gap="3">
                    <Flex justify="between" align="center">
                      <Heading size="3">AI-Suggested Tasks</Heading>
                      <Button 
                        size="1" 
                        variant="soft" 
                        onClick={() => fetchSuggestedTasks(true)}
                        disabled={loading === 'tasks'}
                      >
                        {loading === 'tasks' ? <ReloadIcon className="animate-spin" /> : <ReloadIcon />}
                        Regenerate
                      </Button>
                    </Flex>
                    {formatGeneratedInfo(suggestedTasks)}
                    
                    {suggestedTasks.data.length > 0 ? (
                      suggestedTasks.data.map((task: any, i: number) => (
                        <Card key={i} style={{ position: 'relative' }}>
                          <Flex justify="between" align="start">
                            <Flex direction="column" gap="2" style={{ flex: 1 }}>
                              <Text weight="bold">{task.title}</Text>
                              <Text size="2" color="gray">{task.reason}</Text>
                              <Flex gap="2">
                                <Badge color={task.priority === 'high' ? 'red' : 'blue'} variant="soft">
                                  {task.priority}
                                </Badge>
                                {task.due_date && (
                                  <Text size="2" color="gray">Due: {task.due_date}</Text>
                                )}
                              </Flex>
                            </Flex>
                            <Button 
                              size="2" 
                              onClick={() => createTaskFromSuggestion(task)}
                            >
                              <RocketIcon />
                              Create Task
                            </Button>
                          </Flex>
                          
                          {/* Delete button in lower left */}
                          <IconButton
                            size="1"
                            variant="ghost"
                            color="gray"
                            style={{ 
                              position: 'absolute', 
                              bottom: '8px', 
                              left: '8px',
                              opacity: 0.6,
                              transition: 'opacity 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                            onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
                            onClick={() => deleteSuggestedTask(i)}
                          >
                            <Cross2Icon />
                          </IconButton>
                        </Card>
                      ))
                    ) : (
                      <Text color="gray">No task suggestions available</Text>
                    )}
                  </Flex>
                </ScrollArea>
              ) : (
                <Card>
                  <Flex direction="column" gap="3" align="center" py="4">
                    <Text color="gray">No task suggestions available</Text>
                    <Button 
                      onClick={() => fetchSuggestedTasks(true)}
                      disabled={loading === 'tasks'}
                    >
                      {loading === 'tasks' ? <ReloadIcon className="animate-spin" /> : null}
                      Generate Task Suggestions
                    </Button>
                  </Flex>
                </Card>
              )}
            </Tabs.Content>

            <Tabs.Content value="search">
              {searchResults && (
                <ScrollArea style={{ height: '400px' }}>
                  <Flex direction="column" gap="3">
                    <Text size="2" color="gray">
                      Found {searchResults.total_found} results for "{searchResults.query}"
                    </Text>
                    {searchResults.results.map((result: any, i: number) => (
                      <Card key={i}>
                        <Flex direction="column" gap="2">
                          <Flex justify="between">
                            <Badge>{result.type}</Badge>
                            <Text size="1" color="gray">{result.date}</Text>
                          </Flex>
                          {result.subject && (
                            <Text weight="bold" size="2">{result.subject}</Text>
                          )}
                          <Text size="2">{result.content}</Text>
                          <Text size="1" color="gray">From: {result.from}</Text>
                        </Flex>
                      </Card>
                    ))}
                  </Flex>
                </ScrollArea>
              )}
            </Tabs.Content>
          </Box>
        </Tabs.Root>
      </Flex>
    </Card>
  );
};

export default ClientAIInsights; 