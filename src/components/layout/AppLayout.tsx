import React from 'react';
import { Box, CssBaseline } from '@mui/material';
import { Outlet } from 'react-router-dom';
import NavigationSidebar from './NavigationSidebar';

const DRAWER_WIDTH = 280;

const AppLayout: React.FC = () => {
  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <NavigationSidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
          p: 3
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default AppLayout;