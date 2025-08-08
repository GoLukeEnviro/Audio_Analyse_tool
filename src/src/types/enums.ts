// Audio analysis and playlist generation enums
export enum AnalysisStatus {
  PENDING = 'pending',
  RUNNING = 'running', 
  COMPLETED = 'completed',
  ERROR = 'error',
  CANCELLED = 'cancelled'
}

export enum MoodCategory {
  ENERGETIC = 'energetic',
  HAPPY = 'happy',
  CALM = 'calm',
  MELANCHOLIC = 'melancholic',
  AGGRESSIVE = 'aggressive',
  NEUTRAL = 'neutral'
}

export enum SortingAlgorithm {
  HYBRID_SMART = 'hybrid_smart',
  BPM_PROGRESSION = 'bpm_progression',
  ENERGY_FLOW = 'energy_flow',
  HARMONIC_MIXING = 'harmonic_mixing',
  MOOD_JOURNEY = 'mood_journey'
}

export enum ExportFormat {
  M3U = 'm3u',
  JSON = 'json', 
  CSV = 'csv',
  REKORDBOX = 'rekordbox'
}

export enum PlaylistGenerationStatus {
  LOADING_TRACKS = 'loading_tracks',
  GENERATING = 'generating',
  COMPLETED = 'completed',
  ERROR = 'error'
}

export enum NavigationPage {
  DASHBOARD = 'dashboard',
  LIBRARY = 'library',
  CREATOR_STUDIO = 'creator-studio',
  ANALYSIS_CENTER = 'analysis-center', 
  SETTINGS = 'settings'
}