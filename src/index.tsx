import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import createCache from '@emotion/cache';
import { CacheProvider } from '@emotion/react';

import theme from './theme/theme';
import { AppProps, defaultAppProps } from './types/interfaces';
import AppLayout from './components/layout/AppLayout';
import ErrorBoundary from './components/common/ErrorBoundary';
import { NotificationProvider } from './components/common/NotificationProvider';

// Pages
import Dashboard from './pages/Dashboard';
import Library from './pages/Library';
import TrackDetails from './pages/TrackDetails';
import CreatorStudio from './pages/CreatorStudio';
import AnalysisCenter from './pages/AnalysisCenter';
import Settings from './pages/Settings';

// Create emotion cache
const createEmotionCache = () => {
  return createCache({
    key: 'mui',
    prepend: true,
  });
};

const emotionCache = createEmotionCache();

// Create QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry on 404s or other client errors
        if (error instanceof Error && error.message.includes('404')) {
          return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

const App: React.FC<AppProps> = (props = {}) => {
  const appProps = { ...defaultAppProps, ...props };

  return (
    <CacheProvider value={emotionCache}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <NotificationProvider>
            <ErrorBoundary>
              <BrowserRouter>
                <Routes>
                  <Route path="/" element={<AppLayout />}>
                    <Route index element={<Navigate to="/library" replace />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="library" element={<Library />} />
                    <Route path="tracks/:trackId" element={<TrackDetails />} />
                    <Route path="creator-studio" element={<CreatorStudio />} />
                    <Route path="analysis-center" element={<AnalysisCenter />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/library" replace />} />
                  </Route>
                </Routes>
              </BrowserRouter>
            </ErrorBoundary>
          </NotificationProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </CacheProvider>
  );
};

export default App;