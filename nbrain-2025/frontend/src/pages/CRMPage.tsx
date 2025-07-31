import { useState, useEffect } from 'react';
import { Box, Card, Flex, Heading, Text, Table, Button, TextField, Dialog, Badge, IconButton, Tabs, Grid, Select, ScrollArea, Separator } from '@radix-ui/themes';
import { PlusIcon, MagnifyingGlassIcon, ChevronDownIcon, ChevronRightIcon, FileTextIcon, LinkBreak2Icon, Cross2Icon, Pencil1Icon, CheckIcon, Link2Icon, PersonIcon, TrashIcon, CaretSortIcon } from '@radix-ui/react-icons';
import api from '../api';
import { useNavigate } from 'react-router-dom';

interface AgentIdea {
    id: string;
    title: string;
    summary: string;
    agent_type?: string;
    status: string;
}

interface CRMOpportunity {
    id: string;
    status: string;
    client_opportunity: string;
    lead_start_date?: string;
    lead_source?: string;
    referral_source?: string;
    product?: string;
    deal_status?: string;
    intro_call_date?: string;
    todo_next_steps?: string;
    discovery_call?: string;
    presentation_date?: string;
    proposal_sent?: string;
    estimated_pipeline_value?: string;
    deal_closed?: string;
    kickoff_scheduled?: string;
    actual_contract_value?: string;
    monthly_fees?: string;
    commission?: string;
    invoice_setup?: string;
    payment_1?: string;
    payment_2?: string;
    payment_3?: string;
    payment_4?: string;
    payment_5?: string;
    payment_6?: string;
    payment_7?: string;
    notes_next_steps?: string;
    created_at: string;
    updated_at?: string;
    documents: any[];
    agent_links: any[];
    contact_name?: string;
    contact_email?: string;
    contact_phone?: string;
    linkedin_profile?: string;
    website_url?: string;
    lead_status?: string;
    job_title?: string;
    company_address?: string;
    // New fields for expanded view
    opportunity_type?: string;
    owner?: string;
    sales_pipeline?: string;
    stage?: string;
    est_close_date?: string;
    close_date?: string;
    engagement_type?: string;
    win_likelihood?: string;
    forecast_category?: string;
}

// Define the lead source options
const LEAD_SOURCE_OPTIONS = [
    'Network',
    'LinkedIn', 
    'Email Mkt',
    'Referral Partner'
];

// Define lead status options (replacing deal status)
const LEAD_STATUS_OPTIONS = [
    'New Lead',
    'Working Lead',
    'Qualification Lead',
    'Unqualified Lead'
];

// Define opportunity type options
const OPPORTUNITY_TYPE_OPTIONS = [
    'Qualified Lead',
    'Current Client'
];

// Define sales pipeline options
const SALES_PIPELINE_OPTIONS = [
    'New Business',
    'Renewals',
    'Upsell'
];

// Define stage options
const STAGE_OPTIONS = [
    'Warm Lead',
    'Cold Lead',
    'Introduction',
    'Discovery',
    'Evaluation',
    'Proposal',
    'Negotiation',
    'Closed Won',
    'Closed Lost',
    'Dormant',
    'Post Sale Onboarding'
];

// Define engagement type options
const ENGAGEMENT_TYPE_OPTIONS = [
    'MRR',
    'One-time'
];

// Define win likelihood options
const WIN_LIKELIHOOD_OPTIONS = [
    { label: 'Discovery 10%', value: '10' },
    { label: 'Evaluation 50%', value: '50' },
    { label: 'Negotiation 80%', value: '80' },
    { label: 'Verbal Commit 95%', value: '95' },
    { label: 'Closed Won 100%', value: '100' },
    { label: 'Closed Lost 0%', value: '0' }
];

// Define forecast category options
const FORECAST_CATEGORY_OPTIONS = [
    'Pipeline',
    'Best Case',
    'Committed'
];

// Define common referral partners
const REFERRAL_PARTNER_OPTIONS = [
    'Partner A',
    'Partner B',
    'Partner C',
    'Other'
];

