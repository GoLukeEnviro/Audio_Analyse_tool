import React, { useState } from 'react';
import {
  Typography,
  Stack,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Box,
  Alert,
  Chip
} from '@mui/material';
import CreateIcon from '@mui/icons-material/Create';
import DownloadIcon from '@mui/icons-material/Download';
import { useGeneratePlaylistMutation, usePlaylistGenerationStatusQuery, useExportPlaylistMutation } from '../hooks/usePlaylistQuery.ts';
import { ExportFormat, SortingAlgorithm } from '../types/enums.ts';
import { useNotification } from '../components/common/NotificationProvider.tsx';
import TrackSelector from '../components/tracks/TrackSelector.tsx';

const CreatorStudio: React.FC = () => {
  const [targetDuration, setTargetDuration] = useState(60);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<SortingAlgorithm>(SortingAlgorithm.HYBRID_SMART);
  const [energyCurve, setEnergyCurve] = useState<number[]>([0.3, 0.6, 0.9, 0.7, 0.4]);
  const [currentTaskId, setCurrentTaskId] = useState<string>('');
  const [selectedTracks, setSelectedTracks] = useState<string[]>([]);

  const { showSuccess, showError, showWarning } = useNotification();
  const generatePlaylistMutation = useGeneratePlaylistMutation();
  const exportPlaylistMutation = useExportPlaylistMutation();
  
  const { data: generationStatus } = usePlaylistGenerationStatusQuery(
    currentTaskId,
    currentTaskId ? 2000 : 0
  );

  const handleGeneratePlaylist = async () => {
    if (selectedTracks.length === 0) {
      showError('Bitte wählen Sie mindestens einen Track aus.');
      return;
    }

    try {
      const result = await generatePlaylistMutation.mutateAsync({
        track_file_paths: selectedTracks,
        target_duration_minutes: targetDuration,
        custom_rules: [{
          type: 'energy_curve',
          values: energyCurve
        }]
      });
      
      setCurrentTaskId(result.task_id);
      showSuccess(`Playlist-Generierung gestartet! Task ID: ${result.task_id}`);
    } catch (error) {
      console.error('Failed to generate playlist:', error);
      showError(error instanceof Error ? error.message : 'Fehler beim Generieren der Playlist');
    }
  };

  const handleExportPlaylist = async (format: ExportFormat) => {
    if (!generationStatus?.result) {
      showError('Keine Playlist zum Exportieren verfügbar');
      return;
    }

    try {
      const result = await exportPlaylistMutation.mutateAsync({
        playlist_data: generationStatus.result,
        format_type: format,
        filename: `playlist_${Date.now()}.${format}`,
        include_metadata: true
      });

      if (result.success) {
        showSuccess(`Playlist erfolgreich als ${format.toUpperCase()} exportiert`);
      } else {
        showError(result.error || 'Export fehlgeschlagen');
      }
    } catch (error) {
      console.error('Failed to export playlist:', error);
      showError(error instanceof Error ? error.message : 'Fehler beim Exportieren der Playlist');
    }
  };

  const isGenerating = generationStatus?.status === 'generating' || generationStatus?.status === 'loading_tracks';
  const isCompleted = generationStatus?.status === 'completed';

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Creator Studio
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Erstellen Sie intelligente Playlists basierend auf Audio-Features
        </Typography>
      </Box>

      {/* Track Selection */}
      <TrackSelector
        selectedTracks={selectedTracks}
        onSelectionChange={setSelectedTracks}
        maxSelection={50}
      />

      {/* Playlist Configuration */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Playlist-Regeln definieren
          </Typography>
          
          <Stack spacing={3}>
            <Stack direction="row" spacing={2}>
              <TextField
                label="Zieldauer (Minuten)"
                type="number"
                value={targetDuration}
                onChange={(e) => setTargetDuration(Number(e.target.value))}
                disabled={isGenerating}
                sx={{ width: 200 }}
              />
              
              <FormControl sx={{ minWidth: 200 }}>
                <InputLabel>Algorithmus</InputLabel>
                <Select
                  value={selectedAlgorithm}
                  label="Algorithmus"
                  onChange={(e) => setSelectedAlgorithm(e.target.value as SortingAlgorithm)}
                  disabled={isGenerating}
                >
                  <MenuItem value={SortingAlgorithm.HYBRID_SMART}>Hybrid Smart</MenuItem>
                  <MenuItem value={SortingAlgorithm.BPM_PROGRESSION}>BPM Progression</MenuItem>
                  <MenuItem value={SortingAlgorithm.ENERGY_FLOW}>Energy Flow</MenuItem>
                  <MenuItem value={SortingAlgorithm.HARMONIC_MIXING}>Harmonic Mixing</MenuItem>
                  <MenuItem value={SortingAlgorithm.MOOD_JOURNEY}>Mood Journey</MenuItem>
                </Select>
              </FormControl>
            </Stack>
            
            {/* Energy Curve */}
            <Box>
              <Typography gutterBottom>
                Energie-Kurve (Start → Peak → Ende)
              </Typography>
              <Box sx={{ px: 2 }}>
                <Slider
                  value={energyCurve}
                  onChange={(_, newValue) => setEnergyCurve(newValue as number[])}
                  valueLabelDisplay="auto"
                  min={0}
                  max={1}
                  step={0.1}
                  marks
                  disabled={isGenerating}
                  valueLabelFormat={(value) => `${Math.round(value * 100)}%`}
                />
              </Box>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                {energyCurve.map((value, index) => (
                  <Chip 
                    key={index}
                    label={`${Math.round(value * 100)}%`}
                    size="small"
                    color={value > 0.7 ? 'error' : value > 0.4 ? 'warning' : 'success'}
                  />
                ))}
              </Stack>
            </Box>
            
            <Button
              variant="contained"
              size="large"
              startIcon={<CreateIcon />}
              onClick={handleGeneratePlaylist}
              disabled={selectedTracks.length === 0 || isGenerating || generatePlaylistMutation.isLoading}
            >
              {generatePlaylistMutation.isLoading ? 'Starte...' : 'Playlist generieren'}
            </Button>
            
            {generatePlaylistMutation.isError && (
              <Alert severity="error">
                <Typography variant="subtitle2" gutterBottom>
                  Fehler beim Generieren der Playlist
                </Typography>
                <Typography variant="body2">
                  {generatePlaylistMutation.error instanceof Error 
                    ? generatePlaylistMutation.error.message 
                    : 'Stellen Sie sicher, dass genügend analysierte Tracks verfügbar sind und das Backend läuft.'}
                </Typography>
              </Alert>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* Generation Status */}
      {generationStatus && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Generierungsstatus
            </Typography>
            
            <Stack spacing={2}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Status: <strong>{generationStatus.status}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Fortschritt: <strong>{Math.round(generationStatus.progress)}%</strong>
                </Typography>
                {generationStatus.message && (
                  <Typography variant="body2" color="text.secondary">
                    {generationStatus.message}
                  </Typography>
                )}
              </Box>
              
              {isCompleted && generationStatus.result && (
                <Box>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    Playlist erfolgreich generiert! {generationStatus.result.tracks?.length || 0} Tracks
                  </Alert>
                  
                  <Typography variant="subtitle1" gutterBottom>
                    Export-Optionen:
                  </Typography>
                  <Stack direction="row" spacing={1}>
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExportPlaylist(ExportFormat.M3U)}
                      disabled={exportPlaylistMutation.isLoading}
                    >
                      M3U
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExportPlaylist(ExportFormat.JSON)}
                      disabled={exportPlaylistMutation.isLoading}
                    >
                      JSON
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExportPlaylist(ExportFormat.CSV)}
                      disabled={exportPlaylistMutation.isLoading}
                    >
                      CSV
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExportPlaylist(ExportFormat.REKORDBOX)}
                      disabled={exportPlaylistMutation.isLoading}
                    >
                      Rekordbox
                    </Button>
                  </Stack>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Information */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Wie funktioniert die Playlist-Generierung?
          </Typography>
          
          <Stack spacing={2}>
            <Typography variant="body2" color="text.secondary">
              <strong>1. Algorithmus wählen:</strong> Verschiedene Algorithmen erstellen unterschiedliche Playlist-Flows
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>2. Energie-Kurve definieren:</strong> Bestimmen Sie den Energieverlauf Ihrer Playlist
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>3. Zieldauer festlegen:</strong> Die Playlist wird auf die gewünschte Dauer optimiert
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>4. Export:</strong> Exportieren Sie die Playlist in verschiedene Formate für Ihre DJ-Software
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

export default CreatorStudio;