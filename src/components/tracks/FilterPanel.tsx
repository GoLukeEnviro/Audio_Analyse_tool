import React from 'react';
import {
  Paper,
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Typography,
  Box,
  InputAdornment,
  Chip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { MoodCategory } from '../../types/enums';
import { formatMood } from '../../utils/formatters';

interface FilterPanelProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  selectedMood: MoodCategory | '';
  onMoodChange: (mood: MoodCategory | '') => void;
  bpmRange: [number, number];
  onBpmRangeChange: (range: [number, number]) => void;
  energyRange: [number, number];
  onEnergyRangeChange: (range: [number, number]) => void;
  selectedKey: string;
  onKeyChange: (key: string) => void;
}

const MUSICAL_KEYS = [
  '1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B',
  '5A', '5B', '6A', '6B', '7A', '7B', '8A', '8B',
  '9A', '9B', '10A', '10B', '11A', '11B', '12A', '12B'
];

const FilterPanel: React.FC<FilterPanelProps> = ({
  searchQuery,
  onSearchChange,
  selectedMood,
  onMoodChange,
  bpmRange,
  onBpmRangeChange,
  energyRange,
  onEnergyRangeChange,
  selectedKey,
  onKeyChange
}) => {
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Filter & Suche
      </Typography>
      
      <Stack spacing={3}>
        {/* Search */}
        <TextField
          fullWidth
          placeholder="Suche nach Titel, Künstler oder Dateiname..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        
        {/* Mood and Key Filters */}
        <Stack direction="row" spacing={2}>
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Stimmung</InputLabel>
            <Select
              value={selectedMood}
              label="Stimmung"
              onChange={(e) => onMoodChange(e.target.value as MoodCategory | '')}
            >
              <MenuItem value="">Alle</MenuItem>
              {Object.values(MoodCategory).map((mood) => (
                <MenuItem key={mood} value={mood}>
                  {formatMood(mood)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Camelot Key</InputLabel>
            <Select
              value={selectedKey}
              label="Camelot Key"
              onChange={(e) => onKeyChange(e.target.value)}
            >
              <MenuItem value="">Alle</MenuItem>
              {MUSICAL_KEYS.map((key) => (
                <MenuItem key={key} value={key}>
                  {key}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
        
        {/* BPM Range Slider */}
        <Box>
          <Typography gutterBottom>
            BPM Bereich: {bpmRange[0]} - {bpmRange[1]}
          </Typography>
          <Slider
            value={bpmRange}
            onChange={(_, newValue) => onBpmRangeChange(newValue as [number, number])}
            valueLabelDisplay="auto"
            min={60}
            max={200}
            sx={{ mt: 1 }}
          />
        </Box>
        
        {/* Energy Range Slider */}
        <Box>
          <Typography gutterBottom>
            Energie Bereich: {Math.round(energyRange[0] * 100)}% - {Math.round(energyRange[1] * 100)}%
          </Typography>
          <Slider
            value={energyRange}
            onChange={(_, newValue) => onEnergyRangeChange(newValue as [number, number])}
            valueLabelDisplay="auto"
            min={0}
            max={1}
            step={0.01}
            valueLabelFormat={(value) => `${Math.round(value * 100)}%`}
            sx={{ mt: 1 }}
          />
        </Box>
        
        {/* Active Filters */}
        {(selectedMood || selectedKey || searchQuery) && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Aktive Filter:
            </Typography>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
              {searchQuery && (
                <Chip
                  label={`Suche: "${searchQuery}"`}
                  onDelete={() => onSearchChange('')}
                  size="small"
                />
              )}
              {selectedMood && (
                <Chip
                  label={`Stimmung: ${formatMood(selectedMood)}`}
                  onDelete={() => onMoodChange('')}
                  size="small"
                />
              )}
              {selectedKey && (
                <Chip
                  label={`Key: ${selectedKey}`}
                  onDelete={() => onKeyChange('')}
                  size="small"
                />
              )}
            </Stack>
          </Box>
        )}
      </Stack>
    </Paper>
  );
};

export default FilterPanel;