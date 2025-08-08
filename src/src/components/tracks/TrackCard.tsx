import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Stack, 
  Chip, 
  IconButton,
  Box
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AudiotrackIcon from '@mui/icons-material/Audiotrack';
import { TrackSummary } from '../../types/interfaces';
import { formatDuration, formatBPM, formatEnergy, formatMood } from '../../utils/formatters.ts';

interface TrackCardProps {
  track: TrackSummary;
  onClick?: () => void;
  showPlayButton?: boolean;
}

const TrackCard: React.FC<TrackCardProps> = ({ 
  track, 
  onClick, 
  showPlayButton = true 
}) => {
  return (
    <Card 
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: onClick ? 'translateY(-2px)' : 'none',
          boxShadow: onClick ? 4 : 1,
        }
      }}
      onClick={onClick}
    >
      <CardContent>
        <Stack direction="row" spacing={2} alignItems="center">
          <Box sx={{ 
            width: 48, 
            height: 48, 
            backgroundColor: 'primary.main',
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <AudiotrackIcon sx={{ color: 'primary.contrastText' }} />
          </Box>
          
          <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0 }}>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                fontWeight: 600,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
            >
              {track.title || track.filename}
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ 
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
            >
              {track.artist || 'Unknown Artist'}
            </Typography>
            
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip 
                label={formatBPM(track.bpm)} 
                size="small" 
                variant="outlined" 
              />
              <Chip 
                label={track.camelot} 
                size="small" 
                color="primary" 
                variant="outlined"
              />
              <Chip 
                label={formatEnergy(track.energy)} 
                size="small" 
                color="secondary" 
                variant="outlined"
              />
              {track.mood && (
                <Chip 
                  label={formatMood(track.mood)} 
                  size="small" 
                  color="info" 
                  variant="outlined"
                />
              )}
            </Stack>
          </Stack>
          
          <Stack alignItems="flex-end" spacing={1}>
            <Typography variant="caption" color="text.secondary">
              {formatDuration(track.duration)}
            </Typography>
            {showPlayButton && (
              <IconButton 
                size="small" 
                color="primary"
                onClick={(e) => {
                  e.stopPropagation();
                  // Handle play functionality
                }}
              >
                <PlayArrowIcon />
              </IconButton>
            )}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default TrackCard;