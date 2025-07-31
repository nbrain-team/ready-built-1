import React from 'react';
import { Box, Flex, Text, Card, Badge, Button, IconButton } from '@radix-ui/themes';
import { CheckIcon, Cross2Icon, PlayIcon, EyeOpenIcon, TrashIcon, EnvelopeClosedIcon, FileTextIcon, MagicWandIcon, CheckCircledIcon } from '@radix-ui/react-icons';
import { Campaign, CampaignStatus } from './types';

interface CampaignCardProps {
  campaign: Campaign & { step?: number };
  onView: () => void;
  onDelete: () => void;
  onNextStep?: () => void;
}

interface CampaignStep {
  number: number;
  label: string;
  icon: React.ReactNode;
  action?: string;
}

const CAMPAIGN_STEPS: CampaignStep[] = [
  { number: 1, label: 'Campaign Created', icon: <CheckCircledIcon /> },
  { number: 2, label: 'Upload & Enrich Emails', icon: <FileTextIcon />, action: 'Upload Emails' },
  { number: 3, label: 'Create Personalized Emails', icon: <MagicWandIcon />, action: 'Generate Emails' },
  { number: 4, label: 'Review & Approve', icon: <EyeOpenIcon />, action: 'Review' },
  { number: 5, label: 'Send Emails', icon: <EnvelopeClosedIcon />, action: 'Send Campaign' }
];

export const CampaignCard: React.FC<CampaignCardProps> = ({
  campaign,
  onView,
  onDelete,
  onNextStep
}) => {
  const currentStep = campaign.step || 1;
  
  const getStatusIcon = (status: CampaignStatus) => {
    switch (status) {
      case CampaignStatus.PROCESSING:
        return <PlayIcon className="animate-spin" />;
      case CampaignStatus.READY:
        return <CheckIcon />;
      case CampaignStatus.FAILED:
        return <Cross2Icon />;
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

  const getCurrentStepAction = () => {
    const step = CAMPAIGN_STEPS.find(s => s.number === currentStep);
    return step?.action;
  };

  return (
    <Card style={{ width: '100%' }}>
      {/* Progress Bar */}
      <Box style={{ 
        padding: '1rem', 
        borderBottom: '1px solid var(--gray-4)',
        backgroundColor: 'var(--gray-1)'
      }}>
        <Flex direction="column" gap="3">
          <Text size="1" weight="medium" color="gray">Campaign Progress</Text>
          
          {/* Steps */}
          <Flex align="center" gap="2">
            {CAMPAIGN_STEPS.map((step, index) => (
              <React.Fragment key={step.number}>
                {/* Step Circle */}
                <Flex
                  align="center"
                  justify="center"
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: currentStep >= step.number ? 'var(--green-9)' : 'var(--gray-5)',
                    color: 'white',
                    flexShrink: 0,
                    position: 'relative'
                  }}
                >
                  {currentStep > step.number ? (
                    <CheckIcon />
                  ) : (
                    <Text size="2" weight="bold">{step.number}</Text>
                  )}
                  
                  {/* Step Label */}
                  <Text 
                    size="1" 
                    style={{ 
                      position: 'absolute',
                      top: '40px',
                      whiteSpace: 'nowrap',
                      color: currentStep >= step.number ? 'var(--gray-12)' : 'var(--gray-10)',
                      fontWeight: currentStep === step.number ? 'bold' : 'normal'
                    }}
                  >
                    {step.label}
                  </Text>
                </Flex>
                
                {/* Connector Line */}
                {index < CAMPAIGN_STEPS.length - 1 && (
                  <Box
                    style={{
                      flex: 1,
                      height: '2px',
                      backgroundColor: currentStep > step.number ? 'var(--green-9)' : 'var(--gray-4)',
                      margin: '0 0.5rem'
                    }}
                  />
                )}
              </React.Fragment>
            ))}
          </Flex>
          
          {/* Action Button */}
          {currentStep < 5 && getCurrentStepAction() && (
            <Flex justify="end" style={{ marginTop: '1rem' }}>
              <Button 
                size="2" 
                variant="solid"
                onClick={onNextStep}
                disabled={campaign.status === CampaignStatus.PROCESSING}
              >
                {getCurrentStepAction()}
              </Button>
            </Flex>
          )}
        </Flex>
      </Box>

      {/* Campaign Details */}
      <Box style={{ padding: '1rem' }}>
        <Flex justify="between" align="center">
          <Flex direction="column" gap="1">
            <Flex align="center" gap="2">
              <Text weight="medium" size="3">{campaign.name}</Text>
              {getStatusIcon(campaign.status)}
            </Flex>
            
            <Flex gap="3" align="center">
              <Badge color={getStatusColor(campaign.status)} variant="soft">
                {campaign.status === CampaignStatus.PROCESSING ? 'Processing' : campaign.status}
              </Badge>
              
              {campaign.duration_weeks && (
                <Text size="1" color="gray">
                  {campaign.duration_weeks} weeks
                </Text>
              )}
              
              <Text size="1" color="gray">
                Created {new Date(campaign.created_at).toLocaleDateString()}
              </Text>
            </Flex>
          </Flex>
          
          <Flex align="center" gap="2">
            <Button 
              size="2" 
              variant="ghost"
              onClick={onView}
              disabled={campaign.status === CampaignStatus.PROCESSING}
            >
              <EyeOpenIcon /> View Details
            </Button>
            <IconButton 
              size="2" 
              variant="ghost" 
              color="red"
              onClick={onDelete}
            >
              <TrashIcon />
            </IconButton>
          </Flex>
        </Flex>
      </Box>
    </Card>
  );
}; 