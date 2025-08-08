import React from 'react';
import {
  Typography,
  Stack,
  Card,
  CardContent,
  Box,
  Chip,
  Alert
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LibraryMusicIcon from '@mui/icons-material/LibraryMusic';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import PlaylistPlayIcon from '@mui/icons-material/PlaylistPlay';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { useTracksQuery, useTracksStatsQuery } from '../hooks/useTracksQuery.ts';
import { useAnalysisStatsQuery } from '../hooks/useAnalysisQuery.ts';
import LoadingSkeleton from '../components/common/LoadingSkeleton.tsx';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: tracksData, isLoading: tracksLoading, isError: tracksError } = useTracksQuery({ per_page: 1 });
  const { data: tracksStats, isLoading: statsLoading } = useTracksStatsQuery({ refetchInterval: 30000 });
  const { data: analysisStats } = useAnalysisStatsQuery({ refetchInterval: 30000 });

  const isLoading = tracksLoading || statsLoading;

  const statsCards = [
    {
      title: 'Analysierte Tracks',
      value: tracksStats?.total_tracks || tracksData?.total_count || 0,
      icon: <LibraryMusicIcon />,
      color: 'primary.main'
    },
    {
      title: 'Durchschnittliche BPM',
      value: tracksStats?.statistics?.average_bpm ? Math.round(tracksStats.statistics.average_bpm) : '---',
      icon: <TrendingUpIcon />,
      color: 'secondary.main'
    },
    {
      title: 'Cache Hit Rate',
      value: analysisStats?.analyzer_stats?.cache_hit_rate ? `${analysisStats.analyzer_stats.cache_hit_rate}%` : '---',
      icon: <PlaylistPlayIcon />,
      color: 'success.main'
    },
    {
      title: 'Laufende Analysen',
      value: analysisStats?.current_session?.running_tasks || 0,
      icon: <AnalyticsIcon />,
      color: 'warning.main'
    }
  ];

  if (isLoading) {
    return <LoadingSkeleton variant="dashboard-cards" count={4} />;
  }

  if (tracksError) {
    return (
      <Stack spacing={3}>
        <Alert severity="error">
          Fehler beim Laden der Dashboard-Daten. Stellen Sie sicher, dass das Backend läuft.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Willkommen im Visual DJ Analysis Studio
        </Typography>
      </Box>

      <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap' }}>
        {statsCards.map((card, index) => (
          <Card key={index} sx={{ minWidth: 200, flex: 1 }}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: card.color }}>
                    {card.value}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {card.title}
                  </Typography>
                </Box>
                <Box sx={{ 
                  p: 1.5, 
                  borderRadius: 2, 
                  backgroundColor: `${card.color}15`,
                  color: card.color 
                }}>
                  {card.icon}
                </Box>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Schnellzugriff
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
            <Chip 
              label="Neue Analyse starten" 
              clickable 
              color="primary" 
              variant="outlined"
              onClick={() => navigate('/analysis-center')}
            />
            <Chip 
              label="Playlist generieren" 
              clickable 
              color="secondary" 
              variant="outlined"
              onClick={() => navigate('/creator-studio')}
            />
            <Chip 
              label="Bibliothek durchsuchen" 
              clickable 
              color="info" 
              variant="outlined"
              onClick={() => navigate('/library')}
            />
            <Chip 
              label="Einstellungen" 
              clickable 
              color="default" 
              variant="outlined"
              onClick={() => navigate('/settings')}
            />
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Letzte Aktivitäten
          </Typography>
          <Stack spacing={2}>
            <Box sx={{ p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="body2">
                Analyse von 15 Tracks abgeschlossen
              </Typography>
              <Typography variant="caption" color="text.secondary">
                vor 2 Stunden
              </Typography>
            </Box>
            <Box sx={{ p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="body2">
                Playlist "Summer Vibes" generiert
              </Typography>
              <Typography variant="caption" color="text.secondary">
                vor 1 Tag
              </Typography>
            </Box>
            <Box sx={{ p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="body2">
                Neue Tracks zur Bibliothek hinzugefügt
              </Typography>
              <Typography variant="caption" color="text.secondary">
                vor 3 Tagen
              </Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

export default Dashboard;