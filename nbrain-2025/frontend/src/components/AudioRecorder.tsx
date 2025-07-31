import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  Dialog, 
  Flex, 
  IconButton, 
  ScrollArea, 
  Separator, 
  Text,
  Badge,
  Heading,
  TextArea,
  Tabs
} from '@radix-ui/themes';
import { 
  DotFilledIcon, 
  PauseIcon, 
  PlayIcon, 
  StopIcon,
  SpeakerLoudIcon,
  Cross2Icon,
  CheckIcon,
  UpdateIcon,
  FileTextIcon,
  ReloadIcon,
  DesktopIcon,
  MixIcon
} from '@radix-ui/react-icons';
import api from '../api';

interface AudioRecorderProps {
  clientId?: string;
  clientName?: string;
  context?: 'client' | 'oracle';
  onSave?: (recording: RecordingData) => void;
}

interface RecordingData {
  id?: string;
  clientId?: string;
  clientName?: string;
  context: 'client' | 'oracle';
  audioUrl?: string;
  transcript: string;
  actionItems: string[];
  recommendations: string[];
  summary: string;
  duration: number;
  createdAt: Date;
}

interface TranscriptSegment {
  text: string;
  timestamp: number;
  isFinal: boolean;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  clientId,
  clientName,
  context = 'oracle',
  onSave
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [transcriptSegments, setTranscriptSegments] = useState<TranscriptSegment[]>([]);
  const [actionItems, setActionItems] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [summary, setSummary] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState('');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [manualNotes, setManualNotes] = useState('');
  const [transcript, setTranscript] = useState('');
  const [startTime, setStartTime] = useState<number | null>(null);
  
