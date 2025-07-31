import React, { useState, useEffect } from 'react';
import { Box, Card, Flex, Text, Badge, Button, ScrollArea, Heading, IconButton } from '@radix-ui/themes';
import { PlayIcon, FileTextIcon, CheckIcon, UpdateIcon, CalendarIcon, SpeakerLoudIcon } from '@radix-ui/react-icons';
import api from '../api';

interface Recording {
  id: string;
  clientName?: string;
  duration: number;
  transcript: string;
  actionItems: string[];
  recommendations: string[];
  summary: string;
  createdAt: string;
}

interface RecordingsListProps {
  context: 'client' | 'oracle';
  clientId?: string;
  onPlayRecording?: (recordingId: string) => void;
}

export const RecordingsList: React.FC<RecordingsListProps> = ({ context, clientId, onPlayRecording }) => {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRecording, setSelectedRecording] = useState<Recording | null>(null);

  useEffect(() => {
    fetchRecordings();
  }, [context, clientId]);

  const fetchRecordings = async () => {
    setIsLoading(true);
    try {
      const endpoint = context === 'client' && clientId 
        ? `/api/recordings/client/${clientId}`
        : '/api/recordings/oracle/recent';
      
      const response = await api.get(endpoint);
      setRecordings(response.data);
    } catch (error) {
      console.error('Error fetching recordings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (isLoading) {
    return (
      <Card>
        <Text>Loading recordings...</Text>
      </Card>
    );
  }

  if (recordings.length === 0) {
    return (
      <Card>
        <Flex direction="column" align="center" gap="3" style={{ padding: '2rem' }}>
          <SpeakerLoudIcon width="48" height="48" style={{ opacity: 0.3 }} />
          <Text color="gray">No recordings yet</Text>
        </Flex>
      </Card>
    );
  }

  return (
    <Box>
      <Heading size="4" mb="3">Past Recordings</Heading>
      <ScrollArea style={{ height: '400px' }}>
        <Flex direction="column" gap="3">
          {recordings.map((recording) => (
            <Card 
              key={recording.id}
              style={{ cursor: 'pointer' }}
              onClick={() => setSelectedRecording(recording === selectedRecording ? null : recording)}
            >
              <Flex direction="column" gap="3">
                {/* Recording Header */}
                <Flex justify="between" align="center">
                  <Flex align="center" gap="2">
                    <CalendarIcon />
                    <Text size="2">{formatDate(recording.createdAt)}</Text>
                    {recording.clientName && (
                      <Badge>{recording.clientName}</Badge>
                    )}
                  </Flex>
                  <Flex align="center" gap="2">
                    <Badge variant="soft">{formatDuration(recording.duration)}</Badge>
                    <IconButton 
                      size="1" 
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onPlayRecording) {
                          onPlayRecording(recording.id);
                        }
                      }}
                    >
                      <PlayIcon />
                    </IconButton>
                  </Flex>
                </Flex>

                {/* Summary */}
                {recording.summary && (
                  <Text size="2" style={{ fontStyle: 'italic' }}>
                    {recording.summary}
                  </Text>
                )}

                {/* Stats */}
                <Flex gap="3">
                  {recording.actionItems.length > 0 && (
                    <Flex align="center" gap="1">
                      <CheckIcon />
                      <Text size="1">{recording.actionItems.length} action items</Text>
                    </Flex>
                  )}
                  {recording.recommendations.length > 0 && (
                    <Flex align="center" gap="1">
                      <UpdateIcon />
                      <Text size="1">{recording.recommendations.length} recommendations</Text>
                    </Flex>
                  )}
                </Flex>

                {/* Expanded Details */}
                {selectedRecording?.id === recording.id && (
                  <Box mt="3" style={{ borderTop: '1px solid var(--gray-5)', paddingTop: '1rem' }}>
                    {/* Action Items */}
                    {recording.actionItems.length > 0 && (
                      <Box mb="3">
                        <Text size="2" weight="medium" mb="2">Action Items:</Text>
                        <Flex direction="column" gap="1">
                          {recording.actionItems.map((item, idx) => (
                            <Text key={idx} size="2">• {item}</Text>
                          ))}
                        </Flex>
                      </Box>
                    )}

                    {/* Recommendations */}
                    {recording.recommendations.length > 0 && (
                      <Box mb="3">
                        <Text size="2" weight="medium" mb="2">Recommendations:</Text>
                        <Flex direction="column" gap="1">
                          {recording.recommendations.map((rec, idx) => (
                            <Text key={idx} size="2">• {rec}</Text>
                          ))}
                        </Flex>
                      </Box>
                    )}

                    {/* Transcript */}
                    {recording.transcript && (
                      <Box>
                        <Text size="2" weight="medium" mb="2">Transcript:</Text>
                        <ScrollArea style={{ maxHeight: '200px' }}>
                          <Text size="2" style={{ lineHeight: '1.6' }}>
                            {recording.transcript}
                          </Text>
                        </ScrollArea>
                      </Box>
                    )}
                  </Box>
                )}
              </Flex>
            </Card>
          ))}
        </Flex>
      </ScrollArea>
    </Box>
  );
}; 