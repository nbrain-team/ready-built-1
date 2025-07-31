import { Box, Flex, Heading, Text, Card, TextField, Button, Callout, Table, Checkbox, Badge, IconButton, Dialog, AlertDialog } from '@radix-ui/themes';
import { InfoCircledIcon, PersonIcon, ExitIcon, MagnifyingGlassIcon, GearIcon, TrashIcon, EnvelopeClosedIcon, CalendarIcon, FileTextIcon, ReloadIcon, LinkBreak1Icon } from '@radix-ui/react-icons';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';

interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  website_url?: string;
  role: string;
  permissions: Record<string, boolean>;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

const AVAILABLE_MODULES = [
  { key: 'chat', label: 'AI Chat' },
  { key: 'history', label: 'Chat History' },
  { key: 'email-personalizer', label: 'Email Personalizer' },
  { key: 'agent-ideas', label: 'Agent Ideas' },
  { key: 'knowledge', label: 'Knowledge Base' },
  { key: 'crm', label: 'CRM' },
  { key: 'clients', label: 'Client Portal' },
  { key: 'oracle', label: 'The Oracle' },
];

export const ProfilePage = () => {
  const { userProfile, refreshProfile, isAdmin, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [isSyncing, setIsSyncing] = useState<string | null>(null);
  
  const [profileForm, setProfileForm] = useState({
    first_name: '',
    last_name: '',
    company: '',
    website_url: ''
  });

  useEffect(() => {
    if (userProfile) {
      setProfileForm({
        first_name: userProfile.first_name || '',
        last_name: userProfile.last_name || '',
        company: userProfile.company || '',
        website_url: userProfile.website_url || ''
      });
    }
  }, [userProfile]);

  useEffect(() => {
    if (isAdmin()) {
      fetchUsers();
    }
    // Fetch data sources for Google integrations
    fetchDataSources();
  }, [isAdmin]);

  const fetchDataSources = async () => {
    try {
      const response = await api.get('/oracle/sources');
      console.log('Data sources response:', response.data);
      setDataSources(response.data);
    } catch (error) {
      console.error('Failed to fetch data sources:', error);
      // Set some default sources if the API fails
      setDataSources([
        { id: 'email-default', name: 'Gmail', type: 'email', status: 'disconnected' },
        { id: 'calendar-default', name: 'Google Calendar', type: 'calendar', status: 'disconnected' },
        { id: 'drive-default', name: 'Google Drive', type: 'drive', status: 'disconnected' }
      ]);
    }
  };

  const connectDataSource = async (sourceType: string) => {
    try {
      const response = await api.post(`/oracle/connect/${sourceType}`);
      if (response.data.authUrl) {
        window.open(response.data.authUrl, '_blank');
      }
    } catch (error) {
      console.error('Connection error:', error);
    }
  };

  const syncDataSource = async (sourceType: string) => {
    setIsSyncing(sourceType);
    try {
      await api.post(`/oracle/sync/${sourceType}`);
      // Refresh data sources after sync
      await fetchDataSources();
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setIsSyncing(null);
    }
  };

  const disconnectDataSource = async (sourceType: string) => {
    try {
      await api.delete(`/oracle/disconnect/${sourceType}`);
      await fetchDataSources();
    } catch (error) {
      console.error('Disconnect error:', error);
    }
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'email': return <EnvelopeClosedIcon />;
      case 'calendar': return <CalendarIcon />;
      case 'drive': return <FileTextIcon />;
      default: return <FileTextIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'green';
      case 'disconnected': return 'gray';
      case 'syncing': return 'blue';
      default: return 'gray';
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/user/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const handleProfileUpdate = async () => {
    setIsSaving(true);
    try {
      await api.put('/user/profile', profileForm);
      await refreshProfile();
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
    setIsSaving(false);
  };

  const handlePermissionChange = async (userId: string, module: string, value: boolean) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;

    const updatedPermissions = { ...user.permissions, [module]: value };
    
    try {
      await api.put(`/user/users/${userId}/permissions`, {
        permissions: updatedPermissions
      });
      await fetchUsers();
    } catch (error) {
      console.error('Failed to update permissions:', error);
    }
  };

  const handleRoleChange = async (userId: string, role: string) => {
    try {
      await api.put(`/user/users/${userId}/permissions`, {
        role: role,
        permissions: users.find(u => u.id === userId)?.permissions || {}
      });
      await fetchUsers();
    } catch (error) {
      console.error('Failed to update role:', error);
    }
  };

  const handleToggleActive = async (userId: string) => {
    try {
      await api.put(`/user/users/${userId}/toggle-active`);
      await fetchUsers();
    } catch (error) {
      console.error('Failed to toggle user status:', error);
    }
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    
    try {
      await api.delete(`/user/users/${userToDelete.id}`);
      await fetchUsers();
      setDeleteDialogOpen(false);
      setUserToDelete(null);
    } catch (error) {
      console.error('Failed to delete user:', error);
    }
  };

  const filteredUsers = users.filter(user => 
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.company?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!userProfile) {
    return <Text>Loading...</Text>;
  }

  return (
    <Box className="page-container">
      <Box className="page-header">
        <Flex justify="between" align="center">
          <Heading size="6">My Profile</Heading>
          <Button color="red" variant="soft" onClick={logout}>
            <ExitIcon /> Logout
          </Button>
        </Flex>
      </Box>

      <Box className="page-content">
        <Flex direction="column" gap="4" style={{ maxWidth: '1200px', margin: '0 auto' }}>
          {/* User Profile Section */}
          <Card>
            <Flex direction="column" gap="3">
              <Flex justify="between" align="center">
                <Flex align="center" gap="3">
                  <PersonIcon width="24" height="24" />
                  <Heading size="4">Profile Information</Heading>
                </Flex>
                {!isEditing && (
                  <Button variant="soft" onClick={() => setIsEditing(true)}>
                    Edit Profile
                  </Button>
                )}
              </Flex>

              {isEditing ? (
                <Flex direction="column" gap="3">
                  <Flex gap="3">
                    <Box style={{ flex: 1 }}>
                      <Text size="2" weight="bold">First Name</Text>
                      <TextField.Root
                        value={profileForm.first_name}
                        onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                        placeholder="Enter first name"
                      />
                    </Box>
                    <Box style={{ flex: 1 }}>
                      <Text size="2" weight="bold">Last Name</Text>
                      <TextField.Root
                        value={profileForm.last_name}
                        onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                        placeholder="Enter last name"
                      />
                    </Box>
                  </Flex>

                  <Box>
                    <Text size="2" weight="bold">Company</Text>
                    <TextField.Root
                      value={profileForm.company}
                      onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
                      placeholder="Enter company name"
                    />
                  </Box>

                  <Box>
                    <Text size="2" weight="bold">Website</Text>
                    <TextField.Root
                      value={profileForm.website_url}
                      onChange={(e) => setProfileForm({ ...profileForm, website_url: e.target.value })}
                      placeholder="https://example.com"
                    />
                  </Box>

                  <Flex gap="2">
                    <Button onClick={handleProfileUpdate} disabled={isSaving}>
                      {isSaving ? 'Saving...' : 'Save Changes'}
                    </Button>
                    <Button variant="soft" onClick={() => setIsEditing(false)}>
                      Cancel
                    </Button>
                  </Flex>
                </Flex>
              ) : (
                <Flex direction="column" gap="3">
                  <Flex direction="column" gap="2">
                    <Flex align="center" gap="2">
                      <Text size="3" color="gray">Email:</Text>
                      <Text size="3" weight="medium">{userProfile.email}</Text>
                    </Flex>
                    
                    <Flex align="center" gap="2">
                      <Text size="3" color="gray">Role:</Text>
                      <Badge color={userProfile.role === 'admin' ? 'red' : 'blue'} size="2">
                        {userProfile.role}
                      </Badge>
                    </Flex>

                    <Flex align="center" gap="2">
                      <Text size="3" color="gray">Name:</Text>
                      <Text size="3" weight="medium">
                        {userProfile.first_name || userProfile.last_name 
                          ? `${userProfile.first_name || ''} ${userProfile.last_name || ''}`.trim()
                          : 'Not set'}
                      </Text>
                    </Flex>

                    <Flex align="center" gap="2">
                      <Text size="3" color="gray">Company:</Text>
                      <Text size="3" weight="medium">{userProfile.company || 'Not set'}</Text>
                    </Flex>

                    {userProfile.website_url && (
                      <Flex align="center" gap="2">
                        <Text size="3" color="gray">Website:</Text>
                        <Text size="3" weight="medium">
                          <a href={userProfile.website_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-9)' }}>
                            {userProfile.website_url}
                          </a>
                        </Text>
                      </Flex>
                    )}

                    <Flex align="center" gap="2">
                      <Text size="3" color="gray">Member Since:</Text>
                      <Text size="3" weight="medium">
                        {new Date(userProfile.created_at).toLocaleDateString()}
                      </Text>
                    </Flex>

                    {userProfile.last_login && (
                      <Flex align="center" gap="2">
                        <Text size="3" color="gray">Last Login:</Text>
                        <Text size="3" weight="medium">
                          {new Date(userProfile.last_login).toLocaleString()}
                        </Text>
                      </Flex>
                    )}
                  </Flex>
                </Flex>
              )}
            </Flex>
          </Card>

          {/* Google Integrations Section */}
          <Card>
            <Flex direction="column" gap="3">
              <Flex align="center" gap="3">
                <LinkBreak1Icon width="24" height="24" />
                <Heading size="4">Google Integrations</Heading>
              </Flex>

              <Text size="2" color="gray">
                Connect your Google accounts to enable email sync, calendar integration, and document access across the platform.
              </Text>

              <Flex direction="column" gap="3">
                {dataSources.map((source) => (
                  <Card key={source.id} variant="surface">
                    <Flex justify="between" align="center">
                      <Flex align="center" gap="3">
                        {getSourceIcon(source.type)}
                        <Box>
                          <Text weight="bold">{source.name}</Text>
                          <Flex align="center" gap="2">
                            <Badge color={getStatusColor(source.status)} size="1">
                              {source.status}
                            </Badge>
                            {source.lastSync && (
                              <Text size="1" color="gray">
                                Last synced: {new Date(source.lastSync).toLocaleString()}
                              </Text>
                            )}
                            {source.count !== null && source.count !== undefined && (
                              <Text size="1" color="gray">
                                {source.count} items
                              </Text>
                            )}
                            {source.errorMessage && (
                              <Text size="1" color="red">
                                {source.errorMessage}
                              </Text>
                            )}
                          </Flex>
                        </Box>
                      </Flex>
                      
                      <Flex gap="2">
                        {source.status === 'disconnected' ? (
                          <Button
                            size="2"
                            variant="soft"
                            onClick={() => connectDataSource(source.type)}
                          >
                            Connect
                          </Button>
                        ) : (
                          <>
                            <Button
                              size="2"
                              variant="soft"
                              onClick={() => syncDataSource(source.type)}
                              disabled={isSyncing === source.type}
                            >
                              <ReloadIcon className={isSyncing === source.type ? "animate-spin" : ""} />
                              Sync
                            </Button>
                            <Button
                              size="2"
                              variant="soft"
                              color="red"
                              onClick={() => disconnectDataSource(source.type)}
                            >
                              Disconnect
                            </Button>
                          </>
                        )}
                      </Flex>
                    </Flex>
                  </Card>
                ))}
              </Flex>

              <Callout.Root color="blue">
                <Callout.Icon>
                  <InfoCircledIcon />
                </Callout.Icon>
                <Callout.Text>
                  Connected accounts will be used for email sync in the Oracle, calendar events in Client Portal, and document access.
                </Callout.Text>
              </Callout.Root>
            </Flex>
          </Card>

          {/* Admin Dashboard */}
          {isAdmin() && (
            <>
              <Card>
                <Flex direction="column" gap="3">
                  <Flex align="center" gap="3">
                    <GearIcon width="24" height="24" />
                    <Heading size="4">Admin Dashboard</Heading>
                  </Flex>

                  <Callout.Root color="blue">
                    <Callout.Icon>
                      <InfoCircledIcon />
                    </Callout.Icon>
                    <Callout.Text>
                      As an administrator, you can manage user accounts, permissions, and access levels.
                    </Callout.Text>
                  </Callout.Root>
                </Flex>
              </Card>

              <Card>
                <Flex direction="column" gap="3">
                  <Flex justify="between" align="center">
                    <Heading size="4">User Management</Heading>
                    <TextField.Root 
                      placeholder="Search users..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    >
                      <TextField.Slot>
                        <MagnifyingGlassIcon />
                      </TextField.Slot>
                    </TextField.Root>
                  </Flex>

                  <Box style={{ overflowX: 'auto' }}>
                    <Table.Root>
                      <Table.Header>
                        <Table.Row>
                          <Table.ColumnHeaderCell>User</Table.ColumnHeaderCell>
                          <Table.ColumnHeaderCell>Role</Table.ColumnHeaderCell>
                          <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
                          <Table.ColumnHeaderCell>Permissions</Table.ColumnHeaderCell>
                          <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
                        </Table.Row>
                      </Table.Header>

                      <Table.Body>
                        {filteredUsers.map((user) => (
                          <Table.Row key={user.id}>
                            <Table.Cell>
                              <Flex direction="column">
                                <Text weight="bold">{user.email}</Text>
                                {(user.first_name || user.last_name) && (
                                  <Text size="1" color="gray">
                                    {`${user.first_name || ''} ${user.last_name || ''}`.trim()}
                                  </Text>
                                )}
                                {user.company && (
                                  <Text size="1" color="gray">{user.company}</Text>
                                )}
                              </Flex>
                            </Table.Cell>

                            <Table.Cell>
                              <select
                                value={user.role}
                                onChange={(e) => handleRoleChange(user.id, e.target.value)}
                                disabled={user.id === userProfile.id}
                                style={{
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  border: '1px solid var(--gray-6)'
                                }}
                              >
                                <option value="user">User</option>
                                <option value="admin">Admin</option>
                              </select>
                            </Table.Cell>

                            <Table.Cell>
                              <Badge color={user.is_active ? 'green' : 'red'}>
                                {user.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </Table.Cell>

                            <Table.Cell>
                              <Dialog.Root>
                                <Dialog.Trigger>
                                  <Button variant="soft" size="1">
                                    Manage Permissions
                                  </Button>
                                </Dialog.Trigger>

                                <Dialog.Content style={{ maxWidth: 500 }}>
                                  <Dialog.Title>
                                    Permissions for {user.email}
                                  </Dialog.Title>

                                  <Flex direction="column" gap="3" style={{ marginTop: '1rem' }}>
                                    {AVAILABLE_MODULES.map((module) => (
                                      <Flex key={module.key} justify="between" align="center">
                                        <Text>{module.label}</Text>
                                        <Checkbox
                                          checked={user.permissions[module.key] || false}
                                          onCheckedChange={(checked) => 
                                            handlePermissionChange(user.id, module.key, checked as boolean)
                                          }
                                          disabled={user.role === 'admin'}
                                        />
                                      </Flex>
                                    ))}
                                  </Flex>

                                  {user.role === 'admin' && (
                                    <Callout.Root color="blue" style={{ marginTop: '1rem' }}>
                                      <Callout.Icon>
                                        <InfoCircledIcon />
                                      </Callout.Icon>
                                      <Callout.Text>
                                        Admin users have access to all modules by default.
                                      </Callout.Text>
                                    </Callout.Root>
                                  )}

                                  <Flex gap="3" justify="end" style={{ marginTop: '1.5rem' }}>
                                    <Dialog.Close>
                                      <Button variant="soft">Close</Button>
                                    </Dialog.Close>
                                  </Flex>
                                </Dialog.Content>
                              </Dialog.Root>
                            </Table.Cell>

                            <Table.Cell>
                              <Flex gap="2">
                                <Button
                                  variant="soft"
                                  size="1"
                                  color={user.is_active ? 'orange' : 'green'}
                                  onClick={() => handleToggleActive(user.id)}
                                  disabled={user.id === userProfile.id}
                                >
                                  {user.is_active ? 'Deactivate' : 'Activate'}
                                </Button>
                                <IconButton
                                  variant="soft"
                                  color="red"
                                  size="1"
                                  onClick={() => {
                                    setUserToDelete(user);
                                    setDeleteDialogOpen(true);
                                  }}
                                  disabled={user.id === userProfile.id}
                                >
                                  <TrashIcon />
                                </IconButton>
                              </Flex>
                            </Table.Cell>
                          </Table.Row>
                        ))}
                      </Table.Body>
                    </Table.Root>
                  </Box>
                </Flex>
              </Card>
            </>
          )}
        </Flex>
      </Box>

      {/* Delete Confirmation Dialog */}
      <AlertDialog.Root open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialog.Content style={{ maxWidth: 450 }}>
          <AlertDialog.Title>Delete User</AlertDialog.Title>
          <AlertDialog.Description>
            Are you sure you want to delete {userToDelete?.email}? This action cannot be undone.
          </AlertDialog.Description>
          <Flex gap="3" justify="end" style={{ marginTop: '1.5rem' }}>
            <AlertDialog.Cancel>
              <Button variant="soft">Cancel</Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button color="red" onClick={handleDeleteUser}>
                Delete User
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>
    </Box>
  );
}; 