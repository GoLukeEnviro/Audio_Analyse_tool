import { AnalysisStatus, MoodCategory, NavigationPage } from '../types/enums';

// Mock data for Visual DJ Analysis Studio

// Data for global state store
export const mockStore = {
  currentUser: {
    id: "user-1",
    name: "DJ Max",
    preferences: {
      theme: "dark" as const,
      defaultView: "library" as const
    }
  },
  analysisSettings: {
    enableMultiprocessing: true,
    cacheDir: "/cache/audio",
    supportedFormats: [".mp3", ".wav", ".flac", ".m4a", ".aiff"]
  }
};

// Data returned by API queries
export const mockQuery = {
  tracks: [
    {
      file_path: "/music/track1.mp3",
      filename: "Avicii - Wake Me Up.mp3",
      title: "Wake Me Up",
      artist: "Avicii",
      album: "True",
      duration: 247,
      bpm: 124,
      key: "B Minor",
      camelot: "10A",
      energy: 0.85,
      mood: "energetic" as const,
      analyzed_at: 1703097600000
    },
    {
      file_path: "/music/track2.mp3", 
      filename: "Deadmau5 - Strobe.mp3",
      title: "Strobe",
      artist: "Deadmau5",
      album: "For Lack of a Better Name",
      duration: 636,
      bpm: 128,
      key: "C# Minor", 
      camelot: "4A",
      energy: 0.72,
      mood: "calm" as const,
      analyzed_at: 1703097700000
    },
    {
      file_path: "/music/track3.mp3",
      filename: "Swedish House Mafia - Don't You Worry Child.mp3", 
      title: "Don't You Worry Child",
      artist: "Swedish House Mafia",
      album: "Until Now",
      duration: 351,
      bpm: 129,
      key: "B Major",
      camelot: "1B", 
      energy: 0.91,
      mood: "happy" as const,
      analyzed_at: 1703097800000
    }
  ],
  analysisStatus: {
    task_id: "analysis_20241220_143022_1",
    status: "running" as const,
    progress: 65.5,
    current_file: "Tiësto - Adagio for Strings.mp3",
    processed_files: 13,
    total_files: 20,
    estimated_completion: "2024-12-20T14:35:00Z"
  },
  playlistGeneration: {
    task_id: "playlist_20241220_143500_1", 
    status: "completed" as const,
    progress: 100,
    result: {
      playlist_id: "generated-playlist-1",
      tracks: [
        {
          file_path: "/music/track1.mp3",
          title: "Wake Me Up",
          artist: "Avicii",
          energy_timeline: [0.3, 0.5, 0.8, 0.9, 0.7, 0.4]
        },
        {
          file_path: "/music/track2.mp3",
          title: "Strobe", 
          artist: "Deadmau5",
          energy_timeline: [0.2, 0.4, 0.6, 0.8, 0.9, 0.5]
        }
      ],
      metadata: {
        total_duration: 1234,
        average_bpm: 126,
        energy_curve: [0.3, 0.6, 0.9, 0.7, 0.4],
        generated_at: "2024-12-20T14:35:00Z"
      }
    }
  },
  trackDetails: {
    file_path: "/music/track1.mp3",
    filename: "Avicii - Wake Me Up.mp3",
    metadata: {
      title: "Wake Me Up",
      artist: "Avicii", 
      album: "True",
      duration: 247,
      file_size: 9876543,
      format: "MP3",
      bitrate: 320,
      analyzed_at: 1703097600000
    },
    features: {
      bpm: 124.2,
      energy: 0.847,
      valence: 0.723,
      danceability: 0.891,
      acousticness: 0.123,
      instrumentalness: 0.045
    },
    camelot: {
      key: "B Minor",
      camelot: "10A",
      compatible_keys: ["10B", "9A", "11A"]
    },
    time_series_features: {
      energy_value: [0.3, 0.4, 0.6, 0.8, 0.9, 0.8, 0.7, 0.5, 0.4],
      timestamps: [0, 27, 54, 81, 108, 135, 162, 189, 216, 247]
    },
    mood: {
      primary_mood: "energetic" as const,
      confidence: 0.87,
      scores: {
        energetic: 0.87,
        happy: 0.65,
        calm: 0.23,
        melancholic: 0.12,
        aggressive: 0.34,
        neutral: 0.18
      }
    }
  }
};

// Data passed as props to the root component  
export const mockRootProps = {
  initialPage: "library" as const,
  apiBaseUrl: "http://localhost:8000/api",
  enableRealTimeUpdates: true
};