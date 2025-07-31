import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Badge, Button, Select, IconButton } from '@radix-ui/themes';
import { PlayIcon, CheckIcon, Cross2Icon, ReloadIcon, EyeOpenIcon, TrashIcon } from '@radix-ui/react-icons';
import { AlertDialog } from '@radix-ui/themes';
import { Campaign, CampaignStatus } from './types';
import { CampaignCard } from './CampaignCard';
import api from '../../api';

interface CampaignsListProps {
  clientId: string;
  onViewCampaign: (campaign: Campaign) => void;
  onRefresh?: () => void;
}

export const CampaignsList: React.FC<CampaignsListProps> = ({ 
  clientId, 
  onViewCampaign,
  onRefresh 
}) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'processing' | 'ready' | 'failed'>('all');
  const [campaignToDelete, setCampaignToDelete] = useState<Campaign | null>(null);

  useEffect(() => {
    fetchCampaigns();
  }, [clientId]);

  useEffect(() => {
    // Poll for updates every 5 seconds if there are processing campaigns
    const interval = setInterval(() => {
      if (campaigns.some(c => c.status === CampaignStatus.PROCESSING)) {
        fetchCampaigns();
      }
    }, 10000);
    
    return () => clearInterval(interval);
  }, [campaigns, clientId]);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/social-media-automator/clients/${clientId}/campaigns`);
      setCampaigns(response.data);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    if (filter === 'all') return true;
    return campaign.status === filter;
  });

  const handleDelete = async (campaignId: string) => {
    try {
      await api.delete(`/api/social-media-automator/campaigns/${campaignId}`);
      setCampaignToDelete(null);
      fetchCampaigns();
      onRefresh?.();
    } catch (error) {
      console.error('Error deleting campaign:', error);
      // You can add toast notification here for error
    }
  };

  const handleNextStep = async (campaign: Campaign) => {
    // Handle navigation to next step based on current step
    const currentStep = (campaign as any).step || 1;
    
    switch (currentStep) {
      case 1:
        // Navigate to upload emails
        window.location.href = `/email-personalizer?campaignId=${campaign.id}`;
        break;
      case 2:
        // Navigate to generate emails
        window.location.href = `/email-personalizer?campaignId=${campaign.id}&step=generate`;
        break;
      case 3:
        // Navigate to review
        window.location.href = `/email-personalizer?campaignId=${campaign.id}&step=review`;
        break;
      case 4:
        // Navigate to send
        window.location.href = `/email-personalizer?campaignId=${campaign.id}&step=send`;
        break;
    }
  };

  const getStatusIcon = (status: CampaignStatus) => {
    switch (status) {
      case CampaignStatus.PROCESSING:
        return <ReloadIcon className="animate-spin" />;
      case CampaignStatus.READY:
        return <CheckIcon color="green" />;
      case CampaignStatus.FAILED:
        return <Cross2Icon color="red" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: CampaignStatus) => {
    switch (status) {
      case CampaignStatus.PROCESSING:
        return 'blue';
      case CampaignStatus.READY:
        return 'green';
      case CampaignStatus.FAILED:
        return 'red';
      default:
        return 'gray';
    }
  };

  if (loading) {
    return (
      <Box p="4">
        <Text>Loading campaigns...</Text>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Flex justify="between" align="center" mb="4">
        <Flex align="center" gap="3">
          <Text size="4" weight="bold">Campaigns</Text>
          <Badge size="2" variant="soft">{campaigns.length} total</Badge>
        </Flex>
        
        <Flex gap="2" align="center">
          <Select.Root value={filter} onValueChange={(value: any) => setFilter(value)}>
            <Select.Trigger />
            <Select.Content>
              <Select.Item value="all">All Campaigns</Select.Item>
              <Select.Item value="processing">In Progress</Select.Item>
              <Select.Item value="ready">Completed</Select.Item>
              <Select.Item value="failed">Failed</Select.Item>
            </Select.Content>
          </Select.Root>
          
          <IconButton 
            size="2" 
            variant="soft" 
            onClick={() => {
              fetchCampaigns();
              onRefresh?.();
            }}
          >
            <ReloadIcon />
          </IconButton>
        </Flex>
      </Flex>

      {/* Campaigns List */}
      <Flex direction="column" gap="3">
        {filteredCampaigns.length === 0 ? (
          <Card>
            <Flex align="center" justify="center" p="6">
              <Text color="gray">No campaigns found</Text>
            </Flex>
          </Card>
        ) : (
          filteredCampaigns.map(campaign => (
            <CampaignCard
              key={campaign.id}
              campaign={campaign}
              onView={() => onViewCampaign(campaign)}
              onDelete={() => setCampaignToDelete(campaign)}
              onNextStep={() => handleNextStep(campaign)}
            />
          ))
        )}
      </Flex>

      <AlertDialog.Root open={!!campaignToDelete}>
        <AlertDialog.Content maxWidth="450px">
          <AlertDialog.Title>Delete Campaign</AlertDialog.Title>
          <AlertDialog.Description size="2">
            Are you sure you want to delete "{campaignToDelete?.name}"? This action cannot be undone.
          </AlertDialog.Description>

          <Flex gap="3" mt="4" justify="end">
            <AlertDialog.Cancel>
              <Button variant="soft" color="gray" onClick={() => setCampaignToDelete(null)}>
                Cancel
              </Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button variant="solid" color="red" onClick={() => handleDelete(campaignToDelete!.id)}>
                Delete
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>

    </Box>
  );
}; 