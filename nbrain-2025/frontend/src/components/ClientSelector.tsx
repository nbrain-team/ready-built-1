import React, { useState, useEffect } from 'react';
import { Select } from '@radix-ui/themes';
import api from '../api';

interface Client {
  id: string;
  name: string;
}

interface ClientSelectorProps {
  selectedClientId: string | null;
  onClientChange: (clientId: string | null) => void;
}

const ClientSelector: React.FC<ClientSelectorProps> = ({ selectedClientId, onClientChange }) => {
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Select.Root value={selectedClientId || 'all'} onValueChange={(value) => onClientChange(value === 'all' ? null : value)}>
      <Select.Trigger placeholder="Select a client..." />
      <Select.Content>
        <Select.Group>
          <Select.Label>Search Context</Select.Label>
          <Select.Item value="all">All Documents</Select.Item>
        </Select.Group>
        {clients.length > 0 && (
          <Select.Group>
            <Select.Label>Clients</Select.Label>
            {clients.map((client) => (
              <Select.Item key={client.id} value={client.id}>
                {client.name}
              </Select.Item>
            ))}
          </Select.Group>
        )}
      </Select.Content>
    </Select.Root>
  );
};

export default ClientSelector; 