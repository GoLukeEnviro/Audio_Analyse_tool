import { useQuery } from '@tanstack/react-query';
import { TracksListResponse, TrackDetails } from '../types/interfaces';
import { MoodCategory } from '../types/enums';
import { mockQuery } from '../data/visualDJStudioMockData';

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
      // In a real app, this would make an API call
      // For now, return mock data
      return {
        tracks: mockQuery.tracks,
        total_count: mockQuery.tracks.length,
        page: params.page || 1,
        per_page: params.per_page || 50,
        total_pages: 1,
        has_next: false,
        has_prev: false
      };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useTrackDetailsQuery = (trackId: string, includeTimeSeries: boolean = true) => {
  return useQuery({
    queryKey: ['track-details', trackId, includeTimeSeries],
    queryFn: async (): Promise<TrackDetails> => {
      // In a real app, this would make an API call
      // For now, return mock data
      return mockQuery.trackDetails as TrackDetails;
    },
    enabled: !!trackId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useSimilarTracksQuery = (trackPath: string, limit: number = 10, threshold: number = 0.7) => {
  return useQuery({
    queryKey: ['similar-tracks', trackPath, limit, threshold],
    queryFn: async (): Promise<TracksListResponse> => {
      // In a real app, this would make an API call
      // For now, return mock data
      return {
        tracks: mockQuery.tracks.slice(0, limit),
        total_count: limit,
        page: 1,
        per_page: limit,
        total_pages: 1,
        has_next: false,
        has_prev: false
      };
    },
    enabled: !!trackPath,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};