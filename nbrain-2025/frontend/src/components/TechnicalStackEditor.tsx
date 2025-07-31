import React, { useState } from 'react';
import { Box, Card, Flex, Text, Button, IconButton, Select, Badge } from '@radix-ui/themes';
import { TextField } from '@radix-ui/themes';
import { PlusIcon, Cross2Icon, CheckIcon, Pencil1Icon } from '@radix-ui/react-icons';

interface TechnicalStackEditorProps {
    stack: any;
    onSave: (newStack: any) => void;
}

export const TechnicalStackEditor: React.FC<TechnicalStackEditorProps> = ({ stack, onSave }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedStack, setEditedStack] = useState(stack);

    const handleSave = () => {
        onSave(editedStack);
        setIsEditing(false);
    };

    const handleCancel = () => {
        setEditedStack(stack);
        setIsEditing(false);
    };

    const updateStackItem = (key: string, field: string, value: any) => {
        setEditedStack({
            ...editedStack,
            [key]: {
                ...editedStack[key],
                [field]: value
            }
        });
    };

    const addStackItem = () => {
        const newKey = `component_${Date.now()}`;
        setEditedStack({
            ...editedStack,
            [newKey]: {
                name: 'New Component',
                technology: ''
            }
        });
    };

    const removeStackItem = (key: string) => {
        const newStack = { ...editedStack };
        delete newStack[key];
        setEditedStack(newStack);
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
                
                <Flex direction="column" gap="4">
                    {Object.entries(stack).map(([key, value]: [string, any]) => (
                        <Box key={key}>
                            <Text weight="bold" size="3" style={{ textTransform: 'capitalize' }}>
                                {key.replace(/_/g, ' ')}
                            </Text>
                            <Box mt="1">
                                {typeof value === 'object' && value !== null && !Array.isArray(value) ? (
                                    <Box ml="3">
                                        {Object.entries(value).map(([subKey, subValue]) => (
                                            <Box key={subKey} mb="2">
                                                <Text size="2" weight="bold" color="gray" style={{ textTransform: 'capitalize' }}>
                                                    {subKey.replace(/_/g, ' ')}:
                                                </Text>
                                                {Array.isArray(subValue) ? (
                                                    <Box>
                                                        {subValue.map((item, idx) => (
                                                            <Badge key={idx} variant="soft" mr="1">
                                                                {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                                                            </Badge>
                                                        ))}
                                                    </Box>
                                                ) : (
                                                    <Text size="2" ml="2">{String(subValue || '')}</Text>
                                                )}
                                            </Box>
                                        ))}
                                    </Box>
                                ) : Array.isArray(value) ? (
                                    <Flex gap="2" wrap="wrap">
                                        {value.map((item, idx) => (
                                            <Badge key={idx} variant="soft">
                                                {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                                            </Badge>
                                        ))}
                                    </Flex>
                                ) : (
                                    <Text color="gray">{value || 'Not specified'}</Text>
                                )}
                            </Box>
                        </Box>
                    ))}
                </Flex>
            </Box>
        );
    }

    // Editing mode
    return (
        <Card>
            <Flex direction="column" gap="4">
                <Flex justify="between" align="center">
                    <Text size="3" weight="bold">Edit Technical Stack</Text>
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

                {/* Common components */}
                <Box>
                    <Text size="2" weight="bold" mb="2">Core Components</Text>
                    <Flex direction="column" gap="3">
                        {/* LLM Model */}
                        <Card>
                            <Text weight="bold" mb="2">Language Model</Text>
                            <Flex direction="column" gap="2">
                                <TextField.Root
                                    placeholder="Provider (e.g., OpenAI, Anthropic)"
                                    value={editedStack.llm_model?.provider || ''}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStackItem('llm_model', 'provider', e.target.value)}
                                />
                                <TextField.Root
                                    placeholder="Model (e.g., GPT-4, Claude)"
                                    value={editedStack.llm_model?.model || ''}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStackItem('llm_model', 'model', e.target.value)}
                                />
                                <TextField.Root
                                    placeholder="Purpose"
                                    value={editedStack.llm_model?.purpose || ''}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStackItem('llm_model', 'purpose', e.target.value)}
                                />
                            </Flex>
                        </Card>

                        {/* Vector Database */}
                        <Card>
                            <Text weight="bold" mb="2">Vector Database</Text>
                            <Flex direction="column" gap="2">
                                <TextField.Root
                                    placeholder="Technology (e.g., Pinecone, Weaviate)"
                                    value={editedStack.vector_database?.technology || ''}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStackItem('vector_database', 'technology', e.target.value)}
                                />
                                <TextField.Root
                                    placeholder="Purpose"
                                    value={editedStack.vector_database?.purpose || ''}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStackItem('vector_database', 'purpose', e.target.value)}
                                />
                            </Flex>
                        </Card>

                        {/* Framework */}
                        <Card>
                            <Text weight="bold" mb="2">Framework</Text>
                            <Flex direction="column" gap="2">
                                <TextField.Root
                                    placeholder="Backend (e.g., FastAPI, Django)"
                                    value={editedStack.framework?.backend || ''}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStackItem('framework', 'backend', e.target.value)}
                                />
                                <TextField.Root
                                    placeholder="Frontend (e.g., React, Vue)"
                                    value={editedStack.framework?.frontend || ''}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStackItem('framework', 'frontend', e.target.value)}
                                />
                            </Flex>
                        </Card>

                        {/* Custom components */}
                        {Object.entries(editedStack).map(([key, value]: [string, any]) => {
                            if (['llm_model', 'vector_database', 'framework', 'retrieval_method', 'deployment'].includes(key)) {
                                return null;
                            }
                            return (
                                <Card key={key}>
                                    <Flex justify="between" align="start">
                                        <Box style={{ flex: 1 }}>
                                            <TextField.Root
                                                value={key.replace(/_/g, ' ')}
                                                style={{ textTransform: 'capitalize' }}
                                                disabled
                                            />
                                            <TextField.Root
                                                placeholder="Value"
                                                value={typeof value === 'string' ? value : JSON.stringify(value)}
                                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                                    const newStack = { ...editedStack };
                                                    newStack[key] = e.target.value;
                                                    setEditedStack(newStack);
                                                }}
                                            />
                                        </Box>
                                        <IconButton
                                            size="1"
                                            variant="ghost"
                                            color="red"
                                            onClick={() => removeStackItem(key)}
                                        >
                                            <Cross2Icon />
                                        </IconButton>
                                    </Flex>
                                </Card>
                            );
                        })}
                    </Flex>
                </Box>

                <Button onClick={addStackItem} variant="soft">
                    <PlusIcon />
                    Add Component
                </Button>
            </Flex>
        </Card>
    );
}; 