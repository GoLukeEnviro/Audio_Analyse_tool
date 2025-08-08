import { useQuery, useMutation } from '@tanstack/react-query';
import { PlaylistGenerationResponse } from '../types/interfaces';
import { ExportFormat } from '../types/enums';

const API_BASE_URL = 'http://localhost:8000/api';

export const usePlaylistGenerationStatusQuery = (taskId: string, refetchInterval: number = 2000) => {
  return useQuery({
    queryKey: ['playlist-generation-status', taskId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/playlists/generate/${taskId}/status`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Playlist generation task not found');
        }
        throw new Error(`Failed to fetch playlist generation status: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!taskId,
    refetchInterval: refetchInterval,
    staleTime: 0, // Always refetch for real-time updates
    retry: 1,
  });
};

export const usePlaylistGenerationResultQuery = (taskId: string) => {
  return useQuery({
    queryKey: ['playlist-generation-result', taskId],
    queryFn: async (): Promise<PlaylistGenerationResponse> => {
      const response = await fetch(`${API_BASE_URL}/playlists/generate/${taskId}/result`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Playlist generation result not found');
        }
        if (response.status === 202) {
          throw new Error('Playlist generation still in progress');
        }
        throw new Error(`Failed to fetch playlist generation result: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!taskId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
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
      const response = await fetch(`${API_BASE_URL}/playlists/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to generate playlist: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
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
      const response = await fetch(`${API_BASE_URL}/playlists/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to export playlist: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
  });
};

export const usePlaylistPresetsQuery = () => {
  return useQuery({
    queryKey: ['playlist-presets'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/playlists/presets`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch playlist presets: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
};

export const usePlaylistAlgorithmsQuery = () => {
  return useQuery({
    queryKey: ['playlist-algorithms'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/playlists/algorithms`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch playlist algorithms: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
    retry: 1,
  });
};

export const useValidateTracksForPlaylistQuery = (trackPaths: string[]) => {
  return useQuery({
    queryKey: ['validate-tracks-playlist', trackPaths],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/playlists/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trackPaths),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to validate tracks for playlist: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: trackPaths.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
};