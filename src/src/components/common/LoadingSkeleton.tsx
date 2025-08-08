import React from 'react';
import { Skeleton, Stack, Card, CardContent } from '@mui/material';

interface LoadingSkeletonProps {
  variant?: 'track-list' | 'track-details' | 'dashboard-cards' | 'playlist-timeline';
  count?: number;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ 
  variant = 'track-list', 
  count = 5 
}) => {
  const renderTrackListSkeleton = () => (
    <Stack spacing={1}>
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton 
          key={index} 
          variant="rectangular" 
          height={60} 
          sx={{ borderRadius: 1 }} 
        />
      ))}
    </Stack>
  );

  const renderTrackDetailsSkeleton = () => (
    <Stack spacing={3}>
      <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
      <Stack direction="row" spacing={2}>
        <Skeleton variant="rectangular" width={120} height={120} sx={{ borderRadius: 2 }} />
        <Stack spacing={1} sx={{ flex: 1 }}>
          <Skeleton variant="text" width="60%" height={32} />
          <Skeleton variant="text" width="40%" height={24} />
          <Skeleton variant="text" width="80%" height={20} />
        </Stack>
      </Stack>
      <Skeleton variant="rectangular" height={300} sx={{ borderRadius: 2 }} />
    </Stack>
  );

  const renderDashboardCardsSkeleton = () => (
    <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index} sx={{ minWidth: 200, flex: 1 }}>
          <CardContent>
            <Skeleton variant="text" width="80%" height={24} />
            <Skeleton variant="text" width="60%" height={40} />
            <Skeleton variant="rectangular" height={60} sx={{ mt: 2, borderRadius: 1 }} />
          </CardContent>
        </Card>
      ))}
    </Stack>
  );

  const renderPlaylistTimelineSkeleton = () => (
    <Stack spacing={2}>
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="center">
              <Skeleton variant="rectangular" width={60} height={60} sx={{ borderRadius: 1 }} />
              <Stack spacing={1} sx={{ flex: 1 }}>
                <Skeleton variant="text" width="70%" height={20} />
                <Skeleton variant="text" width="50%" height={16} />
              </Stack>
              <Skeleton variant="rectangular" width={100} height={40} sx={{ borderRadius: 1 }} />
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );

  switch (variant) {
    case 'track-details':
      return renderTrackDetailsSkeleton();
    case 'dashboard-cards':
      return renderDashboardCardsSkeleton();
    case 'playlist-timeline':
      return renderPlaylistTimelineSkeleton();
    default:
      return renderTrackListSkeleton();
  }
};

export default LoadingSkeleton;