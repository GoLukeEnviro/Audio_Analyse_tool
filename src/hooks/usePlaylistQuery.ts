import { useQuery, useMutation } from '@tanstack/react-query';
import { PlaylistGenerationResponse } from '../types/interfaces';
import { ExportFormat } from '../types/enums';
import { mockQuery } from '../data/visualDJStudioMockData';

export const usePlaylistGenerationStatusQuery = (taskId: string, refetchInterval: number = 2000) => {
  return useQuery({
    queryKey: ['playlist-generation-status', taskId],
    queryFn: async () => {
      // In a real app, this would make an API call
      // For now, return mock data
      return mockQuery.playlistGeneration;
    },
    enabled: !!taskId,
    refetchInterval: refetchInterval,
    staleTime: 0, // Always refetch for real-time updates
  });
};

export const useGeneratePlaylistMutation = () => {
  return useMutation({
    mutationFn: async (params: {
      track_file_paths: string[];
      preset_name?: string;
      custom_rules?: any[];
      target_duration_minutes?: number;
    }) => {
      // In a real app, this would make an API call
      // For now, return mock response
      return {
        task_id: `playlist_${Date.now()}`,
        status: 'started',
        message: 'Playlist generation started',
        valid_tracks_count: params.track_file_paths.length
      };
    },
  });
};

export const useExportPlaylistMutation = () => {
  return useMutation({
    mutationFn: async (params: {
      playlist_data: any;
      format_type: ExportFormat;
      filename: string;
      include_metadata?: boolean;
    }) => {
      // In a real app, this would make an API call and trigger download
      // For now, return mock response
      return {
        success: true,
        output_path: `/exports/${params.filename}`,
        filename: params.filename,
        format_type: params.format_type,
        track_count: params.playlist_data?.tracks?.length || 0,
        file_size_bytes: 1024,
        error: undefined
      };
    },
  });
};