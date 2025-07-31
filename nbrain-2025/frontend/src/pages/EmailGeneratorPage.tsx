import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, Button, Card, Tabs, Badge, TextArea, Select } from '@radix-ui/themes';
import { UploadIcon, MagicWandIcon, EnvelopeClosedIcon, CheckIcon } from '@radix-ui/react-icons';
import { useSearchParams } from 'react-router-dom';
import { AnalyticsCard } from '../components/SocialMediaAutomator/AnalyticsCard';
import api from '../api';

interface EmailTemplate {
  id: string;
  subject: string;
  content: string;
  recipient: string;
  personalization_data: Record<string, any>;
  status: 'draft' | 'approved' | 'sent';
}

interface Campaign {
  id: string;
  name: string;
  step: number;
}

export const EmailGeneratorPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const campaignId = searchParams.get('campaignId');
  const step = searchParams.get('step') || 'upload';
  
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [emails, setEmails] = useState<EmailTemplate[]>([]);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<EmailTemplate | null>(null);
  const [activeTab, setActiveTab] = useState(step);
  const [analyticsData, setAnalyticsData] = useState({
    emailEnrichmentRate: 0,
    phoneEnrichmentRate: 0,
    totalEmails: 0,
    totalPhones: 0,
    enrichedEmails: 0,
    enrichedPhones: 0
  });

  useEffect(() => {
    if (campaignId) {
      fetchCampaign();
      fetchEmails();
    }
  }, [campaignId]);

  const fetchCampaign = async () => {
    try {
      const response = await api.get(`/api/social-media-automator/campaigns/${campaignId}`);
      setCampaign(response.data);
    } catch (error) {
      console.error('Error fetching campaign:', error);
    }
  };

  const fetchEmails = async () => {
    try {
      const response = await api.get(`/api/social-media-automator/campaigns/${campaignId}/emails`);
      setEmails(response.data);
      
      // Fetch analytics data
      const analyticsResponse = await api.get(`/api/social-media-automator/campaigns/${campaignId}/analytics`);
      if (analyticsResponse.data) {
        setAnalyticsData(analyticsResponse.data);
      }
    } catch (error) {
      console.error('Error fetching emails:', error);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleUploadAndEnrich = async () => {
    if (!uploadedFile || !campaignId) return;

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('campaign_id', campaignId);

    try {
      await api.post('/api/social-media-automator/emails/upload', formData);
      setActiveTab('generate');
      fetchEmails();
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleGenerateEmails = async () => {
    setIsGenerating(true);
    try {
      await api.post(`/api/social-media-automator/campaigns/${campaignId}/generate-emails`);
      setActiveTab('review');
      fetchEmails();
    } catch (error) {
      console.error('Error generating emails:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApproveEmail = async (emailId: string) => {
    try {
      await api.put(`/api/social-media-automator/emails/${emailId}`, { status: 'approved' });
      fetchEmails();
    } catch (error) {
      console.error('Error approving email:', error);
    }
  };

  const handleSendCampaign = async () => {
    try {
      await api.post(`/api/social-media-automator/campaigns/${campaignId}/send`);
      alert('Campaign sent successfully!');
    } catch (error) {
      console.error('Error sending campaign:', error);
    }
  };

  return (
    <Box p="6">
      <Flex direction="column" gap="4">
        {/* Header */}
        <Flex justify="between" align="center">
          <Box>
            <Text size="6" weight="bold">Email Campaign Generator</Text>
            {campaign && (
              <Text size="2" color="gray">Campaign: {campaign.name}</Text>
            )}
          </Box>
          <Button variant="ghost" onClick={() => window.history.back()}>
            Back to Campaigns
          </Button>
        </Flex>

        {/* Tabs */}
        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Trigger value="upload">
              <UploadIcon /> Upload & Enrich
            </Tabs.Trigger>
            <Tabs.Trigger value="generate" disabled={emails.length === 0}>
              <MagicWandIcon /> Generate Emails
            </Tabs.Trigger>
            <Tabs.Trigger value="review" disabled={emails.length === 0}>
              <CheckIcon /> Review & Approve
            </Tabs.Trigger>
            <Tabs.Trigger value="send" disabled={emails.filter(e => e.status === 'approved').length === 0}>
              <EnvelopeClosedIcon /> Send Campaign
            </Tabs.Trigger>
            <Tabs.Trigger value="analytics">
              Analytics
            </Tabs.Trigger>
          </Tabs.List>

          {/* Upload Tab */}
          <Tabs.Content value="upload">
            <Card size="3">
              <Flex direction="column" gap="4">
                <Text size="4" weight="medium">Upload Email List</Text>
                <Text size="2" color="gray">
                  Upload a CSV file containing recipient information. We'll enrich the data with additional context.
                </Text>
                
                <Box>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    id="file-upload"
                  />
                  <label htmlFor="file-upload">
                    <Box style={{ display: 'inline-block' }}>
                      <Button variant="outline" style={{ cursor: 'pointer' }}>
                        <UploadIcon /> Choose File
                      </Button>
                    </Box>
                  </label>
                  {uploadedFile && (
                    <Text size="2" ml="3">{uploadedFile.name}</Text>
                  )}
                </Box>

                <Button 
                  size="3" 
                  disabled={!uploadedFile}
                  onClick={handleUploadAndEnrich}
                >
                  Upload & Enrich Data
                </Button>
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Generate Tab */}
          <Tabs.Content value="generate">
            <Card size="3">
              <Flex direction="column" gap="4">
                <Text size="4" weight="medium">Generate Personalized Emails</Text>
                <Text size="2" color="gray">
                  AI will create personalized emails for each recipient based on their enriched data.
                </Text>
                
                <Box>
                  <Text size="2" weight="medium">Recipients: {emails.length}</Text>
                </Box>

                <Button 
                  size="3" 
                  onClick={handleGenerateEmails}
                  disabled={isGenerating}
                >
                  {isGenerating ? 'Generating...' : 'Generate Emails'}
                </Button>
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Review Tab */}
          <Tabs.Content value="review">
            <Flex direction="column" gap="4">
              <Card size="3">
                <Text size="4" weight="medium">Review & Approve Emails</Text>
              </Card>

              {/* Email List */}
              <Flex direction="column" gap="3">
                {emails.map((email) => (
                  <Card key={email.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedEmail(email)}>
                    <Flex justify="between" align="center">
                      <Box>
                        <Text weight="medium">{email.recipient}</Text>
                        <Text size="2" color="gray">{email.subject}</Text>
                      </Box>
                      <Flex gap="2" align="center">
                        <Badge color={email.status === 'approved' ? 'green' : 'gray'}>
                          {email.status}
                        </Badge>
                        {email.status !== 'approved' && (
                          <Button size="1" onClick={(e) => {
                            e.stopPropagation();
                            handleApproveEmail(email.id);
                          }}>
                            Approve
                          </Button>
                        )}
                      </Flex>
                    </Flex>
                  </Card>
                ))}
              </Flex>
            </Flex>
          </Tabs.Content>

          {/* Send Tab */}
          <Tabs.Content value="send">
            <Card size="3">
              <Flex direction="column" gap="4">
                <Text size="4" weight="medium">Send Campaign</Text>
                
                <Box>
                  <Text size="2">
                    Ready to send: {emails.filter(e => e.status === 'approved').length} / {emails.length} emails
                  </Text>
                </Box>

                <Select.Root defaultValue="now">
                  <Select.Trigger placeholder="Send timing" />
                  <Select.Content>
                    <Select.Item value="now">Send Now</Select.Item>
                    <Select.Item value="schedule">Schedule for Later</Select.Item>
                  </Select.Content>
                </Select.Root>

                <Button 
                  size="3" 
                  color="green"
                  onClick={handleSendCampaign}
                  disabled={emails.filter(e => e.status === 'approved').length === 0}
                >
                  <EnvelopeClosedIcon /> Send Campaign
                </Button>
              </Flex>
            </Card>
          </Tabs.Content>

          {/* Analytics Tab */}
          <Tabs.Content value="analytics">
            <AnalyticsCard data={analyticsData} />
          </Tabs.Content>
        </Tabs.Root>

        {/* Email Preview Modal */}
        {selectedEmail && (
          <Box
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000
            }}
            onClick={() => setSelectedEmail(null)}
          >
            <Card 
              size="4" 
              style={{ 
                width: '600px', 
                maxHeight: '80vh', 
                overflow: 'auto' 
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <Flex direction="column" gap="4">
                <Flex justify="between" align="center">
                  <Text size="4" weight="medium">Email Preview</Text>
                  <Button variant="ghost" onClick={() => setSelectedEmail(null)}>
                    Close
                  </Button>
                </Flex>
                
                <Box>
                  <Text size="2" weight="medium">To:</Text>
                  <Text>{selectedEmail.recipient}</Text>
                </Box>
                
                <Box>
                  <Text size="2" weight="medium">Subject:</Text>
                  <Text>{selectedEmail.subject}</Text>
                </Box>
                
                <Box>
                  <Text size="2" weight="medium">Content:</Text>
                  <Box style={{ 
                    padding: '1rem', 
                    backgroundColor: 'var(--gray-2)', 
                    borderRadius: '8px',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {selectedEmail.content}
                  </Box>
                </Box>
                
                <Flex gap="2" justify="end">
                  <Button variant="outline" onClick={() => setSelectedEmail(null)}>
                    Cancel
                  </Button>
                  <Button 
                    color="green"
                    onClick={() => {
                      handleApproveEmail(selectedEmail.id);
                      setSelectedEmail(null);
                    }}
                    disabled={selectedEmail.status === 'approved'}
                  >
                    {selectedEmail.status === 'approved' ? 'Approved' : 'Approve Email'}
                  </Button>
                </Flex>
              </Flex>
            </Card>
          </Box>
        )}
      </Flex>
    </Box>
  );
}; 