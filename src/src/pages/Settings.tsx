import React from 'react';
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
  Alert
} from '@mui/material';

const Settings: React.FC = () => {
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
              control={<Switch defaultChecked />}
              label="Multiprocessing aktivieren"
            />
            
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Essentia-Features verwenden (wenn verfügbar)"
            />
            
            <TextField
              label="Cache-Verzeichnis"
              defaultValue="/cache/audio"
              fullWidth
              helperText="Verzeichnis für gespeicherte Analyse-Ergebnisse"
            />
            
            <TextField
              label="Maximale Anzahl Worker"
              type="number"
              defaultValue={4}
              sx={{ width: 200 }}
            />
          </Stack>
        </CardContent>
      </Card>

      {/* UI Settings */}
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
              control={<Switch />}
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
              defaultValue="/Users/dj/Music"
              fullWidth
              helperText="Standardpfad für die Musikbibliothek"
            />
            
            <TextField
              label="Minimale Dateigröße (KB)"
              type="number"
              defaultValue={100}
              sx={{ width: 200 }}
            />
            
            <TextField
              label="Maximale Scan-Tiefe"
              type="number"
              defaultValue={10}
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
              defaultValue="/exports"
              fullWidth
              helperText="Standardverzeichnis für exportierte Playlists"
            />
            
            <FormControlLabel
              control={<Switch defaultChecked />}
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
        <Button variant="contained" color="primary">
          Einstellungen speichern
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

export default Settings;