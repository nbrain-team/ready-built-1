import React, { useState, useEffect } from 'react';
import { Box, TextArea, Button, Flex, IconButton, Card, Text } from '@radix-ui/themes';
import { Pencil1Icon, CheckIcon, Cross2Icon } from '@radix-ui/react-icons';

interface EditableComplexSectionProps {
    content: any;
    onSave: (newContent: any) => void;
    style?: React.CSSProperties;
    renderContent: (content: any) => React.ReactNode;
}

export const EditableComplexSection: React.FC<EditableComplexSectionProps> = ({ 
    content, 
    onSave, 
    style,
    renderContent
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState('');

    useEffect(() => {
        // Convert object to JSON string for editing
        setEditValue(JSON.stringify(content, null, 2));
    }, [content]);

    const handleSave = () => {
        try {
            const parsed = JSON.parse(editValue);
            onSave(parsed);
            setIsEditing(false);
        } catch (e) {
            alert('Invalid JSON format. Please check your input.');
        }
    };

    const handleCancel = () => {
        setEditValue(JSON.stringify(content, null, 2));
        setIsEditing(false);
    };

    if (isEditing) {
        return (
            <Box style={style}>
                <Card>
                    <Text size="2" color="gray" mb="2">
                        Edit as JSON (be careful with formatting):
                    </Text>
                    <TextArea
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        style={{ 
                            width: '100%', 
                            minHeight: '300px',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            lineHeight: '1.5'
                        }}
                        autoFocus
                    />
                    <Flex gap="2" mt="2">
                        <Button size="1" onClick={handleSave}>
                            <CheckIcon />
                            Save
                        </Button>
                        <Button size="1" variant="soft" onClick={handleCancel}>
                            <Cross2Icon />
                            Cancel
                        </Button>
                    </Flex>
                </Card>
            </Box>
        );
    }

    return (
        <Box style={{ position: 'relative', ...style }}>
            <Box 
                onMouseEnter={(e) => {
                    const btn = e.currentTarget.querySelector('.edit-btn') as HTMLElement;
                    if (btn) btn.style.opacity = '1';
                }}
                onMouseLeave={(e) => {
                    const btn = e.currentTarget.querySelector('.edit-btn') as HTMLElement;
                    if (btn) btn.style.opacity = '0';
                }}
            >
                {renderContent(content)}
                <IconButton
                    className="edit-btn"
                    size="1"
                    variant="ghost"
                    onClick={() => setIsEditing(true)}
                    style={{
                        position: 'absolute',
                        top: 0,
                        right: 0,
                        opacity: 0,
                        transition: 'opacity 0.2s'
                    }}
                >
                    <Pencil1Icon />
                </IconButton>
            </Box>
        </Box>
    );
}; 