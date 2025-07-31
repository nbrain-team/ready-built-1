import { Theme } from '@radix-ui/themes';
import { Outlet } from 'react-router-dom';

export const AuthLayout = () => {
  return (
    <Theme accentColor="blue" panelBackground="solid" appearance="light" scaling="100%">
      <Outlet />
    </Theme>
  );
}; 