  // Add state for audio level visualization
  const [audioLevel, setAudioLevel] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  // Add state for audio source selection
  const [audioSource, setAudioSource] = useState<'microphone' | 'system' | 'both'>('microphone');
  const [showSourceDialog, setShowSourceDialog] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const websocketRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  const startRecording = async () => {
    try {
      let stream: MediaStream;
      
      if (audioSource === 'system' || audioSource === 'both') {
        try {
          // Request screen capture with audio
          const displayStream = await navigator.mediaDevices.getDisplayMedia({
            video: true, // We need video to be true for screen sharing
            audio: {
              echoCancellation: false,
              noiseSuppression: false,
              autoGainControl: false
            }
          } as any);
          
          // Extract only the audio track
          const audioTracks = displayStream.getAudioTracks();
          
          if (audioTracks.length === 0) {
            // If no audio from screen share, fall back to microphone
            setConnectionError('No audio available from screen share. Falling back to microphone.');
            displayStream.getTracks().forEach(track => track.stop());
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          } else {
            if (audioSource === 'both') {
              // Combine system audio with microphone
              const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
              
              // Create audio context to mix streams
              const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
              audioContextRef.current = audioContext;
              
              const dest = audioContext.createMediaStreamDestination();
              
              // Add system audio
              const systemSource = audioContext.createMediaStreamSource(new MediaStream(audioTracks));
              systemSource.connect(dest);
              
              // Add microphone audio
              const micSource = audioContext.createMediaStreamSource(micStream);
              micSource.connect(dest);
              
              stream = dest.stream;
              
              // Stop video track as we don't need it
              displayStream.getVideoTracks().forEach(track => track.stop());
            } else {
              // System audio only
              stream = new MediaStream(audioTracks);
              // Stop video track as we don't need it
              displayStream.getVideoTracks().forEach(track => track.stop());
            }
          }
        } catch (err) {
          console.error('Error accessing system audio:', err);
          setConnectionError('Failed to capture system audio. Please ensure you select "Share audio" when sharing your screen.');
          // Fall back to microphone
          stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }
      } else {
        // Microphone only
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      // Set up WebSocket connection for real-time transcription
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'https://adtv-backend-5u8n.onrender.com';
      const wsUrl = apiBaseUrl
        .replace('http:', 'ws:')
        .replace('https:', 'wss:') + '/api/recordings/ws/transcribe';
      
      const ws = new WebSocket(wsUrl);
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionError('');
        
        // Send initial configuration
        ws.send(JSON.stringify({
          type: 'config',
          clientId: clientId,
          context: context
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'transcript':
            setTranscript(prev => prev + ' ' + data.text);
            setIsTranscribing(false); // Reset transcribing indicator
            break;
          case 'action_item':
            setActionItems(prev => [...prev, data.item]);
            break;
          case 'recommendation':
            setRecommendations(prev => [...prev, data.recommendation]);
            break;
          case 'summary_update':
            setSummary(data.summary);
            break;
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Connection error. Real-time transcription may not work.');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };

      // Set up audio recording with audio level monitoring
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      
      // Monitor audio levels
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const checkAudioLevel = () => {
        if (isRecording && !isPaused) {
          analyser.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average / 255); // Normalize to 0-1
          requestAnimationFrame(checkAudioLevel);
        }
      };
      checkAudioLevel();

      // Check supported MIME types and use the best available
      const mimeType = (() => {
        const types = [
          'audio/webm;codecs=opus',
          'audio/webm',
          'audio/ogg;codecs=opus',
          'audio/mp4',
          'audio/mpeg'
        ];
        
        for (const type of types) {
          if (MediaRecorder.isTypeSupported(type)) {
            console.log(`Using MIME type: ${type}`);
            return type;
          }
        }
        
        console.warn('No preferred MIME type supported, using default');
        return undefined;
      })();

      // Create MediaRecorder with specific MIME type if supported
      const recorderOptions: MediaRecorderOptions = {};
      if (mimeType) {
        recorderOptions.mimeType = mimeType;
      }
      
      const finalRecorder = new MediaRecorder(stream, recorderOptions);
      mediaRecorderRef.current = finalRecorder;
      
      // Log the actual MIME type being used
      console.log(`MediaRecorder initialized with MIME type: ${finalRecorder.mimeType}`);

      finalRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          console.log(`Audio chunk received: ${event.data.size} bytes, type: ${event.data.type}`);
          audioChunksRef.current.push(event.data);
          
          // Send audio chunks to WebSocket if connected
          if (ws.readyState === WebSocket.OPEN && event.data.size > 0) {
            // Show transcribing indicator
            setIsTranscribing(true);
            // Send the audio data directly
            ws.send(event.data);
          }
        }
      };

      finalRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: finalRecorder.mimeType || 'audio/webm' });
        setAudioBlob(audioBlob);
        
        // Close WebSocket connection
        if (websocketRef.current) {
          websocketRef.current.close();
        }
      };

      // Start recording with larger chunks to ensure enough audio data
      finalRecorder.start(1000); // Capture audio in 1-second chunks for more complete segments
      setIsRecording(true);
      setStartTime(Date.now());
      
      // Store the stream reference
      streamRef.current = stream;
      
