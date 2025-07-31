import React, { useState, useEffect } from 'react';
import { Dialog, Button, Flex, Text, TextField, Box, IconButton, AlertDialog, Badge } from '@radix-ui/themes';
import { Cross2Icon, TrashIcon, PlusIcon } from '@radix-ui/react-icons';
import api from '../api';
import { useNavigate } from 'react-router-dom';

interface EditClientDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  client: any;
  onUpdate: () => void;
}

const EditClientDialog: React.FC<EditClientDialogProps> = ({ 
  open, 
  onOpenChange, 
  client,
  onUpdate 
}) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    company_website: '',
    domain: '',
    industry: '',
    project_value: ''
  });
  const [syncEmails, setSyncEmails] = useState<string[]>([]);
  const [newSyncEmail, setNewSyncEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (client) {
      setFormData({
        name: client.name || '',
        primary_contact_name: client.primaryContactName || '',
        primary_contact_email: client.primaryContactEmail || '',
        primary_contact_phone: client.primaryContactPhone || '',
        company_website: client.companyWebsite || '',
        domain: client.domain || '',
        industry: client.industry || '',
        project_value: client.projectValue?.toString() || ''
      });
      setSyncEmails(client.syncEmailAddresses || []);
    }
  }, [client]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Auto-extract domain from email or website
    if (name === 'primary_contact_email' && value.includes('@')) {
      const emailDomain = value.split('@')[1];
      if (emailDomain && !formData.domain) {
        setFormData(prev => ({
          ...prev,
          domain: emailDomain
        }));
      }
    } else if (name === 'company_website' && value) {
      const websiteDomain = value
        .replace('https://', '')
        .replace('http://', '')
        .replace('www.', '')
        .split('/')[0];
      if (websiteDomain && !formData.domain) {
        setFormData(prev => ({
          ...prev,
          domain: websiteDomain
        }));
      }
    }
  };

  const handleAddSyncEmail = () => {
    if (newSyncEmail && newSyncEmail.includes('@') && !syncEmails.includes(newSyncEmail)) {
      setSyncEmails([...syncEmails, newSyncEmail]);
      setNewSyncEmail('');
    }
  };

  const handleRemoveSyncEmail = (email: string) => {
    setSyncEmails(syncEmails.filter(e => e !== email));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const payload = {
        ...formData,
        project_value: formData.project_value ? parseFloat(formData.project_value) : null,
        sync_email_addresses: syncEmails
      };

      console.log('Sending PUT request to:', `/clients/${client.id}`);
      console.log('Payload:', payload);

      const response = await api.put(`/clients/${client.id}`, payload);
      console.log('Update successful:', response.data);
      
      onUpdate();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Error updating client:', error);
      console.error('Error response:', error.response);
      console.error('Error status:', error.response?.status);
      console.error('Error data:', error.response?.data);
      alert(`Failed to update client: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    
    try {
      await api.delete(`/clients/${client.id}`);
      onOpenChange(false);
      navigate('/clients');
    } catch (error: any) {
      console.error('Error deleting client:', error);
      alert(`Failed to delete client: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  return (
    <>
      <Dialog.Root open={open} onOpenChange={onOpenChange}>
        <Dialog.Content style={{ maxWidth: 500 }}>
          <Dialog.Title>Edit Client Information</Dialog.Title>
          <Dialog.Description size="2" mb="4">
            Update client details and contact information
          </Dialog.Description>

          <form onSubmit={handleSubmit}>
            <Flex direction="column" gap="4">
              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Company Name
                </Text>
                <TextField.Root
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter company name"
                  required
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Primary Contact Name
                </Text>
                <TextField.Root
                  name="primary_contact_name"
                  value={formData.primary_contact_name}
                  onChange={handleChange}
                  placeholder="John Doe"
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Primary Contact Email
                </Text>
                <TextField.Root
                  name="primary_contact_email"
                  type="email"
                  value={formData.primary_contact_email}
                  onChange={handleChange}
                  placeholder="john@company.com"
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Primary Contact Phone
                </Text>
                <TextField.Root
                  name="primary_contact_phone"
                  value={formData.primary_contact_phone}
                  onChange={handleChange}
                  placeholder="+1 (555) 123-4567"
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Company Website
                </Text>
                <TextField.Root
                  name="company_website"
                  value={formData.company_website}
                  onChange={handleChange}
                  placeholder="https://company.com"
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Primary Domain <Text size="1" color="gray">(fallback for sync)</Text>
                </Text>
                <TextField.Root
                  name="domain"
                  value={formData.domain}
                  onChange={handleChange}
                  placeholder="company.com"
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Email Addresses for Sync <Text size="1" color="green">(NEW: Add specific emails to sync)</Text>
                </Text>
                <Flex gap="2" mb="2">
                  <TextField.Root
                    type="email"
                    value={newSyncEmail}
                    onChange={(e) => setNewSyncEmail(e.target.value)}
                    placeholder="email@example.com"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddSyncEmail();
                      }
                    }}
                    style={{ flex: 1 }}
                  />
                  <Button
                    type="button"
                    size="2"
                    onClick={handleAddSyncEmail}
                    disabled={!newSyncEmail || !newSyncEmail.includes('@')}
                  >
                    <PlusIcon />
                    Add
                  </Button>
                </Flex>
                <Flex direction="column" gap="2">
                  {syncEmails.length === 0 ? (
                    <Text size="2" color="gray">No email addresses added for sync yet</Text>
                  ) : (
                    syncEmails.map((email) => (
                      <Flex key={email} align="center" gap="2">
                        <Badge size="2" variant="soft">{email}</Badge>
                        <IconButton
                          type="button"
                          size="1"
                          variant="ghost"
                          color="red"
                          onClick={() => handleRemoveSyncEmail(email)}
                        >
                          <Cross2Icon />
                        </IconButton>
                      </Flex>
                    ))
                  )}
                </Flex>
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Industry
                </Text>
                <TextField.Root
                  name="industry"
                  value={formData.industry}
                  onChange={handleChange}
                  placeholder="Technology, Healthcare, etc."
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" mb="1">
                  Project Value
                </Text>
                <TextField.Root
                  name="project_value"
                  type="number"
                  value={formData.project_value}
                  onChange={handleChange}
                  placeholder="50000"
                />
              </Box>
            </Flex>

            <Flex gap="3" mt="4" justify="between">
              <Button
                type="button"
                variant="soft"
                color="red"
                onClick={() => setShowDeleteConfirm(true)}
              >
                <TrashIcon />
                Delete Client
              </Button>
              <Flex gap="3">
                <Dialog.Close>
                  <Button variant="soft" color="gray">
                    Cancel
                  </Button>
                </Dialog.Close>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Save Changes'}
                </Button>
              </Flex>
            </Flex>
          </form>

          <Dialog.Close>
            <IconButton
              size="1"
              variant="ghost"
              color="gray"
              style={{
                position: 'absolute',
                top: '12px',
                right: '12px',
                cursor: 'pointer'
              }}
            >
              <Cross2Icon />
            </IconButton>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Root>

      <AlertDialog.Root open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialog.Content style={{ maxWidth: 450 }}>
          <AlertDialog.Title>Delete Client</AlertDialog.Title>
          <AlertDialog.Description size="2">
            Are you sure you want to delete <strong>{client?.name}</strong>? 
            This action cannot be undone. The client card will be permanently removed.
            <br /><br />
            <Text size="2" color="orange">
              Note: Google Drive folders will NOT be deleted and must be removed manually if needed.
            </Text>
          </AlertDialog.Description>

          <Flex gap="3" mt="4" justify="end">
            <AlertDialog.Cancel>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button variant="solid" color="red" onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? 'Deleting...' : 'Delete Client'}
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>
    </>
  );
};

export default EditClientDialog; 