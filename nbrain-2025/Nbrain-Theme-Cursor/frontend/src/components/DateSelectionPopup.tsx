import React from 'react';
import { Box, Flex, Text, Separator, Switch, TextField, Checkbox } from '@radix-ui/themes';

const popupBoxStyle: React.CSSProperties = {
  position: 'absolute',
  bottom: 'calc(100% + 10px)',
  left: '50%',
  transform: 'translateX(-50%)',
  width: '300px',
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

export const DateSelectionPopup = () => {
  return (
    <Box style={popupBoxStyle}>
      <Flex direction="column" gap="3">
        <Box px="2">
            <Text as="div" size="2" weight="bold" color="gray">Date Selection</Text>
        </Box>
        
        <Flex justify="between" align="center" px="2">
          <Text size="2">Date Range</Text>
          <Switch />
        </Flex>

        <Separator my="1" size="4" />

        <PopupItem>Last 7 Days</PopupItem>
        <PopupItem>Last 30 Days</PopupItem>
        <PopupItem>This Month</PopupItem>
        <PopupItem>Last Month</PopupItem>
        
        <Separator my="1" size="4" />

        <Flex direction="column" gap="2" px="2">
            <Flex justify="between" align="center">
                <Text size="2">Start Date:</Text>
                <TextField.Root placeholder="mm/dd/yyyy" style={{ width: '120px' }}/>
            </Flex>
            <Flex justify="between" align="center">
                <Text size="2">End Date:</Text>
                <TextField.Root placeholder="mm/dd/yyyy" style={{ width: '120px' }} />
            </Flex>
        </Flex>
        
        <Separator my="1" size="4" />
        
        <Flex align="center" gap="2" px="2">
            <Checkbox id="compare"/>
            <Text as="label" htmlFor="compare" size="2">Compare to previous period</Text>
        </Flex>
      </Flex>
    </Box>
  );
}; 