// Visual DJ Analysis Studio - Dark Theme Configuration
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#007BFF',
      light: '#4DA3FF', 
      dark: '#0056CC',
      contrastText: '#FFFFFF'
    },
    secondary: {
      main: '#6C757D',
      light: '#ADB5BD',
      dark: '#495057',
      contrastText: '#FFFFFF'
    },
    background: {
      default: '#121212',
      paper: '#1E1E1E'
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#B3B3B3',
      disabled: '#666666'
    },
    success: {
      main: '#28A745',
      light: '#5CBB74',
      dark: '#1E7E34',
      contrastText: '#FFFFFF'
    },
    warning: {
      main: '#FFC107',
      light: '#FFD54F',
      dark: '#F57C00',
      contrastText: '#000000'
    },
    error: {
      main: '#DC3545',
      light: '#E57373',
      dark: '#C62828',
      contrastText: '#FFFFFF'
    },
    info: {
      main: '#17A2B8',
      light: '#4FC3F7',
      dark: '#0288D1',
      contrastText: '#FFFFFF'
    },
    grey: {
      50: '#FAFAFA',
      100: '#F5F5F5',
      200: '#EEEEEE',
      300: '#E0E0E0',
      400: '#BDBDBD',
      500: '#9E9E9E',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121'
    },
    divider: '#2C2C2C'
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
      lineHeight: 1.4
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.5
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      textTransform: 'none'
    }
  },
  shape: {
    borderRadius: 8
  },
  shadows: [
    'none',
    '0px 1px 3px rgba(0, 0, 0, 0.2)',
    '0px 2px 6px rgba(0, 0, 0, 0.15)',
    '0px 3px 12px rgba(0, 0, 0, 0.1)',
    '0px 4px 16px rgba(0, 0, 0, 0.1)',
    '0px 6px 20px rgba(0, 0, 0, 0.1)',
    '0px 8px 24px rgba(0, 0, 0, 0.1)',
    '0px 12px 28px rgba(0, 0, 0, 0.1)',
    '0px 16px 32px rgba(0, 0, 0, 0.1)',
    '0px 20px 36px rgba(0, 0, 0, 0.1)',
    '0px 24px 40px rgba(0, 0, 0, 0.1)',
    '0px 28px 44px rgba(0, 0, 0, 0.1)',
    '0px 32px 48px rgba(0, 0, 0, 0.1)',
    '0px 36px 52px rgba(0, 0, 0, 0.1)',
    '0px 40px 56px rgba(0, 0, 0, 0.1)',
    '0px 44px 60px rgba(0, 0, 0, 0.1)',
    '0px 48px 64px rgba(0, 0, 0, 0.1)',
    '0px 52px 68px rgba(0, 0, 0, 0.1)',
    '0px 56px 72px rgba(0, 0, 0, 0.1)',
    '0px 60px 76px rgba(0, 0, 0, 0.1)',
    '0px 64px 80px rgba(0, 0, 0, 0.1)',
    '0px 68px 84px rgba(0, 0, 0, 0.1)',
    '0px 72px 88px rgba(0, 0, 0, 0.1)',
    '0px 76px 92px rgba(0, 0, 0, 0.1)',
    '0px 80px 96px rgba(0, 0, 0, 0.1)'
  ]
});

export default theme;