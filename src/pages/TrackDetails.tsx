import React from 'react';
import {
  Typography,
  Stack,
  Card,
  CardContent,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Button
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AudiotrackIcon from '@mui/icons-material/Audiotrack';
import { useTrackDetailsQuery } from '../hooks/useTracksQuery';
import { formatDuration, formatBPM, formatEnergy, formatMood, formatFileSize } from '../utils/formatters';
import EnergyChart from '../components/charts/EnergyChart';
import LoadingSkeleton from '../components/common/LoadingSkeleton';

const TrackDetails: React.FC = () => {
  const { trackId } = useParams<{ trackId: string }>();
  const navigate = useNavigate();
  
  const { data: trackDetails, isLoading, isError } = useTrackDetailsQuery(
    trackId ? decodeURIComponent(trackId) : '',
    true
  );

  const handleBack = () => {
    navigate('/library');
  };

  if (isLoading) {
    return <LoadingSkeleton variant="track-details" />;
  }

  if (isError || !trackDetails) {
    return (
      <Box sx={{ p: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mb: 2 }}>
          Zurück zur Bibliothek
        </Button>
        <Typography color="error">
          Track nicht gefunden oder Fehler beim Laden.
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mb: 2 }}>
          Zurück zur Bibliothek
        </Button>
        <Typography variant="h4" gutterBottom>
          Track-Detailansicht
        </Typography>
      </Box>

      {/* Header Card */}
      <Card>
        <CardContent>
          <Stack direction="row" spacing={3} alignItems="center">
            <Box sx={{ 
              width: 80, 
              height: 80, 
              backgroundColor: 'primary.main',
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <AudiotrackIcon sx={{ fontSize: 40, color: 'primary.contrastText' }} />
            </Box>
            
            <Stack spacing={1} sx={{ flex: 1 }}>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {trackDetails.metadata.title || trackDetails.filename}
              </Typography>
              <Typography variant="h6" color="text.secondary">
                {trackDetails.metadata.artist || 'Unknown Artist'}
              </Typography>
              {trackDetails.metadata.album && (
                <Typography variant="body2" color="text.secondary">
                  Album: {trackDetails.metadata.album}
                </Typography>
              )}
              
              <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                <Chip 
                  label={formatBPM(trackDetails.features.bpm)} 
                  color="primary" 
                />
                <Chip 
                  label={trackDetails.camelot.camelot} 
                  color="secondary" 
                />
                <Chip 
                  label={formatEnergy(trackDetails.features.energy)} 
                  color="info" 
                />
                <Chip 
                  label={formatMood(trackDetails.mood.primary_mood)} 
                  color="success" 
                />
              </Stack>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {/* Energy Chart */}
      <EnergyChart 
        data={trackDetails.time_series_features}
        title="Energie-Verlauf über Zeit"
        height={400}
      />

      {/* Metadata and Features */}
      <Stack direction="row" spacing={3}>
        {/* File Metadata */}
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Datei-Informationen
            </Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>Dateiname</TableCell>
                  <TableCell>{trackDetails.filename}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Format</TableCell>
                  <TableCell>{trackDetails.metadata.format}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Dateigröße</TableCell>
                  <TableCell>{formatFileSize(trackDetails.metadata.file_size)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Bitrate</TableCell>
                  <TableCell>{trackDetails.metadata.bitrate} kbps</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Dauer</TableCell>
                  <TableCell>{formatDuration(trackDetails.metadata.duration)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Analysiert am</TableCell>
                  <TableCell>
                    {new Date(trackDetails.metadata.analyzed_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Audio Features */}
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Audio-Features
            </Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>BPM</TableCell>
                  <TableCell>{trackDetails.features.bpm.toFixed(1)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Energie</TableCell>
                  <TableCell>{formatEnergy(trackDetails.features.energy)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Valenz</TableCell>
                  <TableCell>{formatEnergy(trackDetails.features.valence)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Tanzbarkeit</TableCell>
                  <TableCell>{formatEnergy(trackDetails.features.danceability)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Akustik</TableCell>
                  <TableCell>{formatEnergy(trackDetails.features.acousticness)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Instrumental</TableCell>
                  <TableCell>{formatEnergy(trackDetails.features.instrumentalness)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Harmonic Information */}
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Harmonische Informationen
            </Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>Tonart</TableCell>
                  <TableCell>{trackDetails.camelot.key}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Camelot</TableCell>
                  <TableCell>{trackDetails.camelot.camelot}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Kompatible Keys</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                      {trackDetails.camelot.compatible_keys.map((key) => (
                        <Chip key={key} label={key} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Stimmungsanalyse
              </Typography>
              <Typography variant="body2">
                Primäre Stimmung: <strong>{formatMood(trackDetails.mood.primary_mood)}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Konfidenz: {(trackDetails.mood.confidence * 100).toFixed(1)}%
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Stack>
    </Stack>
  );
};

export default TrackDetails;