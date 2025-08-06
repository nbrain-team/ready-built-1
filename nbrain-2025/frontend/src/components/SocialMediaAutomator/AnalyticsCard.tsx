import React from 'react';
import { Box, Card, Flex, Text } from '@radix-ui/themes';
import { CheckCircledIcon, CrossCircledIcon, InfoCircledIcon } from '@radix-ui/react-icons';

interface AnalyticsData {
  emailEnrichmentRate: number;
  phoneEnrichmentRate: number;
  totalEmails: number;
  totalPhones: number;
  enrichedEmails: number;
  enrichedPhones: number;
}

interface AnalyticsCardProps {
  data: AnalyticsData;
}

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({ data }) => {
  // Calculate blended enrichment success rate
  const totalRecords = data.totalEmails + data.totalPhones;
  const totalEnriched = data.enrichedEmails + data.enrichedPhones;
  const blendedEnrichmentRate = totalRecords > 0 ? (totalEnriched / totalRecords) * 100 : 0;

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;

  return (
    <Card>
      <Flex direction="column" gap="4">
        <Flex align="center" justify="between">
          <Text size="4" weight="bold">Enrichment Analytics</Text>
          <InfoCircledIcon />
        </Flex>

        {/* Blended Enrichment Success Rate */}
        <Box style={{ 
          padding: '1rem', 
          backgroundColor: 'var(--accent-2)', 
          borderRadius: '8px',
          border: '1px solid var(--accent-6)'
        }}>
          <Flex direction="column" gap="2">
            <Text size="2" weight="medium" color="gray">
              Overall Enrichment Success Rate
            </Text>
            <Flex align="center" gap="3">
              <Text size="6" weight="bold" color="blue">
                {formatPercentage(blendedEnrichmentRate)}
              </Text>
              {blendedEnrichmentRate >= 70 ? (
                <CheckCircledIcon color="green" width="24" height="24" />
              ) : (
                <CrossCircledIcon color="orange" width="24" height="24" />
              )}
            </Flex>
            <div style={{ width: '100%', height: '8px', backgroundColor: '#e5e5e5', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${blendedEnrichmentRate}%`, height: '100%', backgroundColor: '#3b82f6', transition: 'width 0.3s' }} />
            </div>
            <Text size="1" color="gray">
              {totalEnriched} of {totalRecords} records enriched successfully
            </Text>
          </Flex>
        </Box>

        {/* Individual Metrics */}
        <Flex gap="4">
          {/* Email Enrichment */}
          <Box style={{ flex: 1 }}>
            <Card>
              <Flex direction="column" gap="3">
                <Flex align="center" justify="between">
                  <Text size="2" weight="medium">Email Enrichment</Text>
                  <Text size="2" weight="bold" color="blue">
                    {formatPercentage(data.emailEnrichmentRate)}
                  </Text>
                </Flex>
                <div style={{ width: '100%', height: '4px', backgroundColor: '#e5e5e5', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: `${data.emailEnrichmentRate}%`, height: '100%', backgroundColor: '#3b82f6', transition: 'width 0.3s' }} />
                </div>
                <Flex justify="between">
                  <Text size="1" color="gray">Total</Text>
                  <Text size="1">{data.totalEmails}</Text>
                </Flex>
                <Flex justify="between">
                  <Text size="1" color="gray">Enriched</Text>
                  <Text size="1" color="green">{data.enrichedEmails}</Text>
                </Flex>
                <Text size="1" color="gray">
                  {data.enrichedEmails} / {data.totalEmails} enriched
                </Text>
              </Flex>
            </Card>
          </Box>

          {/* Phone Enrichment */}
          <Box style={{ flex: 1 }}>
            <Card>
              <Flex direction="column" gap="3">
                <Flex align="center" justify="between">
                  <Text size="2" weight="medium">Phone Enrichment</Text>
                  <Text size="2" weight="bold" color="green">
                    {formatPercentage(data.phoneEnrichmentRate)}
                  </Text>
                </Flex>
                <div style={{ width: '100%', height: '4px', backgroundColor: '#e5e5e5', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: `${data.phoneEnrichmentRate}%`, height: '100%', backgroundColor: '#10b981', transition: 'width 0.3s' }} />
                </div>
                <Flex justify="between">
                  <Text size="1" color="gray">Total</Text>
                  <Text size="1">{data.totalPhones}</Text>
                </Flex>
                <Flex justify="between">
                  <Text size="1" color="gray">Enriched</Text>
                  <Text size="1" color="green">{data.enrichedPhones}</Text>
                </Flex>
                <Text size="1" color="gray">
                  {data.enrichedPhones} / {data.totalPhones} enriched
                </Text>
              </Flex>
            </Card>
          </Box>
        </Flex>

        {/* Success Indicators */}
        <Card variant="surface">
          <Flex direction="column" gap="2">
            <Text size="2" weight="medium">Performance Indicators</Text>
            <Flex direction="column" gap="1">
              {blendedEnrichmentRate >= 80 && (
                <Flex align="center" gap="2">
                  <CheckCircledIcon color="green" />
                  <Text size="1" color="green">Excellent enrichment rate</Text>
                </Flex>
              )}
              {blendedEnrichmentRate >= 60 && blendedEnrichmentRate < 80 && (
                <Flex align="center" gap="2">
                  <InfoCircledIcon color="blue" />
                  <Text size="1" color="blue">Good enrichment rate</Text>
                </Flex>
              )}
              {blendedEnrichmentRate < 60 && (
                <Flex align="center" gap="2">
                  <CrossCircledIcon color="orange" />
                  <Text size="1" color="orange">Enrichment rate needs improvement</Text>
                </Flex>
              )}
            </Flex>
          </Flex>
        </Card>
      </Flex>
    </Card>
  );
}; 