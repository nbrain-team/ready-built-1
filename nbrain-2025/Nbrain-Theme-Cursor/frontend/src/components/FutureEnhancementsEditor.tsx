import React, { useState } from 'react';
import { Box, Card, Flex, Text, Button, IconButton, TextArea, Select, Badge } from '@radix-ui/themes';
import { TextField } from '@radix-ui/themes';
import { PlusIcon, Cross2Icon, CheckIcon, Pencil1Icon } from '@radix-ui/react-icons';

interface Enhancement {
    enhancement: string;
    description: string;
    impact?: string;
    implementation_effort?: string;
}

interface FutureEnhancementsEditorProps {
    enhancements: Enhancement[];
    onSave: (newEnhancements: Enhancement[]) => void;
}

export const FutureEnhancementsEditor: React.FC<FutureEnhancementsEditorProps> = ({ 
    enhancements, 
    onSave 
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedEnhancements, setEditedEnhancements] = useState<Enhancement[]>(enhancements || []);

    const handleSave = () => {
        onSave(editedEnhancements);
        setIsEditing(false);
    };

    const handleCancel = () => {
        setEditedEnhancements(enhancements || []);
        setIsEditing(false);
    };

    const updateEnhancement = (index: number, field: keyof Enhancement, value: string) => {
        const updated = [...editedEnhancements];
        updated[index] = { ...updated[index], [field]: value };
        setEditedEnhancements(updated);
    };

    const addEnhancement = () => {
        setEditedEnhancements([...editedEnhancements, {
            enhancement: 'New Enhancement',
            description: '',
            impact: '',
            implementation_effort: 'Medium'
        }]);
    };

    const removeEnhancement = (index: number) => {
        setEditedEnhancements(editedEnhancements.filter((_, i) => i !== index));
    };

    if (!isEditing) {
        return (
            <Box style={{ position: 'relative' }}>
                <IconButton
                    size="1"
                    variant="ghost"
                    onClick={() => setIsEditing(true)}
                    style={{
                        position: 'absolute',
                        top: 0,
                        right: 0
                    }}
                >
                    <Pencil1Icon />
                </IconButton>
                
                {enhancements && enhancements.length > 0 ? (
                    <Flex direction="column" gap="3">
                        {enhancements.map((enhancement: Enhancement, index: number) => (
                            <Card key={index} style={{ backgroundColor: 'var(--accent-2)' }}>
                                <Flex direction="column" gap="2">
                                    <Text size="4" weight="bold">
                                        {enhancement.enhancement}
                                    </Text>
                                    <Text size="2">
                                        {enhancement.description}
                                    </Text>
                                    {enhancement.impact && (
                                        <Box mt="2">
                                            <Text size="2" weight="bold" color="green">Impact:</Text>
                                            <Text size="2">{enhancement.impact}</Text>
                                        </Box>
                                    )}
                                    {enhancement.implementation_effort && (
                                        <Box mt="1">
                                            <Badge variant="soft">
                                                Effort: {enhancement.implementation_effort}
                                            </Badge>
                                        </Box>
                                    )}
                                </Flex>
                            </Card>
                        ))}
                    </Flex>
                ) : (
                    <Text color="gray">No future enhancements added yet.</Text>
                )}
            </Box>
        );
    }

    // Editing mode
    return (
        <Card>
            <Flex direction="column" gap="4">
                <Flex justify="between" align="center">
                    <Text size="3" weight="bold">Edit Future Enhancements</Text>
                    <Flex gap="2">
                        <Button size="2" onClick={handleSave}>
                            <CheckIcon />
                            Save
                        </Button>
                        <Button size="2" variant="soft" onClick={handleCancel}>
                            <Cross2Icon />
                            Cancel
                        </Button>
                    </Flex>
                </Flex>

                <Flex direction="column" gap="3">
                    {editedEnhancements.map((enhancement, index) => (
                        <Card key={index}>
                            <Flex direction="column" gap="2">
                                <Flex justify="between" align="start">
                                    <Text weight="bold">Enhancement {index + 1}</Text>
                                    <IconButton
                                        size="1"
                                        variant="ghost"
                                        color="red"
                                        onClick={() => removeEnhancement(index)}
                                    >
                                        <Cross2Icon />
                                    </IconButton>
                                </Flex>
                                
                                <TextField.Root
                                    placeholder="Enhancement Title"
                                    value={enhancement.enhancement}
                                    onChange={(e) => updateEnhancement(index, 'enhancement', e.target.value)}
                                />
                                
                                <TextArea
                                    placeholder="Description"
                                    value={enhancement.description}
                                    onChange={(e) => updateEnhancement(index, 'description', e.target.value)}
                                    style={{ minHeight: '80px' }}
                                />
                                
                                <TextField.Root
                                    placeholder="Business Impact"
                                    value={enhancement.impact || ''}
                                    onChange={(e) => updateEnhancement(index, 'impact', e.target.value)}
                                />
                                
                                <Select.Root
                                    value={enhancement.implementation_effort || 'Medium'}
                                    onValueChange={(value) => updateEnhancement(index, 'implementation_effort', value)}
                                >
                                    <Select.Trigger />
                                    <Select.Content>
                                        <Select.Item value="Low">Low Effort</Select.Item>
                                        <Select.Item value="Medium">Medium Effort</Select.Item>
                                        <Select.Item value="High">High Effort</Select.Item>
                                    </Select.Content>
                                </Select.Root>
                            </Flex>
                        </Card>
                    ))}
                </Flex>

                <Button onClick={addEnhancement} variant="soft">
                    <PlusIcon />
                    Add Enhancement
                </Button>
            </Flex>
        </Card>
    );
}; 