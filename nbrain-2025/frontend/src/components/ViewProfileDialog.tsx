import React, { useState } from 'react';
import { Dialog, Flex, Text, Button, TextField, Heading, Box, Badge, AlertDialog } from '@radix-ui/themes';
import { Cross2Icon, Pencil1Icon, CheckIcon, TrashIcon } from '@radix-ui/react-icons';
import api from '../api';
import { useNavigate } from 'react-router-dom';

interface ViewProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  client: any;
  onUpdate: () => void;
}

const ViewProfileDialog: React.FC<ViewProfileDialogProps> = ({
  open,
  onOpenChange,
  client,
  onUpdate
}) => {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [editedClient, setEditedClient] = useState(client);
  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Update editedClient when client prop changes
  React.useEffect(() => {
    setEditedClient(client);
  }, [client]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Convert camelCase to snake_case for API
      const payload = {
        name: editedClient.name,
        primary_contact_name: editedClient.primaryContactName || null,
        primary_contact_email: editedClient.primaryContactEmail || null,
        primary_contact_phone: editedClient.primaryContactPhone || null,
        company_website: editedClient.companyWebsite || null,
        domain: editedClient.domain || null,
        industry: editedClient.industry || null,
        project_value: editedClient.projectValue || null,
        sync_email_addresses: editedClient.syncEmailAddresses || []
      };
      
      await api.put(`/clients/${client.id}`, payload);
      await onUpdate();
      setIsEditing(false);
      onOpenChange(false);
    } catch (error) {
      console.error('Error updating client:', error);
      alert('Failed to update client. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedClient(client);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await api.delete(`/clients/${client.id}`);
      setShowDeleteDialog(false);
      onOpenChange(false);
      // Navigate back to clients page
      navigate('/clients');
    } catch (error) {
      console.error('Error deleting client:', error);
      alert('Failed to delete client. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Dialog.Root open={open} onOpenChange={onOpenChange}>
        <Dialog.Content style={{ maxWidth: 600 }}>
          <Dialog.Title>
            <Flex justify="between" align="center">
              <Heading size="5">Client Profile</Heading>
              <Dialog.Close>
                <Button variant="ghost" size="2">
                  <Cross2Icon />
                </Button>
              </Dialog.Close>
            </Flex>
          </Dialog.Title>

          <Box mt="4">
            <Flex direction="column" gap="3">
              {/* Status Badge */}
              <Flex justify="between" align="center">
                <Text size="3">Status:</Text>
                <Badge color="green" size="2">{client.status}</Badge>
              </Flex>

              {/* Company Name */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Company:</Text>
                  {isEditing ? (
                    <TextField.Root
                      value={editedClient.name}
                      onChange={(e) => setEditedClient({ ...editedClient, name: e.target.value })}
                    />
                  ) : (
                    <Text size="3">{client.name}</Text>
                  )}
                </Flex>
              </Box>

              {/* Contact Name */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Contact Name:</Text>
                  {isEditing ? (
                    <TextField.Root
                      value={editedClient.primaryContactName || ''}
                      onChange={(e) => setEditedClient({ ...editedClient, primaryContactName: e.target.value })}
                      placeholder="Not set"
                    />
                  ) : (
                    <Text size="3">{client.primaryContactName || 'Not set'}</Text>
                  )}
                </Flex>
              </Box>

              {/* Email */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Email:</Text>
                  {isEditing ? (
                    <TextField.Root
                      value={editedClient.primaryContactEmail || ''}
                      onChange={(e) => setEditedClient({ ...editedClient, primaryContactEmail: e.target.value })}
                      placeholder="Not set"
                    />
                  ) : (
                    <Text size="3">{client.primaryContactEmail || 'Not set'}</Text>
                  )}
                </Flex>
              </Box>

              {/* Phone */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Phone:</Text>
                  {isEditing ? (
                    <TextField.Root
                      value={editedClient.primaryContactPhone || ''}
                      onChange={(e) => setEditedClient({ ...editedClient, primaryContactPhone: e.target.value })}
                      placeholder="Not set"
                    />
                  ) : (
                    <Text size="3">{client.primaryContactPhone || 'Not set'}</Text>
                  )}
                </Flex>
              </Box>

              {/* Website */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Website:</Text>
                  {isEditing ? (
                    <TextField.Root
                      value={editedClient.companyWebsite || ''}
                      onChange={(e) => setEditedClient({ ...editedClient, companyWebsite: e.target.value })}
                      placeholder="Not set"
                    />
                  ) : (
                    <Text size="3">
                      {client.companyWebsite ? (
                        <a href={client.companyWebsite} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-9)' }}>
                          {client.companyWebsite}
                        </a>
                      ) : 'Not set'}
                    </Text>
                  )}
                </Flex>
              </Box>

              {/* Domain */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Domain:</Text>
                  {isEditing ? (
                    <TextField.Root
                      value={editedClient.domain || ''}
                      onChange={(e) => setEditedClient({ ...editedClient, domain: e.target.value })}
                      placeholder="Not set"
                    />
                  ) : (
                    <Text size="3">{client.domain || 'Not set'}</Text>
                  )}
                </Flex>
              </Box>

              {/* Sync Email Addresses */}
              <Box>
                <Text size="3" color="gray">Sync Email Addresses:</Text>
                <Text size="1" color="gray" style={{ marginBottom: '0.5rem' }}>
                  Calendar events and emails will be synced for these addresses
                </Text>
                {isEditing ? (
                  <Flex direction="column" gap="2">
                    <TextField.Root
                      value={(editedClient.syncEmailAddresses || []).join(', ')}
                      onChange={(e) => {
                        const emails = e.target.value
                          .split(',')
                          .map(email => email.trim())
                          .filter(email => email);
                        setEditedClient({ ...editedClient, syncEmailAddresses: emails });
                      }}
                      placeholder="email1@domain.com, email2@domain.com"
                    />
                    <Text size="1" color="gray">
                      Separate multiple emails with commas
                    </Text>
                  </Flex>
                ) : (
                  <Box>
                    {client.syncEmailAddresses && client.syncEmailAddresses.length > 0 ? (
                      <Flex direction="column" gap="1">
                        {client.syncEmailAddresses.map((email: string, index: number) => (
                          <Badge key={index} variant="soft" size="2">
                            {email}
                          </Badge>
                        ))}
                      </Flex>
                    ) : (
                      <Text size="3" color="gray">No sync emails configured</Text>
                    )}
                  </Box>
                )}
              </Box>

              {/* Industry */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Industry:</Text>
                  {isEditing ? (
                    <TextField.Root
                      value={editedClient.industry || ''}
                      onChange={(e) => setEditedClient({ ...editedClient, industry: e.target.value })}
                      placeholder="Not set"
                    />
                  ) : (
                    <Text size="3">{client.industry || 'Not set'}</Text>
                  )}
                </Flex>
              </Box>

              {/* Project Value */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Project Value:</Text>
                  {isEditing ? (
                    <TextField.Root
                      type="number"
                      value={editedClient.projectValue || ''}
                      onChange={(e) => setEditedClient({ ...editedClient, projectValue: parseFloat(e.target.value) || 0 })}
                      placeholder="0"
                    />
                  ) : (
                    <Text size="3" color="green" weight="medium">
                      ${client.projectValue?.toLocaleString() || '0'}
                    </Text>
                  )}
                </Flex>
              </Box>

              {/* Health Score */}
              <Box>
                <Flex align="baseline" gap="2">
                  <Text size="3" color="gray">Health Score:</Text>
                  <Badge color={client.healthScore >= 80 ? 'green' : client.healthScore >= 60 ? 'orange' : 'red'}>
                    {client.healthScore}%
                  </Badge>
                </Flex>
              </Box>
            </Flex>
          </Box>

          <Flex gap="3" mt="4" justify="between">
            <Button 
              variant="soft" 
              color="red" 
              onClick={() => setShowDeleteDialog(true)}
              disabled={isEditing}
            >
              <TrashIcon />
              Delete Client
            </Button>
            
            <Flex gap="3">
              {isEditing ? (
                <>
                  <Button variant="soft" onClick={handleCancel}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave} disabled={isSaving}>
                    <CheckIcon />
                    Save Changes
                  </Button>
                </>
              ) : (
                <Button onClick={() => setIsEditing(true)}>
                  <Pencil1Icon />
                  Edit Profile
                </Button>
              )}
            </Flex>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>

      {/* Delete Confirmation Dialog */}
      <AlertDialog.Root open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialog.Content style={{ maxWidth: 450 }}>
          <AlertDialog.Title>Delete Client</AlertDialog.Title>
          <AlertDialog.Description size="2">
            Are you sure you want to delete <strong>{client.name}</strong>? 
            This action cannot be undone and will remove all associated data including:
            <ul style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>
              <li>Communications and chat history</li>
              <li>Tasks and activities</li>
              <li>Documents and team members</li>
            </ul>
            Note: Google Drive folders will be preserved.
          </AlertDialog.Description>

          <Flex gap="3" mt="4" justify="end">
            <AlertDialog.Cancel>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button 
                variant="solid" 
                color="red" 
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete Client'}
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>
    </>
  );
};

export default ViewProfileDialog; 