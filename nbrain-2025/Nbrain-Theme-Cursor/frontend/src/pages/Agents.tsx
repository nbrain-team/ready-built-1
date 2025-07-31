import { useState, useEffect } from 'react';
import { Box, Button, Card, Flex, Grid, Heading, Text, Badge, IconButton, Dialog } from '@radix-ui/themes';
import { PlusIcon, MagicWandIcon, RocketIcon, BarChartIcon, Pencil2Icon, GearIcon, TrashIcon } from '@radix-ui/react-icons';
import api from '../api';
import { AgentIdeator } from '../components/AgentIdeator';
import { AgentSpecification } from '../components/AgentSpecification';
import { AgentIdeatorEdit } from '../components/AgentIdeatorEdit';

interface AgentIdea {
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
}

const AGENT_TYPE_ICONS = {
  customer_service: <RocketIcon width={24} height={24} />,
  data_analysis: <BarChartIcon width={24} height={24} />,
  content_creation: <Pencil2Icon width={24} height={24} />,
  process_automation: <GearIcon width={24} height={24} />,
  other: <MagicWandIcon width={24} height={24} />
};

const AgentTypeColors = {
  customer_service: 'blue',
  data_analysis: 'green',
  content_creation: 'purple',
  process_automation: 'orange',
  other: 'gray'
} as const;

function Agents() {
  const [agentIdeas, setAgentIdeas] = useState<AgentIdea[]>([]);
  const [showIdeator, setShowIdeator] = useState(false);
  const [selectedIdea, setSelectedIdea] = useState<AgentIdea | null>(null);
  const [editingIdea, setEditingIdea] = useState<AgentIdea | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAgentIdeas();
  }, []);

  const fetchAgentIdeas = async () => {
    try {
      const response = await api.get('/agent-ideas');
      setAgentIdeas(response.data);
    } catch (error) {
      console.error('Error fetching agent ideas:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleIdeatorComplete = async (spec: any, conversation: any[]) => {
    console.log('handleIdeatorComplete called with spec:', spec);
    try {
      // Create the agent idea
      const response = await api.post('/agent-ideas', {
        ...spec,
        conversation_history: conversation,
        status: 'completed'  // Explicitly set status to completed
      });
      
      console.log('Agent idea created, response:', response.data);
      
      // Immediately set the selected idea to show it
      if (response.data && response.data.id) {
        setSelectedIdea(response.data);
        setShowIdeator(false);
        // Also refresh the list for consistency
        await fetchAgentIdeas();
      } else {
        console.error('Invalid response from server:', response);
        alert('There was an error saving your agent specification. Please try again.');
      }
    } catch (error: any) {
      console.error('Error saving agent idea:', error);
      alert(`Error: ${error.response?.data?.detail || error.message || 'Failed to save agent specification'}`);
    }
  };

  const deleteAgentIdea = async (id: string) => {
    if (!confirm('Are you sure you want to delete this agent idea?')) return;
    
    try {
      await api.delete(`/agent-ideas/${id}`);
      await fetchAgentIdeas();
    } catch (error) {
      console.error('Error deleting agent idea:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const handleEdit = (idea: AgentIdea) => {
    setEditingIdea(idea);
    setSelectedIdea(null);
  };

  const handleEditComplete = async (updatedSpec: AgentIdea) => {
    // Refresh the list
    await fetchAgentIdeas();
    // Show the updated spec
    setSelectedIdea(updatedSpec);
    setEditingIdea(null);
  };

  if (showIdeator) {
    return (
      <Box style={{ height: '100%', overflow: 'hidden' }}>
        <AgentIdeator 
          onClose={() => setShowIdeator(false)}
          onComplete={handleIdeatorComplete}
        />
      </Box>
    );
  }

  if (editingIdea) {
    return (
      <Box style={{ height: '100%', overflow: 'hidden' }}>
        <AgentIdeatorEdit
          spec={editingIdea}
          onClose={() => setEditingIdea(null)}
          onUpdate={handleEditComplete}
        />
      </Box>
    );
  }

  if (selectedIdea) {
    return (
      <Box style={{ height: '100%', overflow: 'auto' }}>
        <AgentSpecification
          spec={selectedIdea}
          onClose={() => setSelectedIdea(null)}
          onEdit={() => handleEdit(selectedIdea)}
        />
      </Box>
    );
  }

  return (
    <Box p="6" style={{ height: '100%', overflow: 'auto' }}>
      {/* Header */}
      <Flex justify="between" align="center" mb="6">
        <Box>
          <Heading size="8" mb="2">AI Agents</Heading>
          <Text size="3" color="gray">
            Design and manage your custom AI agents
          </Text>
        </Box>
        <Button size="3" onClick={() => setShowIdeator(true)}>
          <MagicWandIcon />
          New Agent Idea
        </Button>
      </Flex>

      {/* Agent Ideas Grid */}
      {isLoading ? (
        <Flex justify="center" align="center" style={{ minHeight: '200px' }}>
          <Text color="gray">Loading agent ideas...</Text>
        </Flex>
      ) : agentIdeas.length === 0 ? (
        <Flex justify="center" align="center" style={{ minHeight: '400px' }}>
          <Card style={{ textAlign: 'center', padding: '3rem', maxWidth: '500px' }}>
            <Heading size="5" mb="3">No Agent Ideas Yet</Heading>
            <Text color="gray" mb="4" style={{ display: 'block' }}>
              Start by creating your first AI agent specification using our intelligent ideator.
            </Text>
            <Button onClick={() => setShowIdeator(true)}>
              <PlusIcon />
              Create Your First Agent
            </Button>
          </Card>
        </Flex>
      ) : (
        <Grid columns={{ initial: '1', md: '2', lg: '3' }} gap="4">
          {agentIdeas.map((idea) => {
            const agentType = idea.agent_type || 'other';
            const typeColor = AgentTypeColors[agentType as keyof typeof AgentTypeColors] || 'gray';
            
            return (
              <Card 
                key={idea.id} 
                style={{ 
                  cursor: 'pointer', 
                  position: 'relative',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column'
                }}
                onClick={() => setSelectedIdea(idea)}
              >
                <Flex direction="column" gap="3" style={{ height: '100%' }}>
                  <Flex justify="between" align="start">
                    <Box style={{ minWidth: '40px' }}>
                      {AGENT_TYPE_ICONS[agentType as keyof typeof AGENT_TYPE_ICONS]}
                    </Box>
                    <Flex gap="2" align="center">
                      <Badge color={typeColor} variant="soft" size="1">
                        {agentType.replace('_', ' ')}
                      </Badge>
                      <IconButton 
                        size="1" 
                        variant="ghost" 
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteAgentIdea(idea.id);
                        }}
                      >
                        <TrashIcon />
                      </IconButton>
                    </Flex>
                  </Flex>
                  
                  <Box style={{ flex: 1 }}>
                    <Heading size="4" mb="2" style={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      lineHeight: '1.2'
                    }}>{idea.title}</Heading>
                    <Text size="2" color="gray" style={{ 
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      lineHeight: '1.4'
                    }}>
                      {idea.summary}
                    </Text>
                  </Box>
                  
                  <Flex justify="between" align="center" style={{ marginTop: 'auto' }}>
                    <Text size="1" color="gray">
                      {formatDate(idea.created_at)}
                    </Text>
                    <Badge color={idea.status === 'completed' ? 'green' : 'gray'} variant="soft" size="1">
                      {idea.status}
                    </Badge>
                  </Flex>
                </Flex>
              </Card>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}

export default Agents; 