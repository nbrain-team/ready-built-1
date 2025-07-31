import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Flex, Text, Container, Button } from '@radix-ui/themes';
import { ExclamationTriangleIcon } from '@radix-ui/react-icons';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireAdmin?: boolean;
  requirePermission?: string;
}

export const ProtectedRoute = ({ 
  children, 
  requireAuth = true,
  requireAdmin = false,
  requirePermission
}: ProtectedRouteProps) => {
  const { isAuthenticated, userProfile, isAdmin, hasPermission, isLoading } = useAuth();

  // Show loading state
  if (isLoading) {
    return (
      <Flex align="center" justify="center" style={{ height: '100vh' }}>
        <Text>Loading...</Text>
      </Flex>
    );
  }

  // Check authentication
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check admin role
  if (requireAdmin && !isAdmin()) {
    return (
      <Container size="2" style={{ marginTop: '4rem' }}>
        <Flex direction="column" align="center" gap="4">
          <ExclamationTriangleIcon width="64" height="64" color="var(--red-9)" />
          <Text size="5" weight="bold">Access Denied</Text>
          <Text size="3" color="gray">
            You need administrator privileges to access this page.
          </Text>
          <Button onClick={() => window.history.back()}>
            Go Back
          </Button>
        </Flex>
      </Container>
    );
  }

  // Check specific permission
  if (requirePermission && !hasPermission(requirePermission)) {
    return (
      <Container size="2" style={{ marginTop: '4rem' }}>
        <Flex direction="column" align="center" gap="4">
          <ExclamationTriangleIcon width="64" height="64" color="var(--red-9)" />
          <Text size="5" weight="bold">Access Denied</Text>
          <Text size="3" color="gray">
            You don't have permission to access this feature.
          </Text>
          <Text size="2" color="gray">
            Required permission: {requirePermission}
          </Text>
          <Button onClick={() => window.history.back()}>
            Go Back
          </Button>
        </Flex>
      </Container>
    );
  }

  // Check if user is active
  if (userProfile && !userProfile.is_active) {
    return (
      <Container size="2" style={{ marginTop: '4rem' }}>
        <Flex direction="column" align="center" gap="4">
          <ExclamationTriangleIcon width="64" height="64" color="var(--orange-9)" />
          <Text size="5" weight="bold">Account Deactivated</Text>
          <Text size="3" color="gray">
            Your account has been deactivated. Please contact an administrator.
          </Text>
        </Flex>
      </Container>
    );
  }

  return <>{children}</>;
}; 