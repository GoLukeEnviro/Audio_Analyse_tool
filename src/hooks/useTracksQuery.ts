import { useQuery } from '@tanstack/react-query';
import { TracksListResponse, TrackDetails } from '../types/interfaces';
import { MoodCategory } from '../types/enums';

const API_BASE_URL = 'http://localhost:8000/api';

interface TracksQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  key?: string;
  camelot?: string;
  mood?: MoodCategory;
  min_bpm?: number;
  max_bpm?: number;
  min_energy?: number;
  max_energy?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const useTracksQuery = (params: TracksQueryParams = {}) => {
  return useQuery({
    queryKey: ['tracks', params],
    queryFn: async (): Promise<TracksListResponse> => {
      const searchParams = new URLSearchParams();
      
      // Always add default page and per_page to avoid empty params
      searchParams.append('page', (params.page || 1).toString());
      searchParams.append('per_page', (params.per_page || 50).toString());
      
      if (params.search) searchParams.append('search', params.search);
      if (params.key) searchParams.append('key', params.key);
      if (params.camelot) searchParams.append('camelot', params.camelot);
      if (params.mood) searchParams.append('mood', params.mood);
      if (params.min_bpm !== undefined) searchParams.append('min_bpm', params.min_bpm.toString());
      if (params.max_bpm !== undefined) searchParams.append('max_bpm', params.max_bpm.toString());
      if (params.min_energy !== undefined) searchParams.append('min_energy', params.min_energy.toString());
      if (params.max_energy !== undefined) searchParams.append('max_energy', params.max_energy.toString());
      if (params.sort_by) searchParams.append('sort_by', params.sort_by);
      if (params.sort_order) searchParams.append('sort_order', params.sort_order);

      const response = await fetch(`${API_BASE_URL}/tracks?${searchParams}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch tracks: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    enabled: true, // Always enabled
  });
};

export const useTrackDetailsQuery = (trackId: string, includeTimeSeries: boolean = true) => {
  return useQuery({
    queryKey: ['track-details', trackId, includeTimeSeries],
    queryFn: async (): Promise<TrackDetails> => {
      const encodedTrackId = encodeURIComponent(trackId);
      const searchParams = new URLSearchParams();
      if (includeTimeSeries) searchParams.append('include_time_series', 'true');
      
      const response = await fetch(`${API_BASE_URL}/tracks/${encodedTrackId}?${searchParams}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Track not found');
        }
        throw new Error(`Failed to fetch track details: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.track;
    },
    enabled: !!trackId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
};

export const useSimilarTracksQuery = (trackPath: string, limit: number = 10, threshold: number = 0.7) => {
  return useQuery({
    queryKey: ['similar-tracks', trackPath, limit, threshold],
    queryFn: async (): Promise<TracksListResponse> => {
      const searchParams = new URLSearchParams();
      searchParams.append('track_path', trackPath);
      searchParams.append('limit', limit.toString());
      searchParams.append('similarity_threshold', threshold.toString());
      
      const response = await fetch(`${API_BASE_URL}/tracks/search/similar?${searchParams}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch similar tracks: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!trackPath,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
};

export const useTracksStatsQuery = (options: { refetchInterval?: number } = {}) => {
  return useQuery({
    queryKey: ['tracks-stats'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/tracks/stats/overview`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch tracks statistics: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    refetchInterval: options.refetchInterval,
    enabled: true, // Always enabled
  });
};