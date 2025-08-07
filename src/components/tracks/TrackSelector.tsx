import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Stack,
  Checkbox,
  FormControlLabel,
  TextField,
  InputAdornment,
  Box,
  Chip,
  Alert,
  Pagination
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useTracksQuery } from '../../hooks/useTracksQuery';
import { TrackSummary } from '../../types/interfaces';
import LoadingSkeleton from '../common/LoadingSkeleton';

interface TrackSelectorProps {
  selectedTracks: string[];
  onSelectionChange: (trackPaths: string[]) => void;
  maxSelection?: number;
}

const TrackSelector: React.FC<TrackSelectorProps> = ({
  selectedTracks,
  onSelectionChange,
  maxSelection = 50
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const { data: tracksData, isLoading, isError } = useTracksQuery({
    page: currentPage,
    per_page: 10,
    search: searchQuery || undefined,
  });

  const handleTrackToggle = (trackPath: string) => {
    if (selectedTracks.includes(trackPath)) {
      onSelectionChange(selectedTracks.filter(path => path !== trackPath));
    } else if (selectedTracks.length < maxSelection) {
      onSelectionChange([...selectedTracks, trackPath]);
    }
  };

  const handleSelectAll = () => {
    if (!tracksData?.tracks) return;
    
    const currentPagePaths = tracksData.tracks.map(track => track.file_path);
    const newSelection = [...selectedTracks];
    
    currentPagePaths.forEach(path => {
      if (!newSelection.includes(path) && newSelection.length < maxSelection) {
        newSelection.push(path);
      }
    });
    
    onSelectionChange(newSelection);
  };

  const handleDeselectAll = () => {
    if (!tracksData?.tracks) return;
    
    const currentPagePaths = tracksData.tracks.map(track => track.file_path);
    const newSelection = selectedTracks.filter(path => !currentPagePaths.includes(path));
    
    onSelectionChange(newSelection);
  };

  const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
  };

  if (isLoading) {
    return <LoadingSkeleton variant="track-list" count={5} />;
  }

  if (isError) {
    return (
      <Alert severity="error">
        Fehler beim Laden der Tracks. Stellen Sie sicher, dass Tracks analysiert wurden.
      </Alert>
    );
  }

  const allCurrentPageSelected = tracksData?.tracks.every(track => 
    selectedTracks.includes(track.file_path)
  ) ?? false;

  const someCurrentPageSelected = tracksData?.tracks.some(track => 
    selectedTracks.includes(track.file_path)
  ) ?? false;

  return (
    <Card>
      <CardContent>
        <Stack spacing={3}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Track-Auswahl für Playlist
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Wählen Sie bis zu {maxSelection} Tracks für die Playlist-Generierung aus
            </Typography>
          </Box>

          {/* Search */}
          <TextField
            fullWidth
            placeholder="Tracks durchsuchen..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          {/* Selection Info */}
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" color="text.secondary">
              {selectedTracks.length} von {maxSelection} Tracks ausgewählt
            </Typography>
            
            <Stack direction="row" spacing={1}>
              <Chip
                label="Alle auf Seite auswählen"
                clickable
                size="small"
                variant="outlined"
                onClick={handleSelectAll}
                disabled={allCurrentPageSelected || selectedTracks.length >= maxSelection}
              />
              <Chip
                label="Alle auf Seite abwählen"
                clickable
                size="small"
                variant="outlined"
                onClick={handleDeselectAll}
                disabled={!someCurrentPageSelected}
              />
            </Stack>
          </Stack>

          {/* Track List */}
          <Stack spacing={1}>
            {tracksData?.tracks.map((track: TrackSummary) => {
              const isSelected = selectedTracks.includes(track.file_path);
              const canSelect = !isSelected && selectedTracks.length < maxSelection;
              
              return (
                <Box
                  key={track.file_path}
                  sx={{
                    p: 2,
                    border: 1,
                    borderColor: isSelected ? 'primary.main' : 'divider',
                    borderRadius: 1,
                    backgroundColor: isSelected ? 'primary.light' : 'transparent',
                    opacity: (!canSelect && !isSelected) ? 0.5 : 1,
                  }}
                >
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={isSelected}
                        onChange={() => handleTrackToggle(track.file_path)}
                        disabled={!canSelect && !isSelected}
                      />
                    }
                    label={
                      <Stack spacing={0.5} sx={{ ml: 1 }}>
                        <Typography variant="subtitle2">
                          {track.title || track.filename}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {track.artist || 'Unknown Artist'} • {Math.round(track.bpm)} BPM • {track.camelot}
                        </Typography>
                      </Stack>
                    }
                    sx={{ margin: 0, alignItems: 'flex-start' }}
                  />
                </Box>
              );
            })}
          </Stack>

          {/* Pagination */}
          {tracksData && tracksData.total_pages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <Pagination
                count={tracksData.total_pages}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}

          {selectedTracks.length === 0 && (
            <Alert severity="info">
              Wählen Sie mindestens einen Track aus, um eine Playlist zu generieren.
            </Alert>
          )}

          {selectedTracks.length >= maxSelection && (
            <Alert severity="warning">
              Maximale Anzahl von {maxSelection} Tracks erreicht.
            </Alert>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default TrackSelector;