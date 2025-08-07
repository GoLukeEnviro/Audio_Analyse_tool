import { useQuery, useMutation } from '@tanstack/react-query';
import { AnalysisStatusResponse } from '../types/interfaces';
import { mockQuery } from '../data/visualDJStudioMockData';

export const useAnalysisStatusQuery = (taskId: string, refetchInterval: number = 2000) => {
  return useQuery({
    queryKey: ['analysis-status', taskId],
    queryFn: async (): Promise<AnalysisStatusResponse> => {
      // In a real app, this would make an API call
      // For now, return mock data
      return mockQuery.analysisStatus;
    },
    enabled: !!taskId,
    refetchInterval: refetchInterval,
    staleTime: 0, // Always refetch for real-time updates
  });
};

export const useStartAnalysisMutation = () => {
  return useMutation({
    mutationFn: async (params: {
      directories?: string[];
      file_paths?: string[];
      recursive?: boolean;
      overwrite_cache?: boolean;
    }) => {
      // In a real app, this would make an API call
      // For now, return mock response
      return {
        task_id: `analysis_${Date.now()}`,
        status: 'started',
        message: 'Audio analysis started',
        total_files: 20
      };
    },
  });
};

export const useCancelAnalysisMutation = () => {
  return useMutation({
    mutationFn: async (taskId: string) => {
      // In a real app, this would make an API call
      // For now, return mock response
      return {
        message: `Analysis task ${taskId} cancelled`
      };
    },
  });
};