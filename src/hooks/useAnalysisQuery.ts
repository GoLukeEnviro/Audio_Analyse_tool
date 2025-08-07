import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AnalysisStatusResponse } from '../types/interfaces';

const API_BASE_URL = 'http://localhost:8000/api';

export const useAnalysisStatusQuery = (taskId: string, refetchInterval: number = 2000) => {
  return useQuery({
    queryKey: ['analysis-status', taskId],
    queryFn: async (): Promise<AnalysisStatusResponse> => {
      const response = await fetch(`${API_BASE_URL}/analysis/${taskId}/status`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Analysis task not found');
        }
        throw new Error(`Failed to fetch analysis status: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!taskId,
    refetchInterval: refetchInterval,
    staleTime: 0, // Always refetch for real-time updates
    retry: 1,
  });
};

export const useStartAnalysisMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (params: {
      directories?: string[];
      file_paths?: string[];
      recursive?: boolean;
      overwrite_cache?: boolean;
      include_patterns?: string[];
      exclude_patterns?: string[];
    }) => {
      const response = await fetch(`${API_BASE_URL}/analysis/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to start analysis: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    onSuccess: () => {
      // Invalidate tracks queries to refresh data after analysis
      queryClient.invalidateQueries({ queryKey: ['tracks'] });
      queryClient.invalidateQueries({ queryKey: ['tracks-stats'] });
    },
  });
};

export const useCancelAnalysisMutation = () => {
  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await fetch(`${API_BASE_URL}/analysis/${taskId}/cancel`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to cancel analysis: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
  });
};

export const useAnalysisStatsQuery = (options: { refetchInterval?: number } = {}) => {
  return useQuery({
    queryKey: ['analysis-stats'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/analysis/stats`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch analysis statistics: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    staleTime: 30 * 1000, // 30 seconds
    retry: 1,
    refetchInterval: options.refetchInterval,
    enabled: true, // Always enabled
  });
};

export const useValidateDirectoryQuery = (directory: string, recursive: boolean = true) => {
  return useQuery({
    queryKey: ['validate-directory', directory, recursive],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append('directory', directory);
      searchParams.append('recursive', recursive.toString());
      
      const response = await fetch(`${API_BASE_URL}/analysis/validate/directory?${searchParams}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to validate directory: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!directory,
    staleTime: 60 * 1000, // 1 minute
    retry: 1,
  });
};