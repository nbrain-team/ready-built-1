import React, { useState } from 'react';
import { DropdownMenu, Button, Flex, Text, Badge } from '@radix-ui/themes';
import { ChevronDownIcon, ChatBubbleIcon, LightningBoltIcon, MagnifyingGlassIcon } from '@radix-ui/react-icons';

export type ChatMode = 'standard' | 'quick' | 'deep';

interface ChatModeSelectorProps {
    value: ChatMode;
    onChange: (mode: ChatMode) => void;
}

const modeConfig = {
    standard: {
        label: 'Standard',
        icon: <ChatBubbleIcon />,
        color: 'blue' as const,
        description: 'Balanced responses with context'
    },
    quick: {
        label: 'Quick Answer',
        icon: <LightningBoltIcon />,
        color: 'green' as const,
        description: 'Brief, concise responses'
    },
    deep: {
        label: 'Deep Research',
        icon: <MagnifyingGlassIcon />,
        color: 'purple' as const,
        description: 'Comprehensive analysis with follow-ups'
    }
};

export const ChatModeSelector: React.FC<ChatModeSelectorProps> = ({ value, onChange }) => {
    const currentMode = modeConfig[value];

    return (
        <DropdownMenu.Root>
            <DropdownMenu.Trigger>
                <Button 
                    variant="soft" 
                    color={currentMode.color}
                    style={{ minWidth: '140px' }}
                >
                    <Flex align="center" gap="2">
                        {currentMode.icon}
                        <Text size="2">{currentMode.label}</Text>
                        <ChevronDownIcon />
                    </Flex>
                </Button>
            </DropdownMenu.Trigger>

            <DropdownMenu.Content style={{ minWidth: '250px' }}>
                {Object.entries(modeConfig).map(([mode, config]) => (
                    <DropdownMenu.Item
                        key={mode}
                        onClick={() => onChange(mode as ChatMode)}
                        style={{ 
                            padding: '12px 16px',
                            minHeight: '60px'
                        }}
                    >
                        <Flex direction="column" gap="2">
                            <Flex align="center" gap="2">
                                <Badge color={config.color} variant="soft" size="1">
                                    {config.icon}
                                </Badge>
                                <Text size="2" weight="medium">{config.label}</Text>
                            </Flex>
                            <Text size="1" color="gray" style={{ 
                                marginLeft: '28px',
                                marginTop: '4px',
                                lineHeight: '1.4'
                            }}>
                                {config.description}
                            </Text>
                        </Flex>
                    </DropdownMenu.Item>
                ))}
            </DropdownMenu.Content>
        </DropdownMenu.Root>
    );
}; 