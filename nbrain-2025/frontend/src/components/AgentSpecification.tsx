import { Box, Card, Flex, Heading, Text, Badge, Button, IconButton, Tabs, Grid } from '@radix-ui/themes';
import { Cross2Icon, DownloadIcon, CodeIcon, CheckCircledIcon, InfoCircledIcon, ClockIcon, UpdateIcon, Pencil1Icon } from '@radix-ui/react-icons';
import ReactMarkdown from 'react-markdown';
import api from '../api';
import { generateAgentSpecPDF } from '../utils/pdfGenerator';
import { useState, useEffect } from 'react';
import { EditableSection } from './EditableSection';
import { EditableComplexSection } from './EditableComplexSection';
import { TechnicalStackEditor } from './TechnicalStackEditor';
import { FutureEnhancementsEditor } from './FutureEnhancementsEditor';

interface AgentSpecProps {
    spec: {
        id?: string;
        title: string;
        summary: string;
        steps: string[];
        agent_stack: any;
        client_requirements: string[];
        agent_type?: string;
        status?: string;
        created_at?: string;
        conversation_history?: any[];
        implementation_estimate?: any;
        security_considerations?: any;
        future_enhancements?: any[];
    };
    onClose: () => void;
    onEdit?: () => void;
}

const AgentTypeColors = {
    customer_service: 'blue',
    data_analysis: 'green',
    content_creation: 'purple',
    process_automation: 'orange',
    other: 'gray'
} as const;

