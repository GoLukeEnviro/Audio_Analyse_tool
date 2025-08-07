import { AnalysisStatus, MoodCategory } from '../types/enums';

// Date and time formatting utilities
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

export const formatFileSize = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
};

export const formatBPM = (bpm: number): string => {
  return `${Math.round(bpm)} BPM`;
};

export const formatEnergy = (energy: number): string => {
  return `${(energy * 100).toFixed(1)}%`;
};

export const formatProgress = (progress: number): string => {
  return `${Math.round(progress)}%`;
};

export const formatAnalysisStatus = (status: AnalysisStatus): string => {
  const statusMap = {
    [AnalysisStatus.PENDING]: 'Wartend',
    [AnalysisStatus.RUNNING]: 'Läuft',
    [AnalysisStatus.COMPLETED]: 'Abgeschlossen',
    [AnalysisStatus.ERROR]: 'Fehler',
    [AnalysisStatus.CANCELLED]: 'Abgebrochen'
  };
  return statusMap[status] || status;
};

export const formatMood = (mood: MoodCategory): string => {
  const moodMap = {
    [MoodCategory.ENERGETIC]: 'Energetisch',
    [MoodCategory.HAPPY]: 'Fröhlich', 
    [MoodCategory.CALM]: 'Ruhig',
    [MoodCategory.MELANCHOLIC]: 'Melancholisch',
    [MoodCategory.AGGRESSIVE]: 'Aggressiv',
    [MoodCategory.NEUTRAL]: 'Neutral'
  };
  return moodMap[mood] || mood;
};