import React, { useState } from 'react';
import {
  Typography,
  Stack,
  Box,
  Pagination
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTracksQuery } from '../hooks/useTracksQuery';
import { MoodCategory } from '../types/enums';
import FilterPanel from '../components/tracks/FilterPanel';
import TrackCard from '../components/tracks/TrackCard';
import LoadingSkeleton from '../components/common/LoadingSkeleton';

const Library: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMood, setSelectedMood] = useState<MoodCategory | ''>('');
  const [bpmRange, setBpmRange] = useState<[number, number]>([60, 200]);
  const [energyRange, setEnergyRange] = useState<[number, number]>([0, 1]);
  const [selectedKey, setSelectedKey] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const { data: tracksData, isLoading, isError } = useTracksQuery({
    page: currentPage,
    per_page: 20,
    search: searchQuery || undefined,
    mood: selectedMood || undefined,
    min_bpm: bpmRange[0],
    max_bpm: bpmRange[1],
    min_energy: energyRange[0],
    max_energy: energyRange[1],
    camelot: selectedKey || undefined
  });

  const handleTrackClick = (trackPath: string) => {
    navigate(`/tracks/${encodeURIComponent(trackPath)}`);
  };

  const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
  };

  if (isLoading) {
    return <LoadingSkeleton variant="track-list" count={10} />;
  }

  if (isError) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">
          Fehler beim Laden der Tracks. Bitte versuchen Sie es erneut.
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Bibliothek
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Durchsuchen und filtern Sie Ihre Musiksammlung
        </Typography>
      </Box>

      <FilterPanel
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedMood={selectedMood}
        onMoodChange={setSelectedMood}
        bpmRange={bpmRange}
        onBpmRangeChange={setBpmRange}
        energyRange={energyRange}
        onEnergyRangeChange={setEnergyRange}
        selectedKey={selectedKey}
        onKeyChange={setSelectedKey}
      />

      <Box>
        <Typography variant="h6" gutterBottom>
          {tracksData?.total_count || 0} Tracks gefunden
        </Typography>
        
        <Stack spacing={2}>
          {tracksData?.tracks.map((track) => (
            <TrackCard
              key={track.file_path}
              track={track}
              onClick={() => handleTrackClick(track.file_path)}
            />
          ))}
        </Stack>

        {tracksData && tracksData.total_pages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Pagination
              count={tracksData.total_pages}
              page={currentPage}
              onChange={handlePageChange}
              color="primary"
              size="large"
            />
          </Box>
        )}
      </Box>
    </Stack>
  );
};

export default Library;