      // Start duration timer
      intervalRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Error starting recording:', error);
      setConnectionError('Failed to access microphone. Please check permissions.');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      
      // Pause duration timer
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      
      // Resume duration timer
      intervalRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    }
  };

  const stopRecording = async () => {
    setIsProcessing(true);

    // Stop media recorder
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
    }

    // Stop stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    
    // Stop audio context if it exists
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Close WebSocket
    if (websocketRef.current) {
      websocketRef.current.close();
    }

    // Clear timer
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Process and save recording
    if (audioChunksRef.current.length > 0) {
      const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current?.mimeType || 'audio/webm' });
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('duration', duration.toString());
      formData.append('context', context);
      
      if (clientId) {
        formData.append('clientId', clientId);
      }
      if (clientName) {
        formData.append('clientName', clientName);
      }

      // Join transcript segments
      const fullTranscript = transcriptSegments
        .map(seg => seg.text)
        .join(' ');
      
      formData.append('transcript', fullTranscript);
      formData.append('actionItems', JSON.stringify(actionItems));
      formData.append('recommendations', JSON.stringify(recommendations));
      formData.append('summary', summary);

      try {
        const response = await api.post('/api/recordings/save', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        const recordingData: RecordingData = {
          id: response.data.id,
          clientId,
          clientName,
          context,
          audioUrl: response.data.audioUrl,
          transcript: fullTranscript,
          actionItems,
          recommendations,
          summary,
          duration,
          createdAt: new Date()
        };

        if (onSave) {
          onSave(recordingData);
        }

        // Reset state
        resetRecording();
        
      } catch (error) {
        console.error('Error saving recording:', error);
        setError('Failed to save recording. Please try again.');
      }
    }

    setIsProcessing(false);
  };

  const resetRecording = () => {
    setDuration(0);
    setTranscriptSegments([]);
    setActionItems([]);
    setRecommendations([]);
    setSummary('');
    audioChunksRef.current = [];
    setError(null);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTime = (startTime: number | null) => {
    if (startTime === null) return '00:00';
    const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
    return formatDuration(elapsedSeconds);
  };

  const playRecording = () => {
    if (audioBlob) {
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play().catch(e => console.error('Error playing audio:', e));
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);

    const formData = new FormData();
    formData.append('audio', audioBlob!, 'recording.webm');
    formData.append('duration', duration.toString());
    formData.append('context', context);
    formData.append('transcript', transcript);
    formData.append('actionItems', JSON.stringify(actionItems));
    formData.append('recommendations', JSON.stringify(recommendations));
    formData.append('summary', summary);
    formData.append('manualNotes', manualNotes);

    if (clientId) {
      formData.append('clientId', clientId);
    }
    if (clientName) {
      formData.append('clientName', clientName);
    }

    try {
      const response = await api.post('/api/recordings/save', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const recordingData: RecordingData = {
        id: response.data.id,
        clientId,
        clientName,
        context,
        audioUrl: response.data.audioUrl,
        transcript: transcript,
        actionItems,
        recommendations,
        summary,
        duration,
        createdAt: new Date()
      };

      if (onSave) {
        onSave(recordingData);
      }

      resetRecording();
      setAudioBlob(null);
      setTranscript('');
      setActionItems([]);
      setRecommendations([]);
      setSummary('');
      setManualNotes('');

    } catch (error) {
      console.error('Error saving recording:', error);
      setSaveError('Failed to save recording. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Box style={{ width: '100%' }}>
      <Card>
        <Flex direction="column" gap="4">
          <Flex justify="between" align="center">
            <Flex align="center" gap="2">
              <SpeakerLoudIcon />
              <Heading size="3">Meeting Recorder</Heading>
            </Flex>
            {isRecording && (
              <Flex align="center" gap="3">
                <Badge color="blue" variant="soft">
                  {audioSource === 'microphone' && <SpeakerLoudIcon />}
                  {audioSource === 'system' && <DesktopIcon />}
                  {audioSource === 'both' && <MixIcon />}
                  {audioSource === 'microphone' && 'Mic'}
                  {audioSource === 'system' && 'System'}
                  {audioSource === 'both' && 'Mic + System'}
                </Badge>
                <Badge color="red" variant="solid">
                  <DotFilledIcon />
                  {formatTime(startTime)}
                </Badge>
              </Flex>
            )}
          </Flex>

          {connectionError && (
            <Text color="red" size="2">{connectionError}</Text>
          )}

          {/* System Audio Warning */}
          {isRecording && (audioSource === 'system' || audioSource === 'both') && (
            <Card variant="surface" style={{ backgroundColor: 'var(--amber-3)', borderColor: 'var(--amber-6)' }}>
              <Flex align="center" gap="2">
                <Text size="2" weight="medium" color="amber">
                  ⚠️ System Audio Active
                </Text>
                <Text size="1" color="gray">
                  Recording all computer audio. Close other apps like Otter.ai, music players, or video calls to avoid interference.
                </Text>
              </Flex>
            </Card>
          )}

          {/* Recording Controls */}
          <Flex gap="2" justify="center" align="center">
            {!isRecording && !audioBlob && (
              <Button size="3" onClick={() => setShowSourceDialog(true)}>
                <DotFilledIcon />
                Start Recording
              </Button>
            )}
            
            {isRecording && (
              <>
                {/* Audio Level Indicator */}
                <Box style={{ 
                  width: '100px', 
                  height: '8px', 
                  backgroundColor: 'var(--gray-4)',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  position: 'relative'
                }}>
                  <Box style={{ 
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    height: '100%',
                    width: `${audioLevel * 100}%`,
                    backgroundColor: audioLevel > 0.5 ? 'var(--red-9)' : audioLevel > 0.2 ? 'var(--green-9)' : 'var(--gray-6)',
                    transition: 'width 0.1s ease-out'
                  }} />
                </Box>
                
                {isTranscribing && (
                  <Badge color="blue" variant="soft">
                    <ReloadIcon className="spinning" style={{ marginRight: '4px' }} />
                    Transcribing...
                  </Badge>
                )}
                
                <Button size="3" variant="soft" onClick={isPaused ? resumeRecording : pauseRecording}>
                  {isPaused ? <PlayIcon /> : <PauseIcon />}
                  {isPaused ? 'Resume' : 'Pause'}
                </Button>
                <Button size="3" color="red" onClick={stopRecording}>
                  <StopIcon />
                  Stop Recording
                </Button>
              </>
            )}
            
            {audioBlob && !isRecording && (
              <>
                <Button size="3" variant="soft" onClick={playRecording}>
                  <PlayIcon />
                  Play Recording
                </Button>
                <Button size="3" onClick={handleSave} disabled={isSaving}>
                  <CheckIcon />
                  {isSaving ? 'Saving...' : 'Save Recording'}
                </Button>
                <Button size="3" variant="ghost" color="red" onClick={resetRecording}>
                  <Cross2Icon />
                  Discard
                </Button>
              </>
            )}
          </Flex>

          {/* Live Insights Section */}
          {(isRecording || audioBlob) && (
            <Box style={{ maxHeight: '400px', overflow: 'hidden' }}>
              <Tabs.Root defaultValue="transcript">
                <Tabs.List>
                  <Tabs.Trigger value="transcript">
                    <FileTextIcon />
                    Transcript
                  </Tabs.Trigger>
                  <Tabs.Trigger value="actions">
                    <CheckIcon />
                    Action Items ({actionItems.length})
                  </Tabs.Trigger>
                  <Tabs.Trigger value="recommendations">
                    <UpdateIcon />
                    Recommendations ({recommendations.length})
                  </Tabs.Trigger>
                  <Tabs.Trigger value="summary">
                    <FileTextIcon />
                    Summary
                  </Tabs.Trigger>
                </Tabs.List>

                <Box mt="3">
                  <Tabs.Content value="transcript">
                    <ScrollArea style={{ height: '200px' }}>
                      <Box p="3" style={{ backgroundColor: 'var(--gray-2)', borderRadius: '4px' }}>
                        {transcript || (
                          <Text color="gray" size="2">
                            {isRecording ? 'Waiting for speech...' : 'No transcript available'}
                          </Text>
                        )}
                      </Box>
                    </ScrollArea>
                  </Tabs.Content>

                  <Tabs.Content value="actions">
                    <ScrollArea style={{ height: '200px' }}>
                      <Flex direction="column" gap="2">
                        {actionItems.length === 0 ? (
                          <Text color="gray" size="2" style={{ padding: '1rem' }}>
                            No action items detected yet
                          </Text>
                        ) : (
                          actionItems.map((item, index) => (
                            <Card key={index}>
                              <Flex align="center" gap="2">
                                <CheckIcon color="green" />
                                <Text>{item}</Text>
                              </Flex>
                            </Card>
                          ))
                        )}
                      </Flex>
                    </ScrollArea>
                  </Tabs.Content>

                  <Tabs.Content value="recommendations">
                    <ScrollArea style={{ height: '200px' }}>
                      <Flex direction="column" gap="2">
                        {recommendations.length === 0 ? (
                          <Text color="gray" size="2" style={{ padding: '1rem' }}>
                            No recommendations yet
                          </Text>
                        ) : (
                          recommendations.map((rec, index) => (
                            <Card key={index}>
                              <Flex align="center" gap="2">
                                <UpdateIcon color="blue" />
                                <Text>{rec}</Text>
                              </Flex>
                            </Card>
                          ))
                        )}
                      </Flex>
                    </ScrollArea>
                  </Tabs.Content>

                  <Tabs.Content value="summary">
                    <ScrollArea style={{ height: '200px' }}>
                      <Box p="3" style={{ backgroundColor: 'var(--gray-2)', borderRadius: '4px' }}>
                        {summary || (
                          <Text color="gray" size="2">
                            Summary will appear here as the conversation progresses
                          </Text>
                        )}
                      </Box>
                    </ScrollArea>
                  </Tabs.Content>
                </Box>
              </Tabs.Root>
            </Box>
          )}

          {/* Manual Notes Section */}
          {(isRecording || audioBlob) && (
            <Box>
              <Separator size="4" mb="3" />
              <Text size="2" weight="medium" mb="2">Additional Notes (Optional)</Text>
              <TextArea
                placeholder="Add any manual notes or context..."
                rows={3}
                value={manualNotes}
                onChange={(e) => setManualNotes(e.target.value)}
              />
            </Box>
          )}

          {saveError && (
            <Text color="red" size="2">{saveError}</Text>
          )}
        </Flex>
      </Card>
      
      {/* Audio Source Selection Dialog */}
      <Dialog.Root open={showSourceDialog} onOpenChange={setShowSourceDialog}>
        <Dialog.Content style={{ maxWidth: 450 }}>
          <Dialog.Title>Select Audio Source</Dialog.Title>
          <Dialog.Description>
            Choose what audio to capture for your recording
          </Dialog.Description>
          
          <Flex direction="column" gap="3" mt="4">
            <Card 
              variant={audioSource === 'microphone' ? 'surface' : 'ghost'}
              style={{ cursor: 'pointer', padding: '1rem' }}
              onClick={() => setAudioSource('microphone')}
            >
              <Flex align="center" gap="3">
                <Box>
                  <SpeakerLoudIcon width="24" height="24" />
                </Box>
                <Box style={{ flex: 1 }}>
                  <Text weight="bold">Microphone Only</Text>
                  <Text size="2" color="gray">
                    Record your voice through your microphone
                  </Text>
                </Box>
                {audioSource === 'microphone' && <CheckIcon color="green" />}
              </Flex>
            </Card>
            
            <Card 
              variant={audioSource === 'system' ? 'surface' : 'ghost'}
              style={{ cursor: 'pointer', padding: '1rem' }}
              onClick={() => setAudioSource('system')}
            >
              <Flex align="center" gap="3">
                <Box>
                  <DesktopIcon width="24" height="24" />
                </Box>
                <Box style={{ flex: 1 }}>
                  <Text weight="bold">System Audio Only</Text>
                  <Text size="2" color="gray">
                    Record conference calls and browser audio (requires screen share)
                  </Text>
                </Box>
                {audioSource === 'system' && <CheckIcon color="green" />}
              </Flex>
            </Card>
            
            <Card 
              variant={audioSource === 'both' ? 'surface' : 'ghost'}
              style={{ cursor: 'pointer', padding: '1rem' }}
              onClick={() => setAudioSource('both')}
            >
              <Flex align="center" gap="3">
                <Box>
                  <MixIcon width="24" height="24" />
                </Box>
                <Box style={{ flex: 1 }}>
                  <Text weight="bold">Both (Recommended)</Text>
                  <Text size="2" color="gray">
                    Record your microphone and system audio together
                  </Text>
                </Box>
                {audioSource === 'both' && <CheckIcon color="green" />}
              </Flex>
            </Card>
            
            <Text size="1" color="gray" style={{ marginTop: '0.5rem' }}>
              Note: System audio recording will prompt you to share your screen. Make sure to check "Share audio" in the dialog.
            </Text>
          </Flex>
          
          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </Dialog.Close>
            <Button 
              onClick={() => {
                setShowSourceDialog(false);
                startRecording();
              }}
            >
              Start Recording
            </Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    </Box>
  );
}; 