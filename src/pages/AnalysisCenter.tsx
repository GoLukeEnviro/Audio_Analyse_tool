import React, { useState } from 'react';
import {
  Typography,
  Stack,
  Card,
  CardContent,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  Box
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useStartAnalysisMutation, useAnalysisStatusQuery, useCancelAnalysisMutation } from '../hooks/useAnalysisQuery';
import ProgressMonitor from '../components/analysis/ProgressMonitor';

const AnalysisCenter: React.FC = () => {
  const [directories, setDirectories] = useState<string>('');
  const [recursive, setRecursive] = useState(true);
  const [overwriteCache, setOverwriteCache] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string>('');

  const startAnalysisMutation = useStartAnalysisMutation();
  const cancelAnalysisMutation = useCancelAnalysisMutation();
  
  const { data: analysisStatus } = useAnalysisStatusQuery(
    currentTaskId, 
    currentTaskId ? 2000 : 0
  );

  const handleStartAnalysis = async () => {
    if (!directories.trim()) {
      return;
    }

    try {
      const result = await startAnalysisMutation.mutateAsync({
        directories: directories.split('\n').map(d => d.trim()).filter(d => d),
        recursive,
        overwrite_cache: overwriteCache
      });
      
      setCurrentTaskId(result.task_id);
    } catch (error) {
      console.error('Failed to start analysis:', error);
    }
  };

  const handleCancelAnalysis = async () => {
    if (!currentTaskId) return;

    try {
      await cancelAnalysisMutation.mutateAsync(currentTaskId);
      setCurrentTaskId('');
    } catch (error) {
      console.error('Failed to cancel analysis:', error);
    }
  };

  const isAnalysisRunning = analysisStatus?.status === 'running';

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Analyse-Center
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Starten und überwachen Sie die Audio-Analyse Ihrer Musikbibliothek
        </Typography>
      </Box>

      {/* Analysis Configuration */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Analyse konfigurieren
          </Typography>
          
          <Stack spacing={3}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Verzeichnisse"
              placeholder="Geben Sie die Pfade zu Ihren Musik-Verzeichnissen ein (ein Pfad pro Zeile)"
              value={directories}
              onChange={(e) => setDirectories(e.target.value)}
              disabled={isAnalysisRunning}
              helperText="Beispiel: /Users/dj/Music/Electronic"
            />
            
            <Stack direction="row" spacing={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={recursive}
                    onChange={(e) => setRecursive(e.target.checked)}
                    disabled={isAnalysisRunning}
                  />
                }
                label="Unterverzeichnisse einschließen"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={overwriteCache}
                    onChange={(e) => setOverwriteCache(e.target.checked)}
                    disabled={isAnalysisRunning}
                  />
                }
                label="Vorhandenen Cache überschreiben"
              />
            </Stack>
            
            <Box>
              <Button
                variant="contained"
                size="large"
                startIcon={<PlayArrowIcon />}
                onClick={handleStartAnalysis}
                disabled={!directories.trim() || isAnalysisRunning || startAnalysisMutation.isLoading}
                sx={{ mr: 2 }}
              >
                {startAnalysisMutation.isLoading ? 'Starte...' : 'Analyse starten'}
              </Button>
              
              {isAnalysisRunning && (
                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleCancelAnalysis}
                  disabled={cancelAnalysisMutation.isLoading}
                >
                  {cancelAnalysisMutation.isLoading ? 'Bricht ab...' : 'Abbrechen'}
                </Button>
              )}
            </Box>
            
            {startAnalysisMutation.isError && (
              <Alert severity="error">
                Fehler beim Starten der Analyse. Bitte überprüfen Sie die Verzeichnispfade.
              </Alert>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* Progress Monitor */}
      {analysisStatus && (
        <ProgressMonitor
          analysisStatus={analysisStatus}
          onCancel={isAnalysisRunning ? handleCancelAnalysis : undefined}
        />
      )}

      {/* Information Card */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Hinweise zur Audio-Analyse
          </Typography>
          
          <Stack spacing={2}>
            <Alert severity="info">
              Die Analyse kann je nach Anzahl der Dateien mehrere Minuten dauern. 
              Sie können den Fortschritt in Echtzeit verfolgen.
            </Alert>
            
            <Typography variant="body2" color="text.secondary">
              <strong>Unterstützte Formate:</strong> MP3, WAV, FLAC, M4A, AAC, OGG
            </Typography>
            
            <Typography variant="body2" color="text.secondary">
              <strong>Analysierte Features:</strong> BPM, Energie, Valenz, Tanzbarkeit, 
              Tonart, Camelot Wheel Position, Stimmung und Zeitreihen-Daten
            </Typography>
            
            <Typography variant="body2" color="text.secondary">
              <strong>Cache:</strong> Bereits analysierte Dateien werden übersprungen, 
              es sei denn, Sie aktivieren "Cache überschreiben"
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

export default AnalysisCenter;