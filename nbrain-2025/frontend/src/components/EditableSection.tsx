import React, { useState, useEffect } from 'react';
import { Box, TextArea, Button, Flex, IconButton } from '@radix-ui/themes';
import { Pencil1Icon, CheckIcon, Cross2Icon } from '@radix-ui/react-icons';

interface EditableSectionProps {
    content: string | string[];
    onSave: (newContent: string | string[]) => void;
    isArray?: boolean;
    style?: React.CSSProperties;
    renderContent?: (content: string | string[]) => React.ReactNode;
}

export const EditableSection: React.FC<EditableSectionProps> = ({ 
    content, 
    onSave, 
    isArray = false,
    style,
    renderContent
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState('');

    useEffect(() => {
        if (isArray && Array.isArray(content)) {
            setEditValue(content.join('\n'));
        } else {
            setEditValue(String(content));
        }
    }, [content, isArray]);

    const handleSave = () => {
        if (isArray) {
            const newContent = editValue.split('\n').filter(line => line.trim());
            onSave(newContent);
        } else {
            onSave(editValue);
        }
        setIsEditing(false);
    };

    const handleCancel = () => {
        if (isArray && Array.isArray(content)) {
            setEditValue(content.join('\n'));
        } else {
            setEditValue(String(content));
        }
        setIsEditing(false);
    };

    if (isEditing) {
        return (
            <Box style={style}>
                <TextArea
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    style={{ 
                        width: '100%', 
                        minHeight: '100px',
                        fontFamily: 'inherit',
                        fontSize: 'inherit',
                        lineHeight: '1.6'
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
                {renderContent ? renderContent(content) : (
                    isArray && Array.isArray(content) ? (
                        content.map((item, index) => (
                            <Box key={index}>{item}</Box>
                        ))
                    ) : (
                        <Box>{String(content)}</Box>
                    )
                )}
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