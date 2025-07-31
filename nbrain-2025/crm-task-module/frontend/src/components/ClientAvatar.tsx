import React, { useState, useEffect } from 'react';
import { Avatar } from '@radix-ui/themes';

interface ClientAvatarProps {
  name: string;
  domain?: string;
  website?: string;
  size?: '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9';
  color?: string;
}

const ClientAvatar: React.FC<ClientAvatarProps> = ({ 
  name, 
  domain, 
  website,
  size = '3',
  color = 'blue'
}) => {
  const [faviconUrl, setFaviconUrl] = useState<string | null>(null);
  const [faviconError, setFaviconError] = useState(false);

  useEffect(() => {
    // Try to get favicon URL from domain or website
    let faviconDomain = domain;
    
    if (!faviconDomain && website) {
      // Extract domain from website URL
      faviconDomain = website
        .replace('https://', '')
        .replace('http://', '')
        .replace('www.', '')
        .split('/')[0];
    }

    if (faviconDomain) {
      // Try multiple favicon sources
      const faviconUrls = [
        `https://${faviconDomain}/favicon.ico`,
        `https://www.google.com/s2/favicons?domain=${faviconDomain}&sz=64`,
        `https://favicon.ico.la/${faviconDomain}`
      ];
      
      // Use Google's favicon service as it's more reliable
      setFaviconUrl(faviconUrls[1]);
      setFaviconError(false);
    }
  }, [domain, website]);

  const handleFaviconError = () => {
    setFaviconError(true);
  };

  if (faviconUrl && !faviconError) {
    return (
      <Avatar
        size={size}
        src={faviconUrl}
        fallback={name.charAt(0).toUpperCase()}
        color={color as any}
        variant="solid"
        onError={handleFaviconError}
        style={{ backgroundColor: 'var(--gray-3)' }}
      />
    );
  }

  // Fallback to letter avatar
  return (
    <Avatar
      size={size}
      fallback={name.charAt(0).toUpperCase()}
      color={color as any}
      variant="solid"
    />
  );
};

export default ClientAvatar; 