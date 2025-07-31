import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, Paper, IconButton, Typography, Chip, LinearProgress, Fade } from '@mui/material';
import { Mic, MicOff, Phone, PhoneDisabled, VolumeUp, Settings } from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useAuth } from '../context/AuthContext';

// Styled components
const VoiceContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  borderRadius: 16,
  background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
  color: 'white',
  position: 'relative',
  overflow: 'hidden',
}));

const AudioVisualizer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: 120,
  gap: 4,
  margin: theme.spacing(3, 0),
}));

const AudioBar = styled(Box)<{ height: number }>(({ height }) => ({
  width: 4,
  height: `${height}%`,
  backgroundColor: 'rgba(255, 255, 255, 0.8)',
  borderRadius: 2,
  transition: 'height 0.1s ease',
}));

interface TranscriptLine {
  speaker: 'user' | 'ai';
  text: string;
  timestamp: Date;
  isPartial?: boolean;
}

interface VoiceIdeatorProps {
  onTranscriptUpdate?: (transcript: TranscriptLine[]) => void;
}

const VoiceIdeator: React.FC<VoiceIdeatorProps> = ({ onTranscriptUpdate }) => {
  const { user } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [audioLevels, setAudioLevels] = useState<number[]>(new Array(20).fill(10));
  const [conversationState, setConversationState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sessionId = useRef<string>(`session-${Date.now()}`);
  
  // Initialize WebSocket connection
  const connectVoice = useCallback(async () => {
    try {
      const wsUrl = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/voice/ws/${sessionId.current}`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('Voice WebSocket connected');
        setIsConnected(true);
        
        // Send auth message
        wsRef.current?.send(JSON.stringify({
          type: 'auth',
          token: localStorage.getItem('token')
        }));
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };
      
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  }, []);
  
  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'system':
        console.log('System:', data.message);
        setConversationState(data.state || 'idle');
        break;
        
      case 'partial_transcript':
        updateTranscript('user', data.text, true);
        break;
        
      case 'audio':
        // Handle incoming audio for TTS
        if (data.is_filler) {
          setConversationState('thinking');
        } else {
          setConversationState('speaking');
        }
        playAudio(data.audio_data);
        updateTranscript('ai', data.text);
        break;
        
      case 'interruption':
        console.log('Interruption handled:', data.response);
        setConversationState('listening');
        break;
        
      case 'response':
        updateTranscript('ai', data.ai_response);
        break;
        
      default:
        console.log('Unknown message type:', data.type);
    }
  };
  
  // Update transcript
  const updateTranscript = (speaker: 'user' | 'ai', text: string, isPartial = false) => {
    setTranscript(prev => {
      const newTranscript = [...prev];
      
      if (isPartial && newTranscript.length > 0 && newTranscript[newTranscript.length - 1].speaker === speaker) {
        // Update last partial transcript
        newTranscript[newTranscript.length - 1].text = text;
      } else {
        // Add new transcript line
        newTranscript.push({
          speaker,
          text,
          timestamp: new Date(),
          isPartial
        });
      }
      
      // Call the parent callback if provided
      if (onTranscriptUpdate) {
        onTranscriptUpdate(newTranscript);
      }
      
      return newTranscript;
    });
  };
  
  // Start audio recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // Create processor for audio visualization and streaming
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      
      processor.onaudioprocess = (e) => {
        if (isRecording && wsRef.current?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          
          // Update visualization
          updateAudioVisualization(inputData);
          
          // Convert to 16-bit PCM
          const pcmData = convertToPCM16(inputData);
          
          // Send audio data via WebSocket
          wsRef.current.send(pcmData);
        }
      };
      
      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
      
      setIsRecording(true);
      setConversationState('listening');
      
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };
  
  // Stop recording
  const stopRecording = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    setIsRecording(false);
    setConversationState('idle');
  };
  
  // Convert Float32Array to 16-bit PCM
  const convertToPCM16 = (float32Array: Float32Array): ArrayBuffer => {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    
    return buffer;
  };
  
  // Update audio visualization
  const updateAudioVisualization = (audioData: Float32Array) => {
    const levels = [];
    const chunkSize = Math.floor(audioData.length / 20);
    
    for (let i = 0; i < 20; i++) {
      let sum = 0;
      for (let j = 0; j < chunkSize; j++) {
        sum += Math.abs(audioData[i * chunkSize + j]);
      }
      const average = sum / chunkSize;
      levels.push(Math.min(100, average * 500));
    }
    
    setAudioLevels(levels);
  };
  
  // Play audio (placeholder - will integrate with Web Audio API)
  const playAudio = async (audioData: string) => {
    setIsSpeaking(true);
    // Decode base64 audio and play
    // Implementation depends on audio format from ElevenLabs
    setTimeout(() => setIsSpeaking(false), 2000); // Placeholder
  };
  
  // Toggle recording
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  return (
    <VoiceContainer elevation={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight="bold">
          Voice AI Ideator
        </Typography>
        <Box display="flex" gap={1}>
          <Chip
            label={conversationState}
            color={isConnected ? 'success' : 'default'}
            size="small"
          />
          <IconButton size="small" sx={{ color: 'white' }}>
            <Settings />
          </IconButton>
        </Box>
      </Box>
      
      {/* Audio Visualizer */}
      <AudioVisualizer>
        {audioLevels.map((level, index) => (
          <AudioBar key={index} height={level} />
        ))}
      </AudioVisualizer>
      
      {/* Status Message */}
      <Box textAlign="center" mb={3}>
        <Fade in={conversationState === 'thinking'}>
          <Typography variant="body1" sx={{ opacity: 0.8 }}>
            Thinking about your idea...
          </Typography>
        </Fade>
        <Fade in={conversationState === 'speaking'}>
          <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
            <VolumeUp />
            <Typography variant="body1">
              AI is speaking...
            </Typography>
          </Box>
        </Fade>
      </Box>
      
      {/* Control Buttons */}
      <Box display="flex" justifyContent="center" gap={2}>
        <IconButton
          onClick={connectVoice}
          disabled={isConnected}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            color: 'white',
            '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.3)' }
          }}
        >
          {isConnected ? <Phone /> : <PhoneDisabled />}
        </IconButton>
        
        <IconButton
          onClick={toggleRecording}
          disabled={!isConnected}
          sx={{
            backgroundColor: isRecording ? '#f44336' : 'rgba(255, 255, 255, 0.2)',
            color: 'white',
            width: 64,
            height: 64,
            '&:hover': { 
              backgroundColor: isRecording ? '#d32f2f' : 'rgba(255, 255, 255, 0.3)' 
            }
          }}
        >
          {isRecording ? <MicOff /> : <Mic />}
        </IconButton>
      </Box>
      
      {/* Progress indicator */}
      {(conversationState === 'thinking' || isSpeaking) && (
        <Box position="absolute" bottom={0} left={0} right={0}>
          <LinearProgress sx={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }} />
        </Box>
      )}
    </VoiceContainer>
  );
};

export default VoiceIdeator; 