export const AgentSpecification = ({ spec, onClose, onEdit }: AgentSpecProps) => {
    console.log('AgentSpecification rendering with spec:', spec);
    const agentType = spec.agent_type || 'other';
    const typeColor = AgentTypeColors[agentType as keyof typeof AgentTypeColors] || 'gray';
    
    // State for edited specification
    const [editedSpec, setEditedSpec] = useState(spec);
    const [isCreatingDoc, setIsCreatingDoc] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    
    useEffect(() => {
        setEditedSpec(spec);
        setHasChanges(false);
    }, [spec]);

    const downloadSpec = () => {
        generateAgentSpecPDF(editedSpec);
    };
    
    const createGoogleDoc = async () => {
        setIsCreatingDoc(true);
        try {
            const response = await api.post('/agent-ideas/create-google-doc', editedSpec);
            if (response.data.success) {
                // Open the Google Doc in a new tab
                window.open(response.data.doc_url, '_blank');
            } else {
                alert('Failed to create Google Doc. Please try again.');
            }
        } catch (error: any) {
            console.error('Error creating Google Doc:', error);
            
            // Extract error message from response
            let errorMessage = 'There was an error creating the Google Doc.';
            
            if (error.response?.data?.detail) {
                // Handle FastAPI error response
                const detail = error.response.data.detail;
                if (detail.includes('Google Docs service not configured')) {
                    errorMessage = 'Google Docs integration is not configured on this server. Please use the PDF download option instead.';
                } else {
                    errorMessage = detail;
                }
            }
            
            alert(errorMessage);
        } finally {
            setIsCreatingDoc(false);
        }
    };

    const moveToProduction = async () => {
        try {
            // For now, send email to danny@nbrain.ai
            await api.post('/agent-ideas/move-to-production', {
                spec_id: editedSpec.id,
                spec_details: editedSpec
            });
            alert('Your agent specification has been sent to our team. We\'ll contact you shortly to discuss implementation!');
        } catch (error) {
            console.error('Error moving to production:', error);
            alert('There was an error sending your specification. Please try again.');
        }
    };
    
    // Helper function to update nested properties
    const updateSpec = (path: string, value: any) => {
        setEditedSpec(prev => {
            const newSpec = { ...prev };
            const keys = path.split('.');
            let current: any = newSpec;
            
            for (let i = 0; i < keys.length - 1; i++) {
                if (!(keys[i] in current)) {
                    current[keys[i]] = {};
                }
                current = current[keys[i]];
            }
            
            current[keys[keys.length - 1]] = value;
            setHasChanges(true);
            return newSpec;
        });
    };
    
    const saveChanges = async () => {
        if (!editedSpec.id) return;
        
        setIsSaving(true);
        try {
            await api.put(`/agent-ideas/${editedSpec.id}/full-update`, editedSpec);
            setHasChanges(false);
            alert('Changes saved successfully!');
        } catch (error) {
            console.error('Error saving changes:', error);
            alert('Failed to save changes. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <Box style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
            {/* Header */}
            <Flex justify="between" align="start" mb="6">
                <Box>
                    <Flex align="center" gap="3" mb="2">
                        <EditableSection
                            content={editedSpec.title}
                            onSave={(value) => updateSpec('title', value)}
                            renderContent={(content) => (
                                <Heading size="8">{content}</Heading>
                            )}
                        />
                        <Badge color={typeColor} size="2">
                            {spec.agent_type?.replace('_', ' ').toUpperCase() || 'CUSTOM'}
                        </Badge>
                        {editedSpec.status && (
                            <Badge color={editedSpec.status === 'completed' ? 'green' : 'gray'}>
                                {editedSpec.status}
                            </Badge>
                        )}
                    </Flex>
                    <EditableSection
                        content={editedSpec.summary}
                        onSave={(value) => updateSpec('summary', value)}
                        renderContent={(content) => (
                            <Text size="3" color="gray">{content}</Text>
                        )}
                    />
                </Box>
                <Flex gap="2">
                    {hasChanges && (
                        <Button 
                            variant="solid" 
                            onClick={saveChanges}
                            disabled={isSaving}
                        >
                            <UpdateIcon />
                            {isSaving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    )}
                    <Button 
                        variant="soft" 
                        onClick={createGoogleDoc}
                        disabled={isCreatingDoc}
                    >
                        {isCreatingDoc ? 'Creating...' : '📄 Create Google Doc'}
                    </Button>
                    <IconButton variant="soft" onClick={downloadSpec}>
                        <DownloadIcon />
                    </IconButton>
                    <IconButton variant="ghost" onClick={onClose}>
                        <Cross2Icon />
                    </IconButton>
                </Flex>
            </Flex>

            <Tabs.Root defaultValue="scope">
                <Tabs.List>
                    <Tabs.Trigger value="scope">Detailed Scope</Tabs.Trigger>
                    <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
                    <Tabs.Trigger value="technical">Technical Stack</Tabs.Trigger>
                    <Tabs.Trigger value="requirements">Requirements</Tabs.Trigger>
                    <Tabs.Trigger value="security">Security</Tabs.Trigger>
                    <Tabs.Trigger value="future">Future Enhancements</Tabs.Trigger>
                    {editedSpec.implementation_estimate && (
                        <Tabs.Trigger value="estimate">Cost Estimate</Tabs.Trigger>
                    )}
                </Tabs.List>

                <Box mt="4">
                    <Tabs.Content value="overview">
                        <Card>
                            <Heading size="5" mb="4">Implementation Steps</Heading>
                            <EditableSection
                                content={editedSpec.steps}
                                isArray={true}
                                onSave={(value) => updateSpec('steps', value)}
                                renderContent={(steps) => (
                                    <Flex direction="column" gap="3">
                                        {(steps as string[]).map((step, index) => (
                                            <Flex key={index} gap="3" align="start">
                                                <Flex
                                                    align="center"
                                                    justify="center"
                                                    style={{
                                                        minWidth: '32px',
                                                        width: '32px',
                                                        height: '32px',
                                                        borderRadius: '50%',
                                                        backgroundColor: 'var(--accent-3)',
                                                        color: 'var(--accent-11)',
                                                        flexShrink: 0,
                                                        fontWeight: 'bold',
                                                        fontSize: '14px'
                                                    }}
                                                >
                                                    {index + 1}
                                                </Flex>
                                                <Box style={{ flex: 1, marginTop: '0' }}>
                                                    <Text style={{ lineHeight: '1.6' }}>
                                                        {step}
                                                    </Text>
                                                </Box>
                                            </Flex>
                                        ))}
                                    </Flex>
                                )}
                            />
                        </Card>
                    </Tabs.Content>

                    <Tabs.Content value="scope">
                        <Flex direction="column" gap="4">
                            {/* Executive Summary */}
                            <Card>
                                <Heading size="5" mb="4">Executive Summary</Heading>
                                <Text size="3" style={{ lineHeight: '1.8' }}>
                                    {editedSpec.summary}
                                </Text>
                                <Box mt="4">
                                    <Text size="3" weight="bold">Value Proposition:</Text>
                                    <Text size="3" style={{ lineHeight: '1.8', marginTop: '0.5rem' }}>
                                        This AI agent will transform your {editedSpec.agent_type?.replace('_', ' ')} operations by automating 
                                        key processes, reducing operational costs by up to 90%, and improving response times from hours 
                                        to seconds. By leveraging cutting-edge AI technology, your team will be freed from repetitive 
                                        tasks to focus on high-value strategic initiatives.
                                    </Text>
                                </Box>
                            </Card>

                            {/* Business Case */}
                            <Card>
                                <Heading size="5" mb="4">Business Case & ROI</Heading>
                                <Grid columns="2" gap="4">
                                    <Box>
                                        <Heading size="3" mb="2">Current State Challenges</Heading>
                                        <Flex direction="column" gap="2">
                                            <Text size="2">• Manual processes consuming valuable human resources</Text>
                                            <Text size="2">• Inconsistent quality and response times</Text>
                                            <Text size="2">• Limited scalability with growing demands</Text>
                                            <Text size="2">• High operational costs and error rates</Text>
                                        </Flex>
                                    </Box>
                                    <Box>
                                        <Heading size="3" mb="2">Future State Benefits</Heading>
                                        <Flex direction="column" gap="2">
                                            <Text size="2">• 24/7 automated operations with consistent quality</Text>
                                            <Text size="2">• Instant response times and infinite scalability</Text>
                                            <Text size="2">• 90% reduction in operational costs</Text>
                                            <Text size="2">• Data-driven insights for continuous improvement</Text>
                                        </Flex>
                                    </Box>
                                </Grid>
                            </Card>

                            {/* Detailed Implementation Plan */}
                            <Card>
                                <Heading size="5" mb="4">Detailed Implementation Plan</Heading>
                                {editedSpec.steps.map((step, index) => (
                                    <Box key={index} mb="4">
                                        <Flex align="center" gap="2" mb="2">
                                            <Badge size="2" variant="solid">{index + 1}</Badge>
                                            <Heading size="4">{step.split(':')[0]}</Heading>
                                        </Flex>
                                        <Box pl="3" style={{ borderLeft: '3px solid var(--accent-6)' }}>
                                            <Text size="3" style={{ lineHeight: '1.8' }}>
                                                {step.split(':').slice(1).join(':').trim() || step}
                                            </Text>
                                            <Box mt="2">
                                                <Text size="2" color="gray">
                                                    <strong>Deliverables:</strong> Fully functional {step.toLowerCase().includes('api') ? 'API endpoints' : 
                                                    step.toLowerCase().includes('test') ? 'test reports and quality assurance documentation' :
                                                    step.toLowerCase().includes('deploy') ? 'production-ready deployment with monitoring' :
                                                    'implementation artifacts and documentation'}
                                                </Text>
                                            </Box>
                                        </Box>
                                    </Box>
                                ))}
                            </Card>

                            {/* Success Metrics */}
                            <Card>
                                <Heading size="5" mb="4">Success Metrics & KPIs</Heading>
                                <Grid columns="3" gap="4">
                                    <Box>
                                        <Heading size="3" mb="2" color="green">Efficiency Gains</Heading>
                                        <Text size="6" weight="bold" color="green" style={{ display: 'block' }}>90%</Text>
                                        <Text size="2" color="gray" style={{ marginTop: '0.5rem' }}>Reduction in processing time</Text>
                                    </Box>
                                    <Box>
                                        <Heading size="3" mb="2" color="blue">Cost Savings</Heading>
                                        <Text size="6" weight="bold" color="blue" style={{ display: 'block' }}>85%</Text>
                                        <Text size="2" color="gray" style={{ marginTop: '0.5rem' }}>Lower operational costs</Text>
                                    </Box>
                                    <Box>
                                        <Heading size="3" mb="2" color="purple">Quality Improvement</Heading>
                                        <Text size="6" weight="bold" color="purple" style={{ display: 'block' }}>99%</Text>
                                        <Text size="2" color="gray" style={{ marginTop: '0.5rem' }}>Consistency in outputs</Text>
                                    </Box>
                                </Grid>
                            </Card>

                            {/* Risk Mitigation */}
                            <Card>
                                <Heading size="5" mb="4">Risk Mitigation Strategy</Heading>
                                <Flex direction="column" gap="3">
                                    <Box>
                                        <Flex align="center" gap="2" mb="1">
                                            <Badge color="yellow">Medium Risk</Badge>
                                            <Text weight="bold">Data Privacy & Security</Text>
                                        </Flex>
                                        <Text size="2" style={{ paddingLeft: '12px' }}>
                                            Mitigation: Implement end-to-end encryption, role-based access control, and regular security audits.
                                        </Text>
                                    </Box>
                                    <Box>
                                        <Flex align="center" gap="2" mb="1">
                                            <Badge color="orange">Low Risk</Badge>
                                            <Text weight="bold">User Adoption</Text>
                                        </Flex>
                                        <Text size="2" style={{ paddingLeft: '12px' }}>
                                            Mitigation: Comprehensive training program, intuitive UI design, and phased rollout approach.
                                        </Text>
                                    </Box>
                                    <Box>
                                        <Flex align="center" gap="2" mb="1">
                                            <Badge color="green">Minimal Risk</Badge>
                                            <Text weight="bold">Technical Integration</Text>
                                        </Flex>
                                        <Text size="2" style={{ paddingLeft: '12px' }}>
                                            Mitigation: Use of industry-standard APIs, extensive testing, and fallback mechanisms.
                                        </Text>
                                    </Box>
                                </Flex>
                            </Card>
                        </Flex>
                    </Tabs.Content>

                    <Tabs.Content value="technical">
                        <Card>
                            <Heading size="5" mb="4">
                                <Flex align="center" gap="2">
                                    <CodeIcon />
                                    Technical Stack
                                </Flex>
                            </Heading>
                            
                            <Box style={{ position: 'relative' }}>
                                <IconButton
                                    size="1"
                                    variant="ghost"
                                    onClick={() => {
                                        // For now, we'll use the simple editor
                                        // In the future, we can create a more complex editor for the new structure
                                    }}
                                    style={{
                                        position: 'absolute',
                                        top: 0,
                                        right: 0
                                    }}
                                >
                                    <Pencil1Icon />
                                </IconButton>
                                
                                <Flex direction="column" gap="4">
                                    {Object.entries(editedSpec.agent_stack).map(([key, value]: [string, any]) => (
                                        <Box key={key}>
                                            <Heading size="4" mb="2" style={{ textTransform: 'capitalize' }}>
                                                {key.replace(/_/g, ' ')}
                                            </Heading>
                                            <Card style={{ backgroundColor: 'var(--gray-2)' }}>
                                                {key === 'llm_model' && typeof value === 'object' && value !== null && value.primary_model ? (
                                                    // Special handling for new LLM model structure
                                                    <Flex direction="column" gap="3">
                                                        {/* Primary Model */}
                                                        {value.primary_model && (
                                                            <Box>
                                                                <Text size="3" weight="bold" color="green">Primary Model</Text>
                                                                <Box mt="1" ml="3">
                                                                    <Text size="2">
                                                                        <strong>Recommendation:</strong> {value.primary_model.recommendation}
                                                                    </Text>
                                                                    <Text size="2" mt="1">
                                                                        <strong>Provider:</strong> {value.primary_model.provider}
                                                                    </Text>
                                                                    {value.primary_model.strengths && (
                                                                        <Box mt="1">
                                                                            <Text size="2" weight="bold">Strengths:</Text>
                                                                            <Flex gap="2" wrap="wrap" mt="1">
                                                                                {value.primary_model.strengths.map((strength: string, idx: number) => (
                                                                                    <Badge key={idx} variant="soft" size="1">
                                                                                        {strength}
                                                                                    </Badge>
                                                                                ))}
                                                                            </Flex>
                                                                        </Box>
                                                                    )}
                                                                    <Text size="2" mt="1">
                                                                        <strong>Reasoning:</strong> {value.primary_model.reasoning}
                                                                    </Text>
                                                                </Box>
                                                            </Box>
                                                        )}
                                                        
                                                        {/* Specialized Models */}
                                                        {value.specialized_models && (
                                                            <Box>
                                                                <Text size="3" weight="bold" color="blue">Specialized Models</Text>
                                                                <Grid columns="2" gap="3" mt="2">
                                                                    {Object.entries(value.specialized_models).map(([modelType, modelInfo]: [string, any]) => (
                                                                        <Card key={modelType}>
                                                                            <Text size="2" weight="bold" style={{ textTransform: 'capitalize' }}>
                                                                                {modelType.replace(/_/g, ' ')}
                                                                            </Text>
                                                                            <Text size="1" mt="1">
                                                                                {modelInfo.model}
                                                                            </Text>
                                                                            <Text size="1" color="gray" mt="1">
                                                                                {modelInfo.use_cases}
                                                                            </Text>
                                                                        </Card>
                                                                    ))}
                                                                </Grid>
                                                            </Box>
                                                        )}
                                                        
                                                        {/* Router Configuration */}
                                                        {value.router_configuration && (
                                                            <Box>
                                                                <Text size="3" weight="bold" color="purple">Router Configuration</Text>
                                                                <Box mt="1" ml="3">
                                                                    <Badge color={value.router_configuration.enabled === 'true' ? 'green' : 'gray'}>
                                                                        Router {value.router_configuration.enabled === 'true' ? 'Enabled' : 'Disabled'}
                                                                    </Badge>
                                                                    {value.router_configuration.enabled === 'true' && (
                                                                        <Box mt="2">
                                                                            <Text size="2">
                                                                                <strong>Strategy:</strong> {value.router_configuration.routing_strategy}
                                                                            </Text>
                                                                            <Text size="2" mt="1">
                                                                                <strong>Logic:</strong> {value.router_configuration.router_logic}
                                                                            </Text>
                                                                            <Text size="2" mt="1">
                                                                                <strong>Fallback:</strong> {value.router_configuration.fallback_model}
                                                                            </Text>
                                                                        </Box>
                                                                    )}
                                                                </Box>
                                                            </Box>
                                                        )}
                                                        
                                                        {/* Cost Optimization */}
                                                        {value.cost_optimization && (
                                                            <Box>
                                                                <Text size="3" weight="bold" color="orange">Cost Optimization</Text>
                                                                <Box mt="1" ml="3">
                                                                    <Text size="2">
                                                                        <strong>Strategy:</strong> {value.cost_optimization.strategy}
                                                                    </Text>
                                                                    <Text size="2" mt="1">
                                                                        <strong>Estimated Monthly Cost:</strong> {value.cost_optimization.estimated_monthly_cost}
                                                                    </Text>
                                                                </Box>
                                                            </Box>
                                                        )}
                                                    </Flex>
                                                ) : typeof value === 'object' && value !== null && !Array.isArray(value) ? (
                                                    // Default object handling
                                                    <Flex direction="column" gap="2">
                                                        {Object.entries(value).map(([subKey, subValue]) => (
                                                            <Box key={subKey}>
                                                                <Text size="2" weight="bold" style={{ textTransform: 'capitalize' }}>
                                                                    {subKey.replace(/_/g, ' ')}:
                                                                </Text>
                                                                {typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue) ? (
                                                                    <Box ml="3">
                                                                        {Object.entries(subValue).map(([k, v]) => (
                                                                            <Text key={k} size="2">
                                                                                <strong>{k.replace(/_/g, ' ')}:</strong> {String(v)}
                                                                            </Text>
                                                                        ))}
                                                                    </Box>
                                                                ) : Array.isArray(subValue) ? (
                                                                    <Flex gap="2" wrap="wrap" mt="1">
                                                                        {subValue.map((item, idx) => (
                                                                            <Badge key={idx} variant="soft" size="1">
                                                                                {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                                                                            </Badge>
                                                                        ))}
                                                                    </Flex>
                                                                ) : (
                                                                    <Text size="2" ml="2">{String(subValue || '')}</Text>
                                                                )}
                                                            </Box>
                                                        ))}
                                                    </Flex>
                                                ) : Array.isArray(value) ? (
                                                    <Flex gap="2" wrap="wrap">
                                                        {value.map((item, idx) => (
                                                            <Badge key={idx} variant="soft">
                                                                {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                                                            </Badge>
                                                        ))}
                                                    </Flex>
                                                ) : (
                                                    <Text>{value || 'Not specified'}</Text>
                                                )}
                                            </Card>
                                        </Box>
                                    ))}
                                </Flex>
                            </Box>
                        </Card>
                    </Tabs.Content>

                    <Tabs.Content value="requirements">
                        <Card>
                            <Heading size="5" mb="4">
                                <Flex align="center" gap="2">
                                    <InfoCircledIcon />
                                    Client Requirements
                                </Flex>
                            </Heading>
                            
                            <EditableSection
                                content={editedSpec.client_requirements}
                                isArray={true}
                                onSave={(value) => updateSpec('client_requirements', value)}
                                renderContent={(requirements) => (
                                    <Flex direction="column" gap="3">
                                        {(requirements as string[]).map((req, index) => (
                                            <Flex key={index} gap="2" align="start">
                                                <CheckCircledIcon 
                                                    style={{ 
                                                        color: 'var(--accent-9)', 
                                                        minWidth: '20px',
                                                        marginTop: '2px'
                                                    }} 
                                                />
                                                <Text>{req}</Text>
                                            </Flex>
                                        ))}
                                    </Flex>
                                )}
                            />
                        </Card>
                    </Tabs.Content>

                    <Tabs.Content value="security">
                        <Card>
                            <Heading size="5" mb="4">
                                <Flex align="center" gap="2">
                                    🔒 Security Considerations
                                </Flex>
                            </Heading>
                            
                            {editedSpec.security_considerations ? (
                                <EditableComplexSection
                                    content={editedSpec.security_considerations}
                                    onSave={(value) => updateSpec('security_considerations', value)}
                                    renderContent={(security) => (
                                        <Flex direction="column" gap="4">
                                            {Object.entries(security).map(([category, details]) => (
                                                <Box key={category}>
                                                    <Heading size="4" mb="2" style={{ textTransform: 'capitalize' }}>
                                                        {category.replace(/_/g, ' ')}
                                                    </Heading>
                                                    <Card style={{ backgroundColor: 'var(--gray-2)' }}>
                                                        {typeof details === 'object' && details !== null ? (
                                                            <Flex direction="column" gap="2">
                                                                {Object.entries(details).map(([key, value]) => (
                                                                    <Box key={key}>
                                                                        <Text size="2" weight="bold" style={{ textTransform: 'capitalize' }}>
                                                                            {key.replace(/_/g, ' ')}:
                                                                        </Text>
                                                                        <Text size="2" ml="2">
                                                                            {Array.isArray(value) ? 
                                                                                value.join(', ') : 
                                                                                String(value || '')
                                                                            }
                                                                        </Text>
                                                                    </Box>
                                                                ))}
                                                            </Flex>
                                                        ) : (
                                                            <Text size="2">{String(details)}</Text>
                                                        )}
                                                    </Card>
                                                </Box>
                                            ))}
                                        </Flex>
                                    )}
                                />
                            ) : (
                                <Text color="gray">Security considerations will be added during implementation.</Text>
                            )}
                        </Card>
                    </Tabs.Content>

                    <Tabs.Content value="future">
                        <Card>
                            <Heading size="5" mb="4">
                                <Flex align="center" gap="2">
                                    ✨ Future Enhancement Ideas
                                </Flex>
                            </Heading>
                            
                            <FutureEnhancementsEditor
                                enhancements={editedSpec.future_enhancements || []}
                                onSave={(value) => updateSpec('future_enhancements', value)}
                            />
                        </Card>
                    </Tabs.Content>

                    {editedSpec.implementation_estimate && (
                        <Tabs.Content value="estimate">
                            <Card>
                                <Heading size="5" mb="4">
                                    <Flex align="center" gap="2">
                                        <ClockIcon />
                                        Implementation Estimate
                                    </Flex>
                                </Heading>
                                
                                <Flex direction="column" gap="4">
                                    {/* Traditional Approach */}
                                    <Box>
                                        <Heading size="4" mb="2">Traditional Development Approach</Heading>
                                        <Card style={{ backgroundColor: 'var(--gray-2)' }}>
                                            <Flex direction="column" gap="2">
                                                <Text size="5" weight="bold">
                                                    {editedSpec.implementation_estimate.traditional_approach.hours}
                                                </Text>
                                                {editedSpec.implementation_estimate.traditional_approach.breakdown && (
                                                    <Box mt="2">
                                                        <Text size="2" color="gray" weight="bold">Breakdown:</Text>
                                                        {Object.entries(editedSpec.implementation_estimate.traditional_approach.breakdown).map(([phase, hours]) => (
                                                            <Flex key={phase} justify="between" mt="1">
                                                                <Text size="2" style={{ textTransform: 'capitalize' }}>{phase}:</Text>
                                                                <Text size="2">{hours as string}</Text>
                                                            </Flex>
                                                        ))}
                                                    </Box>
                                                )}
                                                <Box mt="2" pt="2" style={{ borderTop: '1px solid var(--gray-4)' }}>
                                                    <Text size="4" weight="bold">
                                                        Total Cost: {editedSpec.implementation_estimate.traditional_approach.total_cost}
                                                    </Text>
                                                </Box>
                                            </Flex>
                                        </Card>
                                    </Box>

                                    {/* AI-Powered Approach */}
                                    <Box>
                                        <Heading size="4" mb="2">
                                            nBrain AI-Powered Approach
                                            <Badge color="green" style={{ marginLeft: '0.5rem' }}>90% Savings</Badge>
                                        </Heading>
                                        <Card style={{ backgroundColor: 'var(--accent-2)', border: '2px solid var(--accent-6)' }}>
                                            <Flex direction="column" gap="2">
                                                <Text size="5" weight="bold" color="green">
                                                    {editedSpec.implementation_estimate.ai_powered_approach.hours}
                                                </Text>
                                                <Text size="2">
                                                    {editedSpec.implementation_estimate.ai_powered_approach.methodology}
                                                </Text>
                                                <Box mt="2" pt="2" style={{ borderTop: '1px solid var(--accent-4)' }}>
                                                    <Text size="5" weight="bold" color="green">
                                                        Total Cost: {editedSpec.implementation_estimate.ai_powered_approach.total_cost}
                                                    </Text>
                                                    <Text size="2" color="gray" mt="1">
                                                        {editedSpec.implementation_estimate.ai_powered_approach.cost_savings}
                                                    </Text>
                                                </Box>
                                            </Flex>
                                        </Card>
                                    </Box>

                                    {/* Call to Action */}
                                    <Box mt="4" style={{ textAlign: 'center' }}>
                                        <Button size="3" onClick={moveToProduction}>
                                            Move to Production
                                        </Button>
                                        <Text size="1" color="gray" mt="2" style={{ display: 'block' }}>
                                            Our team will review your specification and contact you within 24 hours
                                        </Text>
                                    </Box>
                                </Flex>
                            </Card>
                        </Tabs.Content>
                    )}
                </Box>
            </Tabs.Root>

            {/* Action Buttons */}
            <Flex justify="center" gap="3" mt="6">
                <Button variant="soft" onClick={onClose}>
                    Close
                </Button>
                {onEdit && (
                    <Button onClick={onEdit}>
                        Edit Specification
                    </Button>
                )}
            </Flex>
        </Box>
    );
}; 