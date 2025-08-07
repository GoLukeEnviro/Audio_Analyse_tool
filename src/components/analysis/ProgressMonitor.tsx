import React from 'react';
import {
  Paper,
  Typography,
  LinearProgress,
  Stack,
  Box,
  Chip,
  Button
} from '@mui/material';
import { AnalysisStatusResponse } from '../../types/interfaces';
import { formatProgress, formatAnalysisStatus } from '../../utils/formatters';
import { AnalysisStatus } from '../../types/enums';

interface ProgressMonitorProps {
  analysisStatus: AnalysisStatusResponse;
  onCancel?: () => void;
}

const ProgressMonitor: React.FC<ProgressMonitorProps> = ({ 
  analysisStatus, 
  onCancel 
}) => {
  const getStatusColor = (status: AnalysisStatus) => {
    switch (status) {
      case AnalysisStatus.RUNNING:
        return 'primary';
      case AnalysisStatus.COMPLETED:
        return 'success';
      case AnalysisStatus.ERROR:
        return 'error';
      case AnalysisStatus.CANCELLED:
        return 'warning';
      default:
        return 'default';
    }
  };

  const isActive = analysisStatus.status === AnalysisStatus.RUNNING;

  return (
    <Paper sx={{ p: 3 }}>
      <Stack spacing={2}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            Analyse-Status
          </Typography>
          <Chip 
            label={formatAnalysisStatus(analysisStatus.status)}
            color={getStatusColor(analysisStatus.status) as any}
            variant="outlined"
          />
        </Stack>
        
        {isActive && (
          <>
            <Box>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Fortschritt
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {formatProgress(analysisStatus.progress)}
                </Typography>
              </Stack>
              <LinearProgress 
                variant="determinate" 
                value={analysisStatus.progress}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
            
            {analysisStatus.current_file && (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Aktuelle Datei:
                </Typography>
                <Typography variant="body2" fontWeight={500}>
                  {analysisStatus.current_file}
                </Typography>
              </Box>
            )}
            
            <Stack direction="row" spacing={3}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Verarbeitet
                </Typography>
                <Typography variant="h6">
                  {analysisStatus.processed_files} / {analysisStatus.total_files}
                </Typography>
              </Box>
              
              {analysisStatus.estimated_completion && (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Geschätzte Fertigstellung
                  </Typography>
                  <Typography variant="body2">
                    {new Date(analysisStatus.estimated_completion).toLocaleTimeString()}
                  </Typography>
                </Box>
              )}
            </Stack>
            
            {onCancel && (
              <Button 
                variant="outlined" 
                color="error" 
                onClick={onCancel}
                sx={{ alignSelf: 'flex-start' }}
              >
                Analyse abbrechen
              </Button>
            )}
          </>
        )}
        
        {analysisStatus.status === AnalysisStatus.COMPLETED && (
          <Box>
            <Typography variant="body1" color="success.main">
              Analyse erfolgreich abgeschlossen!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {analysisStatus.total_files} Dateien wurden verarbeitet.
            </Typography>
          </Box>
        )}
        
        {analysisStatus.status === AnalysisStatus.ERROR && (
          <Box>
            <Typography variant="body1" color="error.main">
              Analyse fehlgeschlagen
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Bitte überprüfen Sie die Logs für weitere Details.
            </Typography>
          </Box>
        )}
      </Stack>
    </Paper>
  );
};

export default ProgressMonitor;