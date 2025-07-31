import React, { useState } from 'react';
import { Box, Heading, Text, Card, Flex, Button, TextField, TextArea } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon } from '@radix-ui/react-icons';
import api from '../api';

const NewClient = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    company_website: '',
    industry: '',
    project_value: '',
    estimated_end_date: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.primary_contact_email) {
      alert('Please fill in required fields');
      return;
    }

    setIsSubmitting(true);
    try {
      const submitData = {
        ...formData,
        project_value: formData.project_value ? parseFloat(formData.project_value) : null,
        estimated_end_date: formData.estimated_end_date || null
      };
      
      const response = await api.post('/clients', submitData);
      navigate(`/client/${response.data.id}`);
    } catch (error) {
      console.error('Error creating client:', error);
      alert('Failed to create client');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <Flex align="center" gap="3">
          <Button
            variant="ghost"
            onClick={() => navigate('/clients')}
          >
            <ArrowLeftIcon /> Back to Clients
          </Button>
        </Flex>
      </div>

      <div className="page-content">
        <Card style={{ maxWidth: '600px', margin: '0 auto' }}>
          <form onSubmit={handleSubmit}>
            <Heading size="5" mb="4">Create New Client</Heading>
            
            <Flex direction="column" gap="4">
              <Box>
                <Text size="2" weight="medium" mb="1">
                  Company Name <Text color="red">*</Text>
                </Text>
                <TextField.Root
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter company name"
                  required
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="1">
                  Primary Contact Name
                </Text>
                <TextField.Root
                  name="primary_contact_name"
                  value={formData.primary_contact_name}
                  onChange={handleChange}
                  placeholder="John Doe"
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="1">
                  Primary Contact Email <Text color="red">*</Text>
                </Text>
                <TextField.Root
                  name="primary_contact_email"
                  type="email"
                  value={formData.primary_contact_email}
                  onChange={handleChange}
                  placeholder="john@company.com"
                  required
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="1">
                  Phone Number
                </Text>
                <TextField.Root
                  name="primary_contact_phone"
                  value={formData.primary_contact_phone}
                  onChange={handleChange}
                  placeholder="+1 (555) 123-4567"
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="1">
                  Company Website
                </Text>
                <TextField.Root
                  name="company_website"
                  value={formData.company_website}
                  onChange={handleChange}
                  placeholder="https://company.com"
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="1">
                  Industry
                </Text>
                <TextField.Root
                  name="industry"
                  value={formData.industry}
                  onChange={handleChange}
                  placeholder="Technology, Finance, etc."
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="1">
                  Project Value
                </Text>
                <TextField.Root
                  name="project_value"
                  type="number"
                  value={formData.project_value}
                  onChange={handleChange}
                  placeholder="50000"
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="1">
                  Estimated End Date
                </Text>
                <TextField.Root
                  name="estimated_end_date"
                  type="date"
                  value={formData.estimated_end_date}
                  onChange={handleChange}
                />
              </Box>

              <Flex gap="3" mt="4">
                <Button
                  type="button"
                  variant="soft"
                  onClick={() => navigate('/clients')}
                  style={{ flex: 1 }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  style={{ flex: 1 }}
                >
                  {isSubmitting ? 'Creating...' : 'Create Client'}
                </Button>
              </Flex>
            </Flex>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default NewClient; 