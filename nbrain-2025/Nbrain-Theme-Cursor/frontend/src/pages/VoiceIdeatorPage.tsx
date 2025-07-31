import React, { useState } from 'react';
import { Container, Box, Paper, Typography, List, ListItem, ListItemText, Divider, Fade } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import VoiceIdeator from '../components/VoiceIdeator';
import { Person, SmartToy } from '@mui/icons-material';

interface TranscriptLine {
  speaker: 'user' | 'ai';
  text: string;
  timestamp: Date;
  isPartial?: boolean;
}

const VoiceIdeatorPage: React.FC = () => {
  const theme = useTheme();
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Voice AI Ideator
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Have a natural conversation with AI to explore and develop your agent ideas
        </Typography>
      </Box>
      
      <Box display="flex" gap={3} sx={{ flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Voice Interface */}
        <Box flex={1}>
          <VoiceIdeator onTranscriptUpdate={setTranscript} />
        </Box>
        
        {/* Transcript Panel */}
        <Box flex={1}>
          <Paper
            elevation={2}
            sx={{
              p: 3,
              borderRadius: 2,
              height: { md: 500 },
              overflowY: 'auto',
              backgroundColor: theme.palette.background.default,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Conversation Transcript
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {transcript.length === 0 ? (
              <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mt: 4 }}>
                Your conversation will appear here...
              </Typography>
            ) : (
              <List>
                {transcript.map((line, index) => (
                  <Fade in key={index} timeout={500}>
                    <ListItem
                      sx={{
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        backgroundColor: line.speaker === 'user' 
                          ? 'rgba(25, 118, 210, 0.08)' 
                          : 'rgba(76, 175, 80, 0.08)',
                        borderRadius: 2,
                        mb: 1,
                        opacity: line.isPartial ? 0.7 : 1,
                      }}
                    >
                      <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                        {line.speaker === 'user' ? (
                          <Person fontSize="small" color="primary" />
                        ) : (
                          <SmartToy fontSize="small" color="success" />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          {line.speaker === 'user' ? 'You' : 'AI Assistant'} • 
                          {line.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Box>
                      <ListItemText
                        primary={line.text}
                        sx={{
                          '& .MuiListItemText-primary': {
                            fontStyle: line.isPartial ? 'italic' : 'normal',
                          }
                        }}
                      />
                    </ListItem>
                  </Fade>
                ))}
              </List>
            )}
          </Paper>
        </Box>
      </Box>
      
      {/* Instructions */}
      <Paper
        elevation={1}
        sx={{
          mt: 3,
          p: 3,
          borderRadius: 2,
          backgroundColor: 'rgba(255, 193, 7, 0.08)',
        }}
      >
        <Typography variant="h6" gutterBottom>
          How to use Voice Ideator
        </Typography>
        <Typography variant="body2" component="ul" sx={{ pl: 2 }}>
          <li>Click the phone icon to connect to the voice service</li>
          <li>Press the microphone button to start speaking</li>
          <li>Describe your agent idea naturally - the AI will ask clarifying questions</li>
          <li>You can interrupt the AI at any time by speaking</li>
          <li>Your conversation is automatically saved and can be converted to an agent specification</li>
        </Typography>
      </Paper>
    </Container>
  );
};

export default VoiceIdeatorPage; 