import React from 'react';
import { Button, Badge } from '@mui/material';
import ClearAllIcon from '@mui/icons-material/ClearAll';
import { MoodCategory } from '../../types/enums';

interface ResetFiltersButtonProps {
  searchQuery: string;
  selectedMood: MoodCategory | '';
  selectedKey: string;
  bpmRange: [number, number];
  energyRange: [number, number];
  onReset: () => void;
}

const DEFAULT_BPM_RANGE: [number, number] = [60, 200];
const DEFAULT_ENERGY_RANGE: [number, number] = [0, 1];

const ResetFiltersButton: React.FC<ResetFiltersButtonProps> = ({
  searchQuery,
  selectedMood,
  selectedKey,
  bpmRange,
  energyRange,
  onReset
}) => {
  // Check if any filters are active (different from defaults)
  const hasActiveFilters = 
    searchQuery.trim() !== '' ||
    selectedMood !== '' ||
    selectedKey !== '' ||
    bpmRange[0] !== DEFAULT_BPM_RANGE[0] ||
    bpmRange[1] !== DEFAULT_BPM_RANGE[1] ||
    energyRange[0] !== DEFAULT_ENERGY_RANGE[0] ||
    energyRange[1] !== DEFAULT_ENERGY_RANGE[1];

  // Count active filters
  let activeFilterCount = 0;
  if (searchQuery.trim() !== '') activeFilterCount++;
  if (selectedMood !== '') activeFilterCount++;
  if (selectedKey !== '') activeFilterCount++;
  if (bpmRange[0] !== DEFAULT_BPM_RANGE[0] || bpmRange[1] !== DEFAULT_BPM_RANGE[1]) activeFilterCount++;
  if (energyRange[0] !== DEFAULT_ENERGY_RANGE[0] || energyRange[1] !== DEFAULT_ENERGY_RANGE[1]) activeFilterCount++;

  return (
    <Badge 
      badgeContent={activeFilterCount} 
      color="primary" 
      invisible={!hasActiveFilters}
      sx={{
        '& .MuiBadge-badge': {
          right: -3,
          top: 3,
        }
      }}
    >
      <Button
        variant="outlined"
        size="small"
        startIcon={<ClearAllIcon />}
        onClick={onReset}
        disabled={!hasActiveFilters}
        sx={{
          color: hasActiveFilters ? 'primary.main' : 'text.disabled',
          borderColor: hasActiveFilters ? 'primary.main' : 'divider',
        }}
      >
        Filter zurücksetzen
      </Button>
    </Badge>
  );
};

export default ResetFiltersButton;