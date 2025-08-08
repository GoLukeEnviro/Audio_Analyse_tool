import React, { useState, useEffect } from 'react';
import {
  Typography,
  Stack,
  Card,
  CardContent,
  FormControlLabel,
  Switch,
  TextField,
  Button,
  Divider,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import { useQuery, useMutation, QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a client
const queryClient = new QueryClient();

const SettingsContent: React.FC = () => {
  const [config, setConfig] = useState<any>({
    audio_analysis: {},
    music_library: {},
    export: {},
    development: {}
  });

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['backendSettings'],
    queryFn: async () => {
      const response = await fetch('/api/config/settings');
      if (!response.ok) {
        throw new Error('Netzwerkantwort war nicht ok');
      }
      return response.json();
    },
  });

  const mutation = useMutation({
    mutationFn: async (newConfig: any) => {
      const response = await fetch('/api/config/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config: newConfig }),
      });
      if (!response.ok) {
        throw new Error('Netzwerkantwort war nicht ok');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backendSettings'] });
      alert('Einstellungen erfolgreich gespeichert!');
    },
    onError: (err: any) => {
      alert(`Fehler beim Speichern der Einstellungen: ${err.message}`);
    },
  });

  useEffect(() => {
    if (data) {
      setConfig(data);
    }
  }, [data]);

  const handleChange = (section: string, key: string, value: any) => {
    setConfig((prevConfig: any) => ({
      ...prevConfig,
      [section]: {
        ...prevConfig[section],
        [key]: value,
      },
    }));
  };

  const handleSave = () => {
    mutation.mutate(config);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Einstellungen werden geladen...</Typography>
      </Box>
    );
  }

  if (isError) {
    return (
      <Alert severity="error">
        Fehler beim Laden der Einstellungen: {error?.message || 'Unbekannter Fehler'}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Einstellungen
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Konfigurieren Sie die Anwendung nach Ihren Wünschen
        </Typography>
      </Box>

      {/* Analysis Settings */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Analyse-Einstellungen
          </Typography>
          
          <Stack spacing={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.audio_analysis.enable_multiprocessing || false}
                  onChange={(e) => handleChange('audio_analysis', 'enable_multiprocessing', e.target.checked)}
                />
              }
              label="Multiprocessing aktivieren"
            />
            
            {/* Essentia-Features verwenden (wenn verfügbar) - Not directly mapped to backend config */}
            
            <TextField
              label="Cache-Verzeichnis"
              value={config.audio_analysis.cache_dir || ''}
              onChange={(e) => handleChange('audio_analysis', 'cache_dir', e.target.value)}
              fullWidth
              helperText="Verzeichnis für gespeicherte Analyse-Ergebnisse"
            />
            
            <TextField
              label="Maximale Anzahl Worker"
              type="number"
              value={config.audio_analysis.max_workers || ''}
              onChange={(e) => handleChange('audio_analysis', 'max_workers', parseInt(e.target.value))}
              sx={{ width: 200 }}
            />
          </Stack>
        </CardContent>
      </Card>

      {/* UI Settings - Not directly mapped to backend config, except Debug Mode */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Benutzeroberfläche
          </Typography>
          
          <Stack spacing={3}>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Dark Theme"
            />
            
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Echtzeit-Updates aktivieren"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={config.development.debug || false}
                  onChange={(e) => handleChange('development', 'debug', e.target.checked)}
                />
              }
              label="Debug-Modus"
            />
          </Stack>
        </CardContent>
      </Card>

      {/* Library Settings */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Bibliothek-Einstellungen
          </Typography>
          
          <Stack spacing={3}>
            <TextField
              label="Standard-Musikverzeichnis"
              value={config.music_library.scan_path || ''}
              onChange={(e) => handleChange('music_library', 'scan_path', e.target.value)}
              fullWidth
              helperText="Standardpfad für die Musikbibliothek"
            />
            
            <TextField
              label="Minimale Dateigröße (KB)"
              type="number"
              value={config.music_library.min_file_size_kb || ''}
              onChange={(e) => handleChange('music_library', 'min_file_size_kb', parseInt(e.target.value))}
              sx={{ width: 200 }}
            />
            
            <TextField
              label="Maximale Scan-Tiefe"
              type="number"
              value={config.music_library.max_depth || ''}
              onChange={(e) => handleChange('music_library', 'max_depth', parseInt(e.target.value))}
              sx={{ width: 200 }}
              helperText="Maximale Anzahl von Unterverzeichnissen"
            />
          </Stack>
        </CardContent>
      </Card>

      {/* Export Settings */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Export-Einstellungen
          </Typography>
          
          <Stack spacing={3}>
            <TextField
              label="Export-Verzeichnis"
              value={config.export.output_dir || ''}
              onChange={(e) => handleChange('export', 'output_dir', e.target.value)}
              fullWidth
              helperText="Standardverzeichnis für exportierte Playlists"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={config.export.include_metadata || false}
                  onChange={(e) => handleChange('export', 'include_metadata', e.target.checked)}
                />
              }
              label="Metadaten in Exporte einschließen"
            />
            
            <FormControlLabel
              control={<Switch />}
              label="Automatische Backups erstellen"
            />
          </Stack>
        </CardContent>
      </Card>

      <Divider />

      {/* Actions */}
      <Stack direction="row" spacing={2}>
        <Button variant="contained" color="primary" onClick={handleSave} disabled={mutation.isPending}>
          {mutation.isPending ? <CircularProgress size={24} /> : 'Einstellungen speichern'}
        </Button>
        <Button variant="outlined">
          Zurücksetzen
        </Button>
        <Button variant="outlined" color="error">
          Cache löschen
        </Button>
      </Stack>

      <Alert severity="info">
        Änderungen an den Analyse-Einstellungen erfordern einen Neustart der Anwendung.
      </Alert>
    </Stack>
  );
};

const Settings: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <SettingsContent />
  </QueryClientProvider>
);

export default Settings;