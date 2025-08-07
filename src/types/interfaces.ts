import { NavigationPage, AnalysisStatus, MoodCategory, PlaylistGenerationStatus, ExportFormat } from './enums';

// Props types (data passed to components)
export interface AppRootProps {
  initialPage: NavigationPage;
  apiBaseUrl: string;
  enableRealTimeUpdates: boolean;
}

export interface TrackSummary {
  file_path: string;
  filename: string;
  title?: string;
  artist?: string;
  duration: number;
  bpm: number;
  key: string;
  camelot: string;
  energy: number;
  mood?: MoodCategory;
  analyzed_at: number;
}

export interface TrackDetails {
  file_path: string;
  filename: string;
  metadata: {
    title?: string;
    artist?: string;
    album?: string;
    duration: number;
    file_size: number;
    format: string;
    bitrate?: number;
    analyzed_at: number;
  };
  features: {
    bpm: number;
    energy: number;
    valence: number;
    danceability: number;
    acousticness: number;
    instrumentalness: number;
  };
  camelot: {
    key: string;
    camelot: string;
    compatible_keys: string[];
  };
  time_series_features: {
    energy_value: number[];
    timestamps: number[];
  };
  mood: {
    primary_mood: MoodCategory;
    confidence: number;
    scores: Record<string, number>;
  };
}

// Store types (global state data)
export interface UserPreferences {
  theme: 'light' | 'dark';
  defaultView: NavigationPage;
}

export interface CurrentUser {
  id: string;
  name: string;
  preferences: UserPreferences;
}

export interface AnalysisSettings {
  enableMultiprocessing: boolean;
  cacheDir: string;
  supportedFormats: string[];
}

export interface GlobalStore {
  currentUser: CurrentUser;
  analysisSettings: AnalysisSettings;
}

// Query types (API response data)
export interface TracksListResponse {
  tracks: TrackSummary[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface AnalysisStatusResponse {
  task_id: string;
  status: AnalysisStatus;
  progress: number;
  current_file?: string;
  processed_files: number;
  total_files: number;
  estimated_completion?: string;
}

export interface PlaylistGenerationResponse {
  success: boolean;
  playlist?: {
    playlist_id: string;
    tracks: Array<{
      file_path: string;
      title?: string;
      artist?: string;
      energy_timeline: number[];
    }>;
    metadata: {
      total_duration: number;
      average_bpm: number;
      energy_curve: number[];
      generated_at: string;
    };
  };
  error?: string;
  generation_time_seconds: number;
}

// Root component props interface for Visual DJ Analysis Studio
export interface AppProps {
  // Initial application state
  initialPage?: NavigationPage;
  
  // API configuration
  apiBaseUrl?: string;
  
  // Feature flags
  enableRealTimeUpdates?: boolean;
  enableAnalysisPolling?: boolean;
  
  // Theme and UI preferences
  defaultTheme?: 'light' | 'dark';
  
  // Development/debugging options
  debugMode?: boolean;
  mockDataMode?: boolean;
}

// Default props for the root component
export const defaultAppProps: Required<AppProps> = {
  initialPage: NavigationPage.LIBRARY,
  apiBaseUrl: 'http://localhost:8000/api',
  enableRealTimeUpdates: true,
  enableAnalysisPolling: true,
  defaultTheme: 'dark',
  debugMode: false,
  mockDataMode: false
};