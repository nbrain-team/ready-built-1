import React from 'react';
import { Box, Flex, Text } from '@radix-ui/themes';

const popupBoxStyle: React.CSSProperties = {
  position: 'absolute',
  bottom: 'calc(100% + 10px)',
  left: '50%',
  transform: 'translateX(-50%)',
  width: '260px',
  backgroundColor: 'white',
  borderRadius: 'var(--radius-3)',
  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  border: '1px solid var(--gray-a5)',
  padding: '1rem',
  zIndex: 10,
};

const PopupItem = ({ children }: { children: React.ReactNode }) => (
    <Text as="div" size="2" style={{ padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-2)', cursor: 'pointer' }}>
        {children}
    </Text>
);

export const DataSourcesPopup = () => {
  return (
    <Box style={popupBoxStyle}>
      <Flex direction="column" gap="1">
        <Box px="2" mb="1">
            <Text as="div" size="2" weight="bold" color="gray">Data Sources</Text>
        </Box>
        <PopupItem>Industry Data</PopupItem>
        <PopupItem>Client nBrain</PopupItem>
        <PopupItem>Best Practices</PopupItem>
      </Flex>
    </Box>
  );
}; 