const CRMPage = () => {
    const [opportunities, setOpportunities] = useState<CRMOpportunity[]>([]);
    const [filteredOpportunities, setFilteredOpportunities] = useState<CRMOpportunity[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [dealStatusFilter, setDealStatusFilter] = useState<string>('all');
    const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
    const [selectedOpportunity, setSelectedOpportunity] = useState<CRMOpportunity | null>(null);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [editingField, setEditingField] = useState<{ id: string; field: string } | null>(null);
    const [editValue, setEditValue] = useState('');
    const [sortField, setSortField] = useState<string>('deal_status'); // Default sort by deal_status
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
    
    // Form state for create dialog with all requested fields
    const [createFormData, setCreateFormData] = useState({
        company_name: '',           // Company Name
        lead_status: 'New Lead',    // Lead Status
        primary_contact_name: '',   // Primary Contact Name
        primary_contact_email: '',  // Primary Contact Email
        primary_contact_phone: '',  // Primary Contact Phone
        job_title: '',             // Job Title
        company_address: '',       // Company Address
        linkedin_profile: '',      // LinkedIn Profile
        website: '',              // Website
        lead_source: 'Network',   // Lead Source
        referral_source: '',      // Referral Source
        lead_created_date: new Date().toISOString().split('T')[0]  // Lead Created Date
    });

    useEffect(() => {
        fetchOpportunities();
    }, []);

    useEffect(() => {
        let filtered = opportunities.filter(opp => {
            const searchLower = searchTerm.toLowerCase();
            const matchesSearch = (
                opp.client_opportunity.toLowerCase().includes(searchLower) ||
                opp.contact_name?.toLowerCase().includes(searchLower) ||
                opp.contact_email?.toLowerCase().includes(searchLower) ||
                opp.deal_status?.toLowerCase().includes(searchLower) ||
                opp.lead_source?.toLowerCase().includes(searchLower)
            );

            const matchesDealStatus = dealStatusFilter === 'all' || opp.deal_status === dealStatusFilter;

            return matchesSearch && matchesDealStatus;
        });

        // Sort the filtered results
        filtered.sort((a, b) => {
            // Always put Closed and Dead at the bottom
            const aIsClosedOrDead = a.deal_status === 'Closed' || a.deal_status === 'Dead';
            const bIsClosedOrDead = b.deal_status === 'Closed' || b.deal_status === 'Dead';
            
            if (aIsClosedOrDead && !bIsClosedOrDead) return 1;
            if (!aIsClosedOrDead && bIsClosedOrDead) return -1;
            
            // If sorting by deal_status, use the predefined order
            if (sortField === 'deal_status') {
                const aIndex = LEAD_STATUS_OPTIONS.indexOf(a.deal_status || '');
                const bIndex = LEAD_STATUS_OPTIONS.indexOf(b.deal_status || '');
                const aSort = aIndex === -1 ? LEAD_STATUS_OPTIONS.length : aIndex;
                const bSort = bIndex === -1 ? LEAD_STATUS_OPTIONS.length : bIndex;
                return sortDirection === 'asc' ? aSort - bSort : bSort - aSort;
            }
            
            // For other fields, do standard comparison
            const aValue = a[sortField as keyof CRMOpportunity] || '';
            const bValue = b[sortField as keyof CRMOpportunity] || '';
            
            if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
            if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        setFilteredOpportunities(filtered);
    }, [searchTerm, dealStatusFilter, opportunities, sortField, sortDirection]);

    const fetchOpportunities = async () => {
        try {
            const response = await api.get('/crm/opportunities');
            setOpportunities(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching opportunities:', error);
            setLoading(false);
        }
    };

    const toggleRowExpansion = (id: string) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedRows(newExpanded);
    };

    const getStatusColor = (status: string) => {
        // This is now for lead source colors
        switch (status.toLowerCase()) {
            case 'network': return 'blue';
            case 'linkedin': return 'purple';
            case 'email mkt': return 'green';
            default: return 'gray';
        }
    };

    const getDealStatusColor = (dealStatus?: string) => {
        if (!dealStatus) return 'gray';
        switch (dealStatus.toLowerCase()) {
            case 'cold lead': return 'gray';
            case 'intro email': return 'blue';
            case 'intro': return 'cyan';
            case 'warm lead': return 'orange';
            case 'discovery': return 'blue';
            case 'presentation': return 'green';
            case 'proposal': return 'purple';
            case 'closed': return 'green';
            case 'dead': return 'red';
            default: return 'gray';
        }
    };

    const handleSort = (field: string) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('asc');
        }
    };

    const deleteOpportunity = async (id: string) => {
        if (!confirm('Are you sure you want to delete this opportunity?')) return;
        
        try {
            await api.delete(`/crm/opportunities/${id}`);
            await fetchOpportunities();
        } catch (error) {
            console.error('Error deleting opportunity:', error);
            alert('Failed to delete opportunity. Please try again.');
        }
    };

    return (
        <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <Box style={{ padding: '2rem', borderBottom: '1px solid var(--gray-4)' }}>
                <Flex justify="between" align="center">
                    <Box>
                        <Heading size="8" mb="2">nBrain Sales Pipeline</Heading>
                        <Text color="gray">Manage your opportunities and track agent assignments</Text>
                    </Box>
                    <Button size="3" onClick={() => setShowCreateDialog(true)}>
                        <PlusIcon />
                        New Opportunity
                    </Button>
                </Flex>
            </Box>

            <Box style={{ flex: 1, overflow: 'auto', padding: '2rem' }}>
                <Card>
                    {/* Search and Filters */}
                    <Flex direction="column" gap="3" mb="4">
                        <Flex gap="3" align="end">
                            <Box style={{ flex: 2 }}>
                                <TextField.Root
                                    placeholder="Search opportunities, contacts, deal status..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    style={{ width: '100%' }}
                                >
                                    <TextField.Slot>
                                        <MagnifyingGlassIcon />
                                    </TextField.Slot>
                                </TextField.Root>
                            </Box>
                            
                            <Box style={{ flex: 1 }}>
                                <Text size="2" weight="bold" mb="1">Filter by Deal Status</Text>
                                <Select.Root value={dealStatusFilter} onValueChange={setDealStatusFilter}>
                                    <Select.Trigger style={{ width: '100%' }} />
                                    <Select.Content>
                                        <Select.Item value="all">All Deal Statuses</Select.Item>
                                        <Select.Separator />
                                        {LEAD_STATUS_OPTIONS.map(status => (
                                            <Select.Item key={status} value={status}>{status}</Select.Item>
                                        ))}
                                    </Select.Content>
                                </Select.Root>
                            </Box>
                        </Flex>
                    </Flex>

                    {/* Opportunities Table */}
                    <Box style={{ overflowX: 'auto' }}>
                        <Table.Root>
                            <Table.Header>
                                <Table.Row>
                                    <Table.ColumnHeaderCell width="40px"></Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell 
                                        onClick={() => handleSort('deal_status')}
                                        style={{ cursor: 'pointer', userSelect: 'none' }}
                                    >
                                        <Flex align="center" gap="1">
                                            Deal Status
                                            <CaretSortIcon />
                                        </Flex>
                                    </Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell 
                                        onClick={() => handleSort('client_opportunity')}
                                        style={{ cursor: 'pointer', userSelect: 'none' }}
                                    >
                                        <Flex align="center" gap="1">
                                            Company
                                            <CaretSortIcon />
                                        </Flex>
                                    </Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell 
                                        onClick={() => handleSort('contact_name')}
                                        style={{ cursor: 'pointer', userSelect: 'none' }}
                                    >
                                        <Flex align="center" gap="1">
                                            Contact
                                            <CaretSortIcon />
                                        </Flex>
                                    </Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell>Lead Source</Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell 
                                        onClick={() => handleSort('lead_start_date')}
                                        style={{ cursor: 'pointer', userSelect: 'none' }}
                                    >
                                        <Flex align="center" gap="1">
                                            Lead Date
                                            <CaretSortIcon />
                                        </Flex>
                                    </Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell width="80px">Actions</Table.ColumnHeaderCell>
                                </Table.Row>
                            </Table.Header>
                            <Table.Body>
                                {filteredOpportunities.map((opportunity, index) => (
                                    <>
                                        <Table.Row 
                                            key={opportunity.id}
                                            style={{ 
                                                backgroundColor: expandedRows.has(opportunity.id) ? 'var(--gray-2)' : 'transparent'
                                            }}
                                        >
                                            <Table.Cell>
                                                <IconButton
                                                    variant="ghost"
                                                    size="1"
                                                    onClick={() => toggleRowExpansion(opportunity.id)}
                                                >
                                                    {expandedRows.has(opportunity.id) ? 
                                                        <ChevronDownIcon /> : <ChevronRightIcon />
                                                    }
                                                </IconButton>
                                            </Table.Cell>
                                            <Table.Cell>
                                                <Badge color={getDealStatusColor(opportunity.deal_status)}>
                                                    {opportunity.deal_status || '-'}
                                                </Badge>
                                            </Table.Cell>
                                            <Table.Cell>
                                                <Text weight="bold">{opportunity.client_opportunity}</Text>
                                            </Table.Cell>
                                            <Table.Cell>
                                                <Text>{opportunity.contact_name || '-'}</Text>
                                            </Table.Cell>
                                            <Table.Cell>
                                                <Badge color={getStatusColor(opportunity.lead_source || '')}>
                                                    {opportunity.lead_source || '-'}
                                                </Badge>
                                            </Table.Cell>
                                            <Table.Cell>
                                                {opportunity.lead_start_date || '-'}
                                            </Table.Cell>
                                            <Table.Cell>
                                                <IconButton
                                                    size="1"
                                                    variant="ghost"
                                                    color="red"
                                                    onClick={() => deleteOpportunity(opportunity.id)}
                                                >
                                                    <TrashIcon />
                                                </IconButton>
                                            </Table.Cell>
                                        </Table.Row>
                                        {expandedRows.has(opportunity.id) && (
                                            <Table.Row>
                                                <Table.Cell colSpan={7} style={{ padding: 0 }}>
                                                    <Box style={{ 
                                                        backgroundColor: 'var(--gray-3)', 
                                                        borderRadius: '0 0 8px 8px',
                                                        border: '1px solid var(--gray-5)',
                                                        borderTop: 'none',
                                                        marginBottom: '16px'
                                                    }}>
                                                        <OpportunityDetails 
                                                            opportunity={opportunity}
                                                            onUpdate={fetchOpportunities}
                                                            editingField={editingField}
                                                            setEditingField={setEditingField}
                                                            editValue={editValue}
                                                            setEditValue={setEditValue}
                                                        />
                                                    </Box>
                                                </Table.Cell>
                                            </Table.Row>
                                        )}
                                    </>
                                ))}
                            </Table.Body>
                        </Table.Root>
                    </Box>
                </Card>
            </Box>

            {/* Create Dialog */}
            <Dialog.Root open={showCreateDialog} onOpenChange={(open) => {
                setShowCreateDialog(open);
                if (!open) {
                    // Reset form when closing
                    setCreateFormData({
                        company_name: '',           // Company Name
                        lead_status: 'New Lead',    // Lead Status
                        primary_contact_name: '',   // Primary Contact Name
                        primary_contact_email: '',  // Primary Contact Email
                        primary_contact_phone: '',  // Primary Contact Phone
                        job_title: '',             // Job Title
                        company_address: '',       // Company Address
                        linkedin_profile: '',      // LinkedIn Profile
                        website: '',              // Website
                        lead_source: 'Network',   // Lead Source
                        referral_source: '',      // Referral Source
                        lead_created_date: new Date().toISOString().split('T')[0]  // Lead Created Date
                    });
                }
            }}>
                <Dialog.Content style={{ maxWidth: '600px' }}>
                    <Dialog.Title>Create New Opportunity</Dialog.Title>
                    <Dialog.Description>
                        Add a new opportunity to your sales pipeline
                    </Dialog.Description>

                    <form onSubmit={async (e) => {
                        e.preventDefault();
                        
                        // Validate required fields
                        if (!createFormData.company_name || !createFormData.primary_contact_name || !createFormData.primary_contact_email) {
                            alert('Please fill in all required fields: Company Name, Primary Contact Name, and Primary Contact Email');
                            return;
                        }
                        
                        try {
                            // Map the form data to the API format
                            const apiData = {
                                status: 'Active',  // All new opportunities start as Active
                                client_opportunity: createFormData.company_name,
                                lead_status: createFormData.lead_status,
                                contact_name: createFormData.primary_contact_name,
                                contact_email: createFormData.primary_contact_email,
                                contact_phone: createFormData.primary_contact_phone,
                                job_title: createFormData.job_title,
                                company_address: createFormData.company_address,
                                linkedin_profile: createFormData.linkedin_profile,
                                website_url: createFormData.website,
                                lead_source: createFormData.lead_source,
                                referral_source: createFormData.referral_source,
                                lead_start_date: createFormData.lead_created_date,
                                deal_status: createFormData.lead_status // Map lead_status to deal_status for now
                            };
                            
                            await api.post('/crm/opportunities', apiData);
                            
                            await fetchOpportunities();
                            setShowCreateDialog(false);
                        } catch (error) {
                            console.error('Error creating opportunity:', error);
                            alert('Failed to create opportunity. Please try again.');
                        }
                    }}>
                        <Flex direction="column" gap="3" mt="4">
                            {/* Company Name */}
                            <Box>
                                <Text size="2" weight="bold" mb="1">Company Name *</Text>
                                <TextField.Root 
                                    value={createFormData.company_name}
                                    onChange={(e) => setCreateFormData({...createFormData, company_name: e.target.value})}
                                    required 
                                />
                            </Box>

                            {/* Lead Status */}
                            <Box>
                                <Text size="2" weight="bold" mb="1">Lead Status *</Text>
                                <Select.Root 
                                    value={createFormData.lead_status} 
                                    onValueChange={(value) => setCreateFormData({...createFormData, lead_status: value})}
                                >
                                    <Select.Trigger style={{ width: '100%' }} />
                                    <Select.Content>
                                        {LEAD_STATUS_OPTIONS.map(status => (
                                            <Select.Item key={status} value={status}>{status}</Select.Item>
                                        ))}
                                    </Select.Content>
                                </Select.Root>
                            </Box>

                            {/* Primary Contact Name and Email */}
                            <Grid columns="2" gap="3">
                                <Box>
                                    <Text size="2" weight="bold" mb="1">Primary Contact Name *</Text>
                                    <TextField.Root 
                                        value={createFormData.primary_contact_name}
                                        onChange={(e) => setCreateFormData({...createFormData, primary_contact_name: e.target.value})}
                                        required 
                                    />
                                </Box>

                                <Box>
                                    <Text size="2" weight="bold" mb="1">Primary Contact Email *</Text>
                                    <TextField.Root 
                                        type="email"
                                        value={createFormData.primary_contact_email}
                                        onChange={(e) => setCreateFormData({...createFormData, primary_contact_email: e.target.value})}
                                        required 
                                    />
                                </Box>
                            </Grid>

                            {/* Phone and Job Title */}
                            <Grid columns="2" gap="3">
                                <Box>
                                    <Text size="2" weight="bold" mb="1">Primary Contact Phone</Text>
                                    <TextField.Root 
                                        type="tel"
                                        value={createFormData.primary_contact_phone}
                                        onChange={(e) => setCreateFormData({...createFormData, primary_contact_phone: e.target.value})}
                                        placeholder="(123) 456-7890"
                                    />
                                </Box>

                                <Box>
                                    <Text size="2" weight="bold" mb="1">Job Title</Text>
                                    <TextField.Root 
                                        value={createFormData.job_title}
                                        onChange={(e) => setCreateFormData({...createFormData, job_title: e.target.value})}
                                        placeholder="CEO, CTO, etc."
                                    />
                                </Box>
                            </Grid>

                            {/* Company Address */}
                            <Box>
                                <Text size="2" weight="bold" mb="1">Company Address</Text>
                                <TextField.Root 
                                    value={createFormData.company_address}
                                    onChange={(e) => setCreateFormData({...createFormData, company_address: e.target.value})}
                                    placeholder="123 Main St, City, State, ZIP"
                                />
                            </Box>

                            {/* LinkedIn and Website */}
                            <Grid columns="2" gap="3">
                                <Box>
                                    <Text size="2" weight="bold" mb="1">LinkedIn Profile</Text>
                                    <TextField.Root 
                                        type="url"
                                        value={createFormData.linkedin_profile}
                                        onChange={(e) => setCreateFormData({...createFormData, linkedin_profile: e.target.value})}
                                        placeholder="https://linkedin.com/in/..."
                                    />
                                </Box>

                                <Box>
                                    <Text size="2" weight="bold" mb="1">Website</Text>
                                    <TextField.Root 
                                        type="url"
                                        value={createFormData.website}
                                        onChange={(e) => setCreateFormData({...createFormData, website: e.target.value})}
                                        placeholder="https://company.com"
                                    />
                                </Box>
                            </Grid>

                            {/* Lead Source and Referral Source */}
                            <Grid columns="2" gap="3">
                                <Box>
                                    <Text size="2" weight="bold" mb="1">Lead Source *</Text>
                                    <Select.Root 
                                        value={createFormData.lead_source} 
                                        onValueChange={(value) => setCreateFormData({...createFormData, lead_source: value})}
                                    >
                                        <Select.Trigger style={{ width: '100%' }} />
                                        <Select.Content>
                                            {LEAD_SOURCE_OPTIONS.map(source => (
                                                <Select.Item key={source} value={source}>{source}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                </Box>

                                <Box>
                                    <Text size="2" weight="bold" mb="1">Referral Source</Text>
                                    {createFormData.lead_source === 'Referral Partner' ? (
                                        <Select.Root 
                                            value={createFormData.referral_source} 
                                            onValueChange={(value) => setCreateFormData({...createFormData, referral_source: value})}
                                        >
                                            <Select.Trigger style={{ width: '100%' }} />
                                            <Select.Content>
                                                <Select.Item value="">Select Partner</Select.Item>
                                                <Select.Separator />
                                                {REFERRAL_PARTNER_OPTIONS.map(partner => (
                                                    <Select.Item key={partner} value={partner}>{partner}</Select.Item>
                                                ))}
                                            </Select.Content>
                                        </Select.Root>
                                    ) : (
                                        <TextField.Root 
                                            value={createFormData.referral_source}
                                            onChange={(e) => setCreateFormData({...createFormData, referral_source: e.target.value})}
                                            placeholder="Enter referral source"
                                            disabled={createFormData.lead_source !== 'Referral Partner'}
                                        />
                                    )}
                                </Box>
                            </Grid>

                            {/* Lead Created Date */}
                            <Box>
                                <Text size="2" weight="bold" mb="1">Lead Created Date</Text>
                                <TextField.Root 
                                    type="date"
                                    value={createFormData.lead_created_date}
                                    onChange={(e) => setCreateFormData({...createFormData, lead_created_date: e.target.value})}
                                />
                            </Box>
                        </Flex>

                        <Flex gap="3" mt="4" justify="end">
                            <Dialog.Close>
                                <Button variant="soft" color="gray">Cancel</Button>
                            </Dialog.Close>
                            <Button type="submit">Create Opportunity</Button>
                        </Flex>
                    </form>
                </Dialog.Content>
            </Dialog.Root>
        </Box>
    );
};

// Opportunity Details Component
const OpportunityDetails = ({ 
    opportunity, 
    onUpdate, 
    editingField, 
    setEditingField, 
    editValue, 
    setEditValue 
}: { 
    opportunity: CRMOpportunity; 
    onUpdate: () => void;
    editingField: { id: string; field: string } | null;
    setEditingField: React.Dispatch<React.SetStateAction<{ id: string; field: string } | null>>;
    editValue: string;
    setEditValue: React.Dispatch<React.SetStateAction<string>>;
}) => {
    const navigate = useNavigate();
    const isEditing = (field: string) => editingField?.id === opportunity.id && editingField?.field === field;

    const startEdit = (field: string, value: string) => {
        setEditingField({ id: opportunity.id, field });
        setEditValue(value || '');
    };

    const cancelEdit = () => {
        setEditingField(null);
        setEditValue('');
    };

    const saveEdit = async () => {
        if (!editingField) return;

        try {
            await api.put(`/crm/opportunities/${opportunity.id}`, {
                [editingField.field]: editValue
            });
            await onUpdate();
            cancelEdit();
        } catch (error) {
            console.error('Error updating opportunity:', error);
        }
    };

    const convertToClient = async () => {
        try {
            const response = await api.post(`/crm/opportunities/${opportunity.id}/convert-to-client`);
            alert(response.data.message);
            await onUpdate();
        } catch (error: any) {
            console.error('Error converting to client:', error);
            alert(error.response?.data?.detail || 'Failed to convert to client');
        }
    };

    const EditableField = ({ field, label, value, inputType = 'text' }: { field: string; label: string; value?: string; inputType?: string }) => {
        const isEditingThis = isEditing(field);

        return (
            <Box style={{ 
                padding: '12px',
                backgroundColor: 'var(--gray-1)',
                borderRadius: '6px',
                border: '1px solid var(--gray-4)',
                minHeight: '60px'
            }}>
                <Flex justify="between" align="start">
                    <Box style={{ flex: 1 }}>
                        <Text size="2" weight="bold" color="gray" style={{ display: 'block', marginBottom: '4px' }}>
                            {label}
                        </Text>
                        {isEditingThis ? (
                            <Flex gap="2" align="center">
                                {field === 'lead_source' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {LEAD_SOURCE_OPTIONS.map(source => (
                                                <Select.Item key={source} value={source}>{source}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : field === 'deal_status' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {LEAD_STATUS_OPTIONS.map(status => (
                                                <Select.Item key={status} value={status}>{status}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : field === 'opportunity_type' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {OPPORTUNITY_TYPE_OPTIONS.map(type => (
                                                <Select.Item key={type} value={type}>{type}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : field === 'sales_pipeline' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {SALES_PIPELINE_OPTIONS.map(pipeline => (
                                                <Select.Item key={pipeline} value={pipeline}>{pipeline}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : field === 'stage' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {STAGE_OPTIONS.map(stage => (
                                                <Select.Item key={stage} value={stage}>{stage}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : field === 'engagement_type' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {ENGAGEMENT_TYPE_OPTIONS.map(type => (
                                                <Select.Item key={type} value={type}>{type}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : field === 'win_likelihood' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {WIN_LIKELIHOOD_OPTIONS.map(option => (
                                                <Select.Item key={option.value} value={option.value}>{option.label}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : field === 'forecast_category' ? (
                                    <Select.Root value={editValue} onValueChange={setEditValue}>
                                        <Select.Trigger style={{ flex: 1 }} />
                                        <Select.Content>
                                            {FORECAST_CATEGORY_OPTIONS.map(category => (
                                                <Select.Item key={category} value={category}>{category}</Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                ) : (
                                    <TextField.Root
                                        value={editValue}
                                        onChange={(e) => setEditValue(e.target.value)}
                                        style={{ flex: 1 }}
                                        autoFocus
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') saveEdit();
                                            if (e.key === 'Escape') cancelEdit();
                                        }}
                                        type={inputType as any}
                                    />
                                )}
                                <IconButton size="1" onClick={saveEdit}>
                                    <CheckIcon />
                                </IconButton>
                                <IconButton size="1" variant="soft" onClick={cancelEdit}>
                                    <Cross2Icon />
                                </IconButton>
                            </Flex>
                        ) : (
                            <Flex justify="between" align="center">
                                <Text size="3" style={{ lineHeight: '1.5' }}>
                                    {field === 'win_likelihood' && value ? 
                                        WIN_LIKELIHOOD_OPTIONS.find(opt => opt.value === value)?.label || value :
                                        value || '-'
                                    }
                                </Text>
                                <IconButton 
                                    size="1" 
                                    variant="ghost" 
                                    onClick={() => startEdit(field, value || '')}
                                    style={{ opacity: 0.6 }}
                                >
                                    <Pencil1Icon />
                                </IconButton>
                            </Flex>
                        )}
                    </Box>
                </Flex>
            </Box>
        );
    };

    return (
        <Box p="5">
            <Tabs.Root defaultValue="details">
                <Tabs.List style={{ marginBottom: '20px' }}>
                    <Tabs.Trigger value="details">Details</Tabs.Trigger>
                    <Tabs.Trigger value="documents">Documents ({opportunity.documents.length})</Tabs.Trigger>
                    <Tabs.Trigger value="agents">Linked Agents ({opportunity.agent_links.length})</Tabs.Trigger>
                </Tabs.List>

                <Box>
                    <Tabs.Content value="details">
                        {/* Show client portal link if status is Closed */}
                        {opportunity.deal_status === 'Closed' && (
                            <Box mb="4" p="3" style={{ 
                                backgroundColor: 'var(--green-3)', 
                                borderRadius: '8px',
                                border: '1px solid var(--green-6)'
                            }}>
                                <Flex align="center" justify="between">
                                    <Flex align="center" gap="2">
                                        <PersonIcon />
                                        <Text weight="bold">Ready for Client Portal</Text>
                                    </Flex>
                                    <Flex gap="2">
                                        <Button 
                                            size="2" 
                                            variant="solid"
                                            onClick={convertToClient}
                                        >
                                            Convert to Client
                                        </Button>
                                        <Button 
                                            size="2" 
                                            variant="soft"
                                            onClick={() => navigate('/clients')}
                                        >
                                            View Client Portal
                                        </Button>
                                    </Flex>
                                </Flex>
                                <Text size="2" color="gray" mt="1">
                                    This closed opportunity can be converted to a client for project management, tasks, and communications.
                                </Text>
                            </Box>
                        )}
                        
                        {/* Core Opportunity Info */}
                        <Heading size="3" mb="3">Opportunity Information</Heading>
                        <Grid columns={{ initial: '1', md: '2', lg: '3' }} gap="3" mb="4">
                            <EditableField field="opportunity_type" label="Opportunity" value={opportunity.opportunity_type} />
                            <EditableField field="customer_name" label="Customer" value={opportunity.client_opportunity} />
                            <EditableField field="owner" label="Owner" value={opportunity.owner} />
                            <EditableField field="sales_pipeline" label="Sales Pipeline" value={opportunity.sales_pipeline} />
                            <EditableField field="stage" label="Stage" value={opportunity.stage} />
                            <EditableField field="est_close_date" label="Est. Close Date" value={opportunity.est_close_date} inputType="date" />
                            <EditableField field="close_date" label="Close Date" value={opportunity.close_date} inputType="date" />
                            <EditableField field="value" label="Value ($)" value={opportunity.actual_contract_value} />
                            <EditableField field="engagement_type" label="Engagement" value={opportunity.engagement_type} />
                            <EditableField field="win_likelihood" label="Win Likelihood" value={opportunity.win_likelihood} />
                            <EditableField field="forecast_category" label="Forecast Category" value={opportunity.forecast_category} />
                        </Grid>

                        <Separator size="4" my="4" />
                        
                        {/* Contact Information */}
                        <Heading size="3" mb="3">Contact Information</Heading>
                        <Grid columns={{ initial: '1', md: '2', lg: '3' }} gap="3" mb="4">
                            <EditableField field="contact_name" label="Primary Contact Name" value={opportunity.contact_name} />
                            <EditableField field="contact_email" label="Primary Contact Email" value={opportunity.contact_email} />
                            <EditableField field="contact_phone" label="Primary Contact Phone" value={opportunity.contact_phone} />
                            <EditableField field="job_title" label="Job Title" value={opportunity.job_title} />
                            <EditableField field="linkedin_profile" label="LinkedIn Profile" value={opportunity.linkedin_profile} />
                            <EditableField field="website_url" label="Website" value={opportunity.website_url} />
                        </Grid>

                        <Separator size="4" my="4" />
                        
                        {/* Lead Information */}
                        <Heading size="3" mb="3">Lead Information</Heading>
                        <Grid columns={{ initial: '1', md: '2', lg: '3' }} gap="3" mb="4">
                            <EditableField field="lead_status" label="Lead Status" value={opportunity.lead_status} />
                            <EditableField field="lead_source" label="Lead Source" value={opportunity.lead_source} />
                            <EditableField field="referral_source" label="Referral Source" value={opportunity.referral_source} />
                            <EditableField field="lead_start_date" label="Lead Created Date" value={opportunity.lead_start_date} inputType="date" />
                        </Grid>

                        <Separator size="4" my="4" />
                        
                        {/* Additional Details */}
                        <Heading size="3" mb="3">Additional Details</Heading>
                        <Grid columns={{ initial: '1', md: '2', lg: '3' }} gap="3" mb="4">
                            <EditableField field="company_address" label="Company Address" value={opportunity.company_address} />
                            <EditableField field="monthly_fees" label="Monthly Fees" value={opportunity.monthly_fees} />
                            <EditableField field="product" label="Product" value={opportunity.product} />
                        </Grid>
                        
                        <Box mt="4">
                            <Grid columns="1" gap="3">
                                <Box style={{ 
                                    padding: '16px',
                                    backgroundColor: 'var(--gray-1)',
                                    borderRadius: '6px',
                                    border: '1px solid var(--gray-4)'
                                }}>
                                    <Text size="2" weight="bold" color="gray" style={{ display: 'block', marginBottom: '8px' }}>
                                        Next Steps / Notes
                                    </Text>
                                    {isEditing('todo_next_steps') ? (
                                        <Flex gap="2">
                                            <TextField.Root
                                                value={editValue}
                                                onChange={(e) => setEditValue(e.target.value)}
                                                style={{ flex: 1 }}
                                                autoFocus
                                            />
                                            <IconButton size="1" onClick={saveEdit}>
                                                <CheckIcon />
                                            </IconButton>
                                            <IconButton size="1" variant="soft" onClick={cancelEdit}>
                                                <Cross2Icon />
                                            </IconButton>
                                        </Flex>
                                    ) : (
                                        <Flex justify="between" align="start">
                                            <Text size="3" style={{ flex: 1, whiteSpace: 'pre-wrap' }}>
                                                {opportunity.todo_next_steps || 'No notes yet'}
                                            </Text>
                                            <IconButton 
                                                size="1" 
                                                variant="ghost" 
                                                onClick={() => startEdit('todo_next_steps', opportunity.todo_next_steps || '')}
                                                style={{ opacity: 0.6, marginLeft: '8px' }}
                                            >
                                                <Pencil1Icon />
                                            </IconButton>
                                        </Flex>
                                    )}
                                </Box>
                            </Grid>
                        </Box>
                    </Tabs.Content>

                    <Tabs.Content value="documents">
                        <Box style={{ 
                            padding: '24px',
                            backgroundColor: 'var(--gray-1)',
                            borderRadius: '6px',
                            border: '1px solid var(--gray-4)',
                            textAlign: 'center'
                        }}>
                            <Text size="2" color="gray">Document management coming soon...</Text>
                        </Box>
                    </Tabs.Content>

                    <Tabs.Content value="agents">
                        <AgentLinkManager 
                            opportunity={opportunity}
                            onUpdate={onUpdate}
                        />
                    </Tabs.Content>
                </Box>
            </Tabs.Root>
        </Box>
    );
};

// Agent Link Manager Component
const AgentLinkManager = ({ opportunity, onUpdate }: { opportunity: CRMOpportunity; onUpdate: () => void }) => {
    const [availableAgents, setAvailableAgents] = useState<AgentIdea[]>([]);
    const [showLinkDialog, setShowLinkDialog] = useState(false);
    const [selectedAgentId, setSelectedAgentId] = useState('');
    const [linkNotes, setLinkNotes] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchAvailableAgents();
    }, []);

    const fetchAvailableAgents = async () => {
        try {
            const response = await api.get('/agent-ideas');
            setAvailableAgents(response.data);
        } catch (error) {
            console.error('Error fetching agents:', error);
        }
    };

    const linkAgent = async () => {
        if (!selectedAgentId) return;

        setLoading(true);
        try {
            await api.post(`/crm/opportunities/${opportunity.id}/agent-links`, {
                agent_idea_id: selectedAgentId,
                notes: linkNotes
            });
            await onUpdate();
            setShowLinkDialog(false);
            setSelectedAgentId('');
            setLinkNotes('');
        } catch (error) {
            console.error('Error linking agent:', error);
            alert('Failed to link agent. It may already be linked to this opportunity.');
        } finally {
            setLoading(false);
        }
    };

    const unlinkAgent = async (linkId: string) => {
        if (!confirm('Are you sure you want to remove this agent link?')) return;

        try {
            await api.delete(`/crm/opportunities/${opportunity.id}/agent-links/${linkId}`);
            await onUpdate();
        } catch (error) {
            console.error('Error unlinking agent:', error);
        }
    };

    const getAgentTypeIcon = (type?: string) => {
        switch (type) {
            case 'customer_service': return '🎧';
            case 'data_analysis': return '📊';
            case 'content_creation': return '✍️';
            case 'process_automation': return '⚙️';
            default: return '🤖';
        }
    };

    return (
        <Box>
            {/* Linked Agents List */}
            {opportunity.agent_links.length > 0 ? (
                <Grid columns={{ initial: '1', md: '2' }} gap="3">
                    {opportunity.agent_links.map((link: any) => (
                        <Card key={link.id} style={{ position: 'relative' }}>
                            <IconButton
                                size="1"
                                variant="ghost"
                                style={{ position: 'absolute', top: '8px', right: '8px' }}
                                onClick={() => unlinkAgent(link.id)}
                            >
                                <Cross2Icon />
                            </IconButton>
                            <Flex gap="3" align="start">
                                <Text size="5">{getAgentTypeIcon(link.agent_type)}</Text>
                                <Box style={{ flex: 1 }}>
                                    <Text weight="bold" size="3">{link.agent_title || 'Unknown Agent'}</Text>
                                    <Text size="2" color="gray" style={{ display: 'block', marginTop: '4px' }}>
                                        Linked on {new Date(link.linked_at).toLocaleDateString()}
                                    </Text>
                                    {link.notes && (
                                        <Text size="2" style={{ display: 'block', marginTop: '8px' }}>
                                            {link.notes}
                                        </Text>
                                    )}
                                </Box>
                            </Flex>
                        </Card>
                    ))}
                </Grid>
            ) : (
                <Box style={{ 
                    padding: '24px',
                    backgroundColor: 'var(--gray-1)',
                    borderRadius: '6px',
                    border: '1px solid var(--gray-4)',
                    textAlign: 'center'
                }}>
                    <Text size="2" color="gray">No agents linked to this opportunity yet</Text>
                </Box>
            )}

            {/* Add Agent Button */}
            <Flex justify="center" mt="4">
                <Button onClick={() => setShowLinkDialog(true)}>
                    <Link2Icon />
                    Link Agent
                </Button>
            </Flex>

            {/* Link Agent Dialog */}
            <Dialog.Root open={showLinkDialog} onOpenChange={setShowLinkDialog}>
                <Dialog.Content style={{ maxWidth: '500px' }}>
                    <Dialog.Title>Link AI Agent to Opportunity</Dialog.Title>
                    <Dialog.Description>
                        Select an AI agent to link to {opportunity.client_opportunity}
                    </Dialog.Description>

                    <Flex direction="column" gap="3" mt="4">
                        <Box>
                            <Text size="2" weight="bold" style={{ display: 'block', marginBottom: '8px' }}>
                                Available Agents
                            </Text>
                            <ScrollArea style={{ height: '200px' }}>
                                <Flex direction="column" gap="2">
                                    {availableAgents
                                        .filter(agent => !opportunity.agent_links.some((link: any) => link.agent_idea_id === agent.id))
                                        .map(agent => (
                                            <Card
                                                key={agent.id}
                                                style={{
                                                    cursor: 'pointer',
                                                    backgroundColor: selectedAgentId === agent.id ? 'var(--accent-3)' : 'transparent',
                                                    border: selectedAgentId === agent.id ? '2px solid var(--accent-9)' : '1px solid var(--gray-6)'
                                                }}
                                                onClick={() => setSelectedAgentId(agent.id)}
                                            >
                                                <Flex gap="2" align="center">
                                                    <Text>{getAgentTypeIcon(agent.agent_type)}</Text>
                                                    <Box style={{ flex: 1 }}>
                                                        <Text weight="bold">{agent.title}</Text>
                                                        <Text size="1" color="gray">{agent.summary.substring(0, 100)}...</Text>
                                                    </Box>
                                                </Flex>
                                            </Card>
                                        ))}
                                </Flex>
                            </ScrollArea>
                        </Box>

                        <Box>
                            <Text size="2" weight="bold" style={{ display: 'block', marginBottom: '8px' }}>
                                Notes (optional)
                            </Text>
                            <TextField.Root
                                placeholder="Add notes about this agent assignment..."
                                value={linkNotes}
                                onChange={(e) => setLinkNotes(e.target.value)}
                            />
                        </Box>
                    </Flex>

                    <Flex gap="3" mt="4" justify="end">
                        <Dialog.Close>
                            <Button variant="soft" color="gray">Cancel</Button>
                        </Dialog.Close>
                        <Button 
                            onClick={linkAgent} 
                            disabled={!selectedAgentId || loading}
                        >
                            {loading ? 'Linking...' : 'Link Agent'}
                        </Button>
                    </Flex>
                </Dialog.Content>
            </Dialog.Root>
        </Box>
    );
};

export default CRMPage; 