import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Heading, 
  Text, 
  Card, 
  Flex, 
  Button, 
  Select,
  Badge,
  IconButton,
  Dialog,
  TextField,
  TextArea,
  Tabs,
  ScrollArea,
  Separator,
  Checkbox
} from '@radix-ui/themes';
import { 
  CalendarIcon, 
  PlusIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  TwitterLogoIcon,
  InstagramLogoIcon,
  LinkedInLogoIcon,
  DotsHorizontalIcon,
  Cross2Icon,
  EnvelopeClosedIcon,
  DragHandleDots2Icon,
  PersonIcon
} from '@radix-ui/react-icons';
import api from '../api';

interface Client {
  id: string;
  name: string;
  email?: string;
  company?: string;
}

interface SocialPost {
  id: string;
  platform: 'twitter' | 'instagram' | 'facebook' | 'linkedin' | 'email';
  content: string;
  scheduledDate: string;
  publishedDate?: string;
  status: 'draft' | 'scheduled' | 'published' | 'failed';
  clientId?: string;
  clientName?: string;
  mediaUrls?: string[];
  campaignName?: string;
  createdAt: string;
  updatedAt: string;
}

interface CalendarDay {
  date: Date;
  posts: SocialPost[];
  isCurrentMonth: boolean;
}

const SocialMediaCalendar: React.FC = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<'month' | 'week' | 'day' | 'list'>('month');
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['all']);
  const [isAddPostOpen, setIsAddPostOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [editingPost, setEditingPost] = useState<SocialPost | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isBulkTemplateOpen, setIsBulkTemplateOpen] = useState(false);
  
  // Client selection state
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string>('nbrain');
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  
  // Drag and drop state
  const [draggedPost, setDraggedPost] = useState<SocialPost | null>(null);
  const [dragOverDate, setDragOverDate] = useState<Date | null>(null);

  // Calendar state
  const [calendarDays, setCalendarDays] = useState<CalendarDay[]>([]);
  
  // Bulk selection state
  const [selectedPostIds, setSelectedPostIds] = useState<Set<string>>(new Set());
  const [isBulkMode, setIsBulkMode] = useState(false);

  // Fetch clients on mount
  useEffect(() => {
    fetchClients();
  }, []);

  // Update selected client when ID changes
  useEffect(() => {
    if (selectedClientId === 'nbrain') {
      setSelectedClient(null);
    } else {
      const client = clients.find(c => c.id === selectedClientId);
      setSelectedClient(client || null);
    }
  }, [selectedClientId, clients]);

  useEffect(() => {
    fetchPosts();
  }, [currentDate, selectedClientId]);

  useEffect(() => {
    generateCalendarDays();
  }, [posts, currentDate, view]);

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  const fetchPosts = async () => {
    setIsLoading(true);
    try {
      const params: any = {
        month: currentDate.getMonth() + 1,
        year: currentDate.getFullYear()
      };
      
      // Add client filter if not nBrain
      if (selectedClientId !== 'nbrain') {
        params.client_id = selectedClientId;
      }
      
      const response = await api.get('/social-media/posts', { params });
      console.log('Fetched posts:', response.data);
      console.log('Current month/year:', currentDate.getMonth() + 1, currentDate.getFullYear());
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setPosts([]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateCalendarDays = () => {
    if (view === 'month') {
      generateMonthView();
    } else if (view === 'week') {
      generateWeekView();
    } else {
      generateDayView();
    }
  };

  const generateMonthView = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    const days: CalendarDay[] = [];
    const endDate = new Date(lastDay);
    endDate.setDate(endDate.getDate() + (6 - lastDay.getDay()));

    console.log('Generating month view for:', month + 1, year);
    console.log('Posts available:', posts.length);

    for (let date = new Date(startDate); date <= endDate; date.setDate(date.getDate() + 1)) {
      const dayPosts = posts.filter(post => {
        const postDate = new Date(post.scheduledDate);
        const matches = postDate.toDateString() === date.toDateString();
        if (matches) {
          console.log('Found post for date:', date.toDateString(), post);
        }
        return matches;
      });

      days.push({
        date: new Date(date),
        posts: dayPosts,
        isCurrentMonth: date.getMonth() === month
      });
    }

    setCalendarDays(days);
  };

  const generateWeekView = () => {
    const startOfWeek = new Date(currentDate);
    const day = startOfWeek.getDay();
    startOfWeek.setDate(startOfWeek.getDate() - day);

    const days: CalendarDay[] = [];
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      
      const dayPosts = posts.filter(post => {
        const postDate = new Date(post.scheduledDate);
        return postDate.toDateString() === date.toDateString();
      });

      days.push({
        date: new Date(date),
        posts: dayPosts,
        isCurrentMonth: true
      });
    }

    setCalendarDays(days);
  };

  const generateDayView = () => {
    const dayPosts = posts.filter(post => {
      const postDate = new Date(post.scheduledDate);
      return postDate.toDateString() === currentDate.toDateString();
    });

    setCalendarDays([{
      date: new Date(currentDate),
      posts: dayPosts,
      isCurrentMonth: true
    }]);
  };

  const navigate = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    
    if (view === 'month') {
      if (direction === 'prev') {
        newDate.setMonth(newDate.getMonth() - 1);
      } else {
        newDate.setMonth(newDate.getMonth() + 1);
      }
    } else if (view === 'week') {
      if (direction === 'prev') {
        newDate.setDate(newDate.getDate() - 7);
      } else {
        newDate.setDate(newDate.getDate() + 7);
      }
    } else {
      if (direction === 'prev') {
        newDate.setDate(newDate.getDate() - 1);
      } else {
        newDate.setDate(newDate.getDate() + 1);
      }
    }
    
    setCurrentDate(newDate);
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'twitter':
        return <TwitterLogoIcon />;
      case 'instagram':
        return <InstagramLogoIcon />;
      case 'linkedin':
        return <LinkedInLogoIcon />;
      case 'email':
        return <EnvelopeClosedIcon />;
      default:
        return <CalendarIcon />;
    }
  };

  const getPlatformColor = (platform: string, status?: string) => {
    const baseColor = (() => {
      switch (platform) {
        case 'twitter':
          return 'blue';
        case 'instagram':
          return 'pink';
        case 'linkedin':
          return 'blue';
        case 'facebook':
          return 'indigo';
        case 'email':
          return 'green';
        default:
          return 'gray';
      }
    })();
    
    // Return muted color for published posts
    if (status === 'published') {
      return 'gray';
    }
    
    return baseColor;
  };

  const handleDayClick = (date: Date) => {
    setSelectedDate(date);
    setIsAddPostOpen(true);
  };

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, post: SocialPost) => {
    setDraggedPost(post);
    e.dataTransfer.effectAllowed = 'move';
    // Add a visual effect
    if (e.target instanceof HTMLElement) {
      e.target.style.opacity = '0.5';
    }
  };

  const handleDragEnd = (e: React.DragEvent) => {
    // Reset opacity
    if (e.target instanceof HTMLElement) {
      e.target.style.opacity = '1';
    }
    setDraggedPost(null);
    setDragOverDate(null);
  };

  const handleDragOver = (e: React.DragEvent, date: Date) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverDate(date);
  };

  const handleDragLeave = () => {
    setDragOverDate(null);
  };

  const handleDrop = async (e: React.DragEvent, targetDate: Date) => {
    e.preventDefault();
    setDragOverDate(null);

    if (!draggedPost) return;

    // Calculate the new scheduled date maintaining the original time
    const originalDate = new Date(draggedPost.scheduledDate);
    const newScheduledDate = new Date(
      targetDate.getFullYear(),
      targetDate.getMonth(),
      targetDate.getDate(),
      originalDate.getHours(),
      originalDate.getMinutes()
    );

    try {
      // Update the post with the new date
      await api.put(`/social-media/posts/${draggedPost.id}`, {
        ...draggedPost,
        scheduledDate: newScheduledDate.toISOString()
      });

      // Refresh posts
      fetchPosts();
      
      // Show success feedback (you could add a toast here)
      console.log(`Moved post to ${newScheduledDate.toLocaleDateString()}`);
    } catch (error) {
      console.error('Error moving post:', error);
      // You could show an error toast here
    }
  };

  // Delete handlers
  const handleDeletePost = async (postId: string) => {
    if (!confirm('Are you sure you want to delete this post?')) return;
    
    try {
      await api.delete(`/social-media/posts/${postId}`);
      fetchPosts();
    } catch (error) {
      console.error('Error deleting post:', error);
      alert('Failed to delete post');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedPostIds.size === 0) {
      alert('No posts selected');
      return;
    }
    
    if (!confirm(`Are you sure you want to delete ${selectedPostIds.size} posts?`)) return;
    
    try {
      // Delete all selected posts
      await Promise.all(
        Array.from(selectedPostIds).map(id => 
          api.delete(`/social-media/posts/${id}`)
        )
      );
      
      setSelectedPostIds(new Set());
      setIsBulkMode(false);
      fetchPosts();
    } catch (error) {
      console.error('Error deleting posts:', error);
      alert('Failed to delete some posts');
    }
  };

  const togglePostSelection = (postId: string) => {
    const newSelection = new Set(selectedPostIds);
    if (newSelection.has(postId)) {
      newSelection.delete(postId);
    } else {
      newSelection.add(postId);
    }
    setSelectedPostIds(newSelection);
  };

  const selectAllPosts = () => {
    const allPostIds = new Set(posts.map(post => post.id));
    setSelectedPostIds(allPostIds);
  };

  const clearSelection = () => {
    setSelectedPostIds(new Set());
  };

  const getDateRangeText = () => {
    if (view === 'month') {
      return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    } else if (view === 'week') {
      const startOfWeek = new Date(currentDate);
      const day = startOfWeek.getDay();
      startOfWeek.setDate(startOfWeek.getDate() - day);
      
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      
      return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    } else {
      return currentDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    }
  };

  const PostDialog = () => {
    const [platform, setPlatform] = useState<string>(editingPost?.platform || 'twitter');
    const [content, setContent] = useState(editingPost?.content || '');
    const [scheduledTime, setScheduledTime] = useState(() => {
      if (editingPost) {
        const date = new Date(editingPost.scheduledDate);
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
      }
      return '10:00';
    });
    const [clientId, setClientId] = useState(editingPost?.clientId || '');
    const [localDate, setLocalDate] = useState(() => {
      if (editingPost) {
        return new Date(editingPost.scheduledDate);
      }
      return selectedDate || new Date();
    });

    const handleSave = async () => {
      try {
        const postData = {
          platform,
          content,
          scheduledDate: new Date(
            localDate.getFullYear(),
            localDate.getMonth(),
            localDate.getDate(),
            parseInt(scheduledTime.split(':')[0]),
            parseInt(scheduledTime.split(':')[1])
          ).toISOString(),
          status: 'scheduled',
          clientId: selectedClientId !== 'nbrain' ? selectedClientId : null
        };

        if (editingPost) {
          await api.put(`/social-media/posts/${editingPost.id}`, postData);
        } else {
          await api.post('/social-media/posts', postData);
        }

        fetchPosts();
        setIsAddPostOpen(false);
        setEditingPost(null);
      } catch (error) {
        console.error('Error saving post:', error);
      }
    };

    return (
      <Dialog.Root open={isAddPostOpen} onOpenChange={(open) => {
        setIsAddPostOpen(open);
        if (!open) {
          setEditingPost(null);
        }
      }}>
        <Dialog.Content style={{ maxWidth: 500 }}>
          <Dialog.Title>
            {editingPost ? 'Edit Post' : 'Schedule New Post'}
          </Dialog.Title>
          
          <Flex direction="column" gap="4" mt="4">
            <Box>
              <Text size="2" weight="medium" mb="1">Platform</Text>
              <Select.Root value={platform} onValueChange={setPlatform}>
                <Select.Trigger />
                <Select.Content>
                  <Select.Item value="twitter">Twitter</Select.Item>
                  <Select.Item value="instagram">Instagram</Select.Item>
                  <Select.Item value="linkedin">LinkedIn</Select.Item>
                  <Select.Item value="facebook">Facebook</Select.Item>
                  <Select.Item value="email">Email Campaign</Select.Item>
                </Select.Content>
              </Select.Root>
            </Box>

            <Box>
              <Text size="2" weight="medium" mb="1">Content</Text>
              <TextArea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="What's on your mind?"
                rows={4}
              />
            </Box>

            <Flex gap="3">
              <Box style={{ flex: 1 }}>
                <Text size="2" weight="medium" mb="1">Date</Text>
                <TextField.Root
                  type="date"
                  value={localDate.toISOString().split('T')[0] || ''}
                  onChange={(e) => {
                    const newDate = new Date(e.target.value);
                    setLocalDate(newDate);
                  }}
                />
              </Box>
              <Box style={{ flex: 1 }}>
                <Text size="2" weight="medium" mb="1">Time</Text>
                <TextField.Root
                  type="time"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                />
              </Box>
            </Flex>

            <Flex gap="3" justify="end">
              {editingPost && editingPost.status !== 'published' && (
                <Button 
                  variant="soft" 
                  color="red"
                  onClick={() => {
                    handleDeletePost(editingPost.id);
                    setIsAddPostOpen(false);
                  }}
                >
                  Delete
                </Button>
              )}
              <Dialog.Close>
                <Button variant="soft" color="gray">
                  Cancel
                </Button>
              </Dialog.Close>
              <Button onClick={handleSave}>
                {editingPost ? 'Update' : 'Schedule'} Post
              </Button>
            </Flex>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    );
  };

  const BulkTemplateDialog = () => {
    const [selectedBulkPlatforms, setSelectedBulkPlatforms] = useState<string[]>([]);
    const [topics, setTopics] = useState('');
    const [duration, setDuration] = useState('2'); // weeks
    const [emailCount, setEmailCount] = useState('4'); // emails per duration
    const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]); // Default to today
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerate = async () => {
      if (selectedBulkPlatforms.length === 0 || !topics.trim()) {
        alert('Please select at least one platform and provide topics');
        return;
      }

      setIsGenerating(true);

      try {
        // Parse topics (one per line)
        const topicList = topics.split('\n').filter(t => t.trim());
        
        // Generate schedule based on best practices
        const response = await api.post('/social-media/bulk-generate', {
          platforms: selectedBulkPlatforms,
          topics: topicList,
          durationWeeks: parseInt(duration),
          emailCount: selectedBulkPlatforms.includes('email') ? parseInt(emailCount) : 0,
          startDate: new Date(startDate).toISOString(),
          clientId: selectedClientId !== 'nbrain' ? selectedClientId : null,
          clientName: selectedClient?.name || 'nBrain'
        });

        // Refresh the calendar
        fetchPosts();
        setIsBulkTemplateOpen(false);
        
        // Reset form
        setSelectedBulkPlatforms([]);
        setTopics('');
        setDuration('2');
        setEmailCount('4');
        setStartDate(new Date().toISOString().split('T')[0]);
      } catch (error) {
        console.error('Error generating bulk content:', error);
        alert('Failed to generate content. Please try again.');
      } finally {
        setIsGenerating(false);
      }
    };

    const platformOptions = [
      { value: 'linkedin', label: 'LinkedIn', icon: <LinkedInLogoIcon /> },
      { value: 'twitter', label: 'Twitter', icon: <TwitterLogoIcon /> },
      { value: 'facebook', label: 'Facebook', icon: <CalendarIcon /> },
      { value: 'email', label: 'Email Campaign', icon: <EnvelopeClosedIcon /> }
    ];

    return (
      <Dialog.Root open={isBulkTemplateOpen} onOpenChange={setIsBulkTemplateOpen}>
        <Dialog.Content style={{ maxWidth: 600 }}>
          <Dialog.Title>Create Bulk Calendar Template</Dialog.Title>
          <Dialog.Description>
            Generate an entire content calendar based on your topics and preferred schedule.
          </Dialog.Description>
          
          <Flex direction="column" gap="4" mt="4">
            {/* Platform Selection */}
            <Box>
              <Text size="2" weight="medium" mb="2">Select Platforms</Text>
              <Flex gap="2" wrap="wrap">
                {platformOptions.map(platform => (
                  <Button
                    key={platform.value}
                    variant={selectedBulkPlatforms.includes(platform.value) ? 'solid' : 'outline'}
                    size="2"
                    onClick={() => {
                      setSelectedBulkPlatforms(prev =>
                        prev.includes(platform.value)
                          ? prev.filter(p => p !== platform.value)
                          : [...prev, platform.value]
                      );
                    }}
                  >
                    {platform.icon} {platform.label}
                  </Button>
                ))}
              </Flex>
            </Box>

            {/* Topics Input */}
            <Box>
              <Text size="2" weight="medium" mb="1">Topics (one per line)</Text>
              <TextArea
                value={topics}
                onChange={(e) => setTopics(e.target.value)}
                placeholder="AI in Marketing&#10;Customer Success Stories&#10;Industry Trends&#10;Product Updates"
                rows={6}
              />
              <Text size="1" color="gray" mt="1">
                Enter topics or themes for your content. AI will generate engaging posts for each topic.
              </Text>
            </Box>

            {/* Start Date and Duration */}
            <Flex gap="3">
              <Box style={{ flex: 1 }}>
                <Text size="2" weight="medium" mb="1">Start Date</Text>
                <TextField.Root
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                />
              </Box>
              
              <Box style={{ flex: 1 }}>
                <Text size="2" weight="medium" mb="1">Duration</Text>
                <Select.Root value={duration} onValueChange={setDuration}>
                  <Select.Trigger />
                  <Select.Content>
                    <Select.Item value="1">1 Week</Select.Item>
                    <Select.Item value="2">2 Weeks</Select.Item>
                    <Select.Item value="3">3 Weeks</Select.Item>
                    <Select.Item value="4">4 Weeks</Select.Item>
                  </Select.Content>
                </Select.Root>
              </Box>

              {selectedBulkPlatforms.includes('email') && (
                <Box style={{ flex: 1 }}>
                  <Text size="2" weight="medium" mb="1">Email Campaigns</Text>
                  <TextField.Root
                    type="number"
                    value={emailCount}
                    onChange={(e) => setEmailCount(e.target.value)}
                    min="1"
                    max="20"
                  />
                </Box>
              )}
            </Flex>

            {/* Schedule Preview */}
            <Card>
              <Text size="2" weight="medium" mb="2">Scheduling Strategy</Text>
              <Text size="1" color="gray">
                {selectedBulkPlatforms.includes('linkedin') && '• LinkedIn: Tuesdays & Thursdays at 10 AM (peak professional engagement)\n'}
                {selectedBulkPlatforms.includes('twitter') && '• Twitter: Mon/Wed/Fri at varied times (9 AM, 2 PM, 6 PM)\n'}
                {selectedBulkPlatforms.includes('facebook') && '• Facebook: Weekends + Wednesdays at 7 PM (highest engagement)\n'}
                {selectedBulkPlatforms.includes('email') && `• Email: ${emailCount} campaigns spread evenly across ${duration} week(s)`}
              </Text>
            </Card>

            {/* Actions */}
            <Flex gap="3" justify="end">
              <Dialog.Close>
                <Button variant="soft" color="gray" disabled={isGenerating}>
                  Cancel
                </Button>
              </Dialog.Close>
              <Button onClick={handleGenerate} disabled={isGenerating}>
                {isGenerating ? 'Generating...' : 'Generate Calendar'}
              </Button>
            </Flex>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    );
  };

  const renderCalendarContent = () => {
    if (view === 'list') {
      // List view
      const sortedPosts = [...posts].sort((a, b) => 
        new Date(a.scheduledDate).getTime() - new Date(b.scheduledDate).getTime()
      );

      return (
        <ScrollArea style={{ height: '100%' }}>
          <Box style={{ padding: '1rem' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--gray-6)' }}>
                  {isBulkMode && (
                    <th style={{ width: '40px', padding: '0.75rem' }}>
                      <Checkbox 
                        checked={selectedPostIds.size === posts.length && posts.length > 0}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            selectAllPosts();
                          } else {
                            clearSelection();
                          }
                        }}
                      />
                    </th>
                  )}
                  <th style={{ textAlign: 'left', padding: '0.75rem', fontWeight: 'bold' }}>Date & Time</th>
                  <th style={{ textAlign: 'left', padding: '0.75rem', fontWeight: 'bold' }}>Platform</th>
                  <th style={{ textAlign: 'left', padding: '0.75rem', fontWeight: 'bold' }}>Content</th>
                  <th style={{ textAlign: 'left', padding: '0.75rem', fontWeight: 'bold' }}>Status</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem', fontWeight: 'bold' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedPosts.length === 0 ? (
                  <tr>
                    <td colSpan={isBulkMode ? 6 : 5} style={{ textAlign: 'center', padding: '2rem' }}>
                      <Text color="gray">No posts scheduled</Text>
                    </td>
                  </tr>
                ) : (
                  sortedPosts.map((post) => (
                    <tr 
                      key={post.id} 
                      style={{ 
                        borderBottom: '1px solid var(--gray-3)',
                        cursor: 'pointer',
                        transition: 'background-color 0.2s',
                        backgroundColor: selectedPostIds.has(post.id) ? 'var(--blue-2)' : 'transparent'
                      }}
                      onMouseEnter={(e) => {
                        if (!selectedPostIds.has(post.id)) {
                          e.currentTarget.style.backgroundColor = 'var(--gray-2)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!selectedPostIds.has(post.id)) {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }
                      }}
                      onClick={() => {
                        if (isBulkMode) {
                          togglePostSelection(post.id);
                        }
                      }}
                    >
                      {isBulkMode && (
                        <td style={{ padding: '0.75rem' }}>
                          <Checkbox 
                            checked={selectedPostIds.has(post.id)}
                            onCheckedChange={() => togglePostSelection(post.id)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </td>
                      )}
                      <td style={{ padding: '0.75rem' }}>
                        <Text size="2" weight="medium">
                          {new Date(post.scheduledDate).toLocaleDateString()}
                        </Text>
                        <Text size="1" color="gray">
                          {new Date(post.scheduledDate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </Text>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <Flex align="center" gap="2">
                          {getPlatformIcon(post.platform)}
                          <Text size="2" style={{ textTransform: 'capitalize' }}>{post.platform}</Text>
                        </Flex>
                      </td>
                      <td style={{ padding: '0.75rem', maxWidth: '400px' }}>
                        <Text size="2" style={{ 
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          display: 'block'
                        }}>
                          {post.content}
                        </Text>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <Badge color={getPlatformColor(post.platform, post.status)}>
                          {post.status}
                        </Badge>
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                        <Flex gap="2" justify="end">
                          <IconButton
                            size="1"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingPost(post);
                              setIsAddPostOpen(true);
                            }}
                          >
                            <DotsHorizontalIcon />
                          </IconButton>
                          {post.status !== 'published' && (
                            <IconButton
                              size="1"
                              variant="ghost"
                              color="red"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeletePost(post.id);
                              }}
                            >
                              <Cross2Icon />
                            </IconButton>
                          )}
                        </Flex>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </Box>
        </ScrollArea>
      );
    } else if (view === 'day') {
      // Day view
      return (
        <ScrollArea style={{ height: '100%' }}>
          <Box style={{ padding: '1rem' }}>
            {calendarDays[0]?.posts.length === 0 ? (
              <Text color="gray" size="3" style={{ textAlign: 'center', padding: '2rem' }}>
                No posts scheduled for this day
              </Text>
            ) : (
              <Flex direction="column" gap="3">
                {calendarDays[0]?.posts.map((post) => (
                  <Card 
                    key={post.id} 
                    draggable={post.status !== 'published'}
                    onDragStart={(e) => handleDragStart(e, post)}
                    onDragEnd={handleDragEnd}
                    style={{ 
                      cursor: post.status === 'published' ? 'pointer' : 'move',
                      userSelect: 'none'
                    }} 
                    onClick={() => {
                      setEditingPost(post);
                      setIsAddPostOpen(true);
                    }}
                  >
                    <Flex justify="between" align="center">
                      <Flex gap="3" align="center">
                        {post.status !== 'published' && (
                          <DragHandleDots2Icon 
                            style={{ 
                              cursor: 'move', 
                              opacity: 0.5
                            }} 
                          />
                        )}
                        {getPlatformIcon(post.platform)}
                        <Box>
                          <Text weight="medium">{post.content}</Text>
                          <Text size="2" color="gray">
                            {new Date(post.scheduledDate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </Text>
                        </Box>
                      </Flex>
                      <Badge color={getPlatformColor(post.platform, post.status)}>
                        {post.status}
                      </Badge>
                    </Flex>
                  </Card>
                ))}
              </Flex>
            )}
          </Box>
        </ScrollArea>
      );
    } else {
      // Month and Week view
      return (
        <>
          {/* Day Headers */}
          <Flex style={{ borderBottom: '1px solid var(--gray-4)', padding: '0.5rem 0' }}>
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <Box 
                key={day} 
                style={{ 
                  flex: 1, 
                  textAlign: 'center',
                  fontWeight: 'bold',
                  fontSize: '0.875rem',
                  color: 'var(--gray-11)'
                }}
              >
                {day}
              </Box>
            ))}
          </Flex>

          {/* Calendar Days */}
          <ScrollArea style={{ flex: 1 }}>
            <Box 
              style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(7, 1fr)',
                height: '100%'
              }}
            >
              {calendarDays.map((day, index) => (
                <Box
                  key={index}
                  onClick={() => handleDayClick(day.date)}
                  onDragOver={(e) => handleDragOver(e, day.date)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, day.date)}
                  style={{
                    minHeight: view === 'week' ? '400px' : '120px',
                    padding: '0.5rem',
                    border: '1px solid var(--gray-3)',
                    backgroundColor: dragOverDate?.toDateString() === day.date.toDateString() 
                      ? 'var(--blue-3)' 
                      : day.isCurrentMonth ? 'var(--gray-1)' : 'var(--gray-2)',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  onMouseEnter={(e) => {
                    if (!dragOverDate) {
                      e.currentTarget.style.backgroundColor = 'var(--gray-3)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!dragOverDate || dragOverDate.toDateString() !== day.date.toDateString()) {
                      e.currentTarget.style.backgroundColor = day.isCurrentMonth ? 'var(--gray-1)' : 'var(--gray-2)';
                    }
                  }}
                >
                  <Text 
                    size="2" 
                    weight={day.date.toDateString() === new Date().toDateString() ? 'bold' : 'regular'}
                    color={day.isCurrentMonth ? undefined : 'gray'}
                  >
                    {day.date.getDate()}
                  </Text>

                  <ScrollArea style={{ maxHeight: view === 'week' ? '350px' : '80px', marginTop: '0.5rem' }}>
                    <Flex direction="column" gap="1">
                      {day.posts.map((post, postIndex) => (
                        <Box
                          key={post.id}
                          draggable={post.status !== 'published'}
                          onDragStart={(e) => handleDragStart(e, post)}
                          onDragEnd={handleDragEnd}
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingPost(post);
                            setIsAddPostOpen(true);
                          }}
                          style={{
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            backgroundColor: post.status === 'published' 
                              ? 'var(--gray-3)' 
                              : `var(--${getPlatformColor(post.platform)}-3)`,
                            border: post.status === 'published'
                              ? '1px solid var(--gray-6)'
                              : `1px solid var(--${getPlatformColor(post.platform)}-6)`,
                            cursor: post.status === 'published' ? 'pointer' : 'move',
                            fontSize: '0.75rem',
                            marginBottom: '2px',
                            opacity: post.status === 'published' ? 0.7 : 1,
                            userSelect: 'none'
                          }}
                        >
                          <Flex align="center" gap="1">
                            {post.status !== 'published' && (
                              <DragHandleDots2Icon 
                                style={{ 
                                  cursor: 'move', 
                                  opacity: 0.5,
                                  minWidth: '12px'
                                }} 
                              />
                            )}
                            <Box style={{ opacity: post.status === 'published' ? 0.6 : 1 }}>
                              {getPlatformIcon(post.platform)}
                            </Box>
                            <Text size="1" style={{ 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis',
                              whiteSpace: view === 'week' ? 'normal' : 'nowrap',
                              lineHeight: '1.2',
                              color: post.status === 'published' ? 'var(--gray-11)' : undefined
                            }}>
                              {view === 'week' ? (
                                <>
                                  <Text weight="medium" size="1">
                                    {new Date(post.scheduledDate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                  </Text>
                                  {' - '}
                                  {post.content.substring(0, 50)}
                                  {post.content.length > 50 && '...'}
                                  {post.status === 'published' && ' ✓'}
                                </>
                              ) : (
                                <>
                                  {post.content.substring(0, 30) + (post.content.length > 30 ? '...' : '')}
                                  {post.status === 'published' && ' ✓'}
                                </>
                              )}
                            </Text>
                          </Flex>
                        </Box>
                      ))}
                    </Flex>
                  </ScrollArea>
                </Box>
              ))}
            </Box>
          </ScrollArea>
        </>
      );
    }
  };

  return (
    <Box style={{ padding: '2rem', height: '100vh', overflow: 'auto' }}>
      {/* Header */}
      <Flex justify="between" align="center" mb="4">
        <Box>
          <Heading size="7">Marketing Calendar</Heading>
          <Flex align="center" gap="2" mt="2">
            <PersonIcon />
            <Select.Root value={selectedClientId} onValueChange={setSelectedClientId}>
              <Select.Trigger style={{ minWidth: '200px' }} />
              <Select.Content>
                <Select.Item value="nbrain">nBrain (Default)</Select.Item>
                <Select.Separator />
                {clients.map(client => (
                  <Select.Item key={client.id} value={client.id}>
                    {client.name}
                  </Select.Item>
                ))}
              </Select.Content>
            </Select.Root>
            <Text size="2" color="gray">
              {selectedClientId === 'nbrain' 
                ? 'Managing nBrain marketing content' 
                : `Managing content for ${selectedClient?.name}`}
            </Text>
          </Flex>
        </Box>
        <Flex gap="2">
          {isBulkMode && (
            <>
              <Text size="2" color="gray" style={{ alignSelf: 'center' }}>
                {selectedPostIds.size} selected
              </Text>
              <Button 
                variant="soft" 
                size="2"
                onClick={selectAllPosts}
              >
                Select All
              </Button>
              <Button 
                variant="soft" 
                size="2"
                color="red"
                onClick={handleBulkDelete}
                disabled={selectedPostIds.size === 0}
              >
                Delete Selected
              </Button>
              <Button 
                variant="ghost" 
                size="2"
                onClick={() => {
                  setIsBulkMode(false);
                  clearSelection();
                }}
              >
                Cancel
              </Button>
              <Separator orientation="vertical" style={{ height: '24px' }} />
            </>
          )}
          
          {!isBulkMode && (
            <Button 
              variant="ghost"
              onClick={() => setIsBulkMode(true)}
              style={{ marginRight: '8px' }}
            >
              <DotsHorizontalIcon /> Bulk Edit
            </Button>
          )}
          
          <Button 
            variant="soft"
            onClick={() => setIsBulkTemplateOpen(true)}
          >
            <CalendarIcon /> Bulk Template
          </Button>
          <Button onClick={() => {
            setSelectedDate(new Date());
            setIsAddPostOpen(true);
          }}>
            <PlusIcon /> New Post
          </Button>
        </Flex>
      </Flex>

      {/* Controls */}
      <Card mb="4">
        <Flex justify="between" align="center">
          <Flex gap="3" align="center">
            <Flex gap="1" align="center">
              <IconButton 
                variant="soft" 
                onClick={() => navigate('prev')}
              >
                <ChevronLeftIcon />
              </IconButton>
              <IconButton 
                variant="soft" 
                onClick={() => navigate('next')}
              >
                <ChevronRightIcon />
              </IconButton>
            </Flex>
            
            <Heading size="4" style={{ margin: 0, lineHeight: 1 }}>
              {getDateRangeText()}
            </Heading>
            
            <Button 
              variant="soft" 
              size="2"
              onClick={() => setCurrentDate(new Date())}
            >
              Today
            </Button>
          </Flex>

          <Flex gap="3" align="center">
            <Select.Root value={view} onValueChange={(v: 'month' | 'week' | 'day' | 'list') => setView(v)}>
              <Select.Trigger />
              <Select.Content>
                <Select.Item value="day">Day</Select.Item>
                <Select.Item value="week">Week</Select.Item>
                <Select.Item value="month">Month</Select.Item>
                <Select.Item value="list">List</Select.Item>
              </Select.Content>
            </Select.Root>

            <Select.Root 
              value={selectedPlatforms[0]} 
              onValueChange={(v) => setSelectedPlatforms([v])}
            >
              <Select.Trigger placeholder="All Platforms" />
              <Select.Content>
                <Select.Item value="all">All Platforms</Select.Item>
                <Select.Item value="twitter">Twitter</Select.Item>
                <Select.Item value="instagram">Instagram</Select.Item>
                <Select.Item value="linkedin">LinkedIn</Select.Item>
                <Select.Item value="facebook">Facebook</Select.Item>
                <Select.Item value="email">Email</Select.Item>
              </Select.Content>
            </Select.Root>
          </Flex>
        </Flex>
      </Card>

      {/* Calendar Grid */}
      <Card style={{ height: 'calc(100vh - 250px)', overflow: 'hidden' }}>
        <Box style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {isLoading ? (
            <Flex align="center" justify="center" style={{ height: '100%' }}>
              <Text color="gray">Loading posts...</Text>
            </Flex>
          ) : (
            renderCalendarContent()
          )}
        </Box>
      </Card>

      {/* Add/Edit Post Dialog */}
      <PostDialog />
      <BulkTemplateDialog />
    </Box>
  );
};

export default SocialMediaCalendar; 