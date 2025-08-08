import { useEffect, useRef } from 'react';

const useHeartbeat = () => {
  const ws = useRef<WebSocket | null>(null);
  const intervalId = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // WebSocket-Verbindung aufbauen
    ws.current = new WebSocket('ws://localhost:8000/ws/health');

    ws.current.onopen = () => {
      console.log('Heartbeat WebSocket verbunden.');
      // Starte das Senden von Pings
      intervalId.current = setInterval(() => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send('ping');
        }
      }, 5000); // Alle 5 Sekunden einen Ping senden
    };

    ws.current.onmessage = (event) => {
      // Optional: Backend könnte hier auch eine Antwort senden
      // console.log('Heartbeat Pong:', event.data);
    };

    ws.current.onclose = () => {
      console.log('Heartbeat WebSocket getrennt.');
      if (intervalId.current) {
        clearInterval(intervalId.current);
      }
    };

    ws.current.onerror = (error) => {
      console.error('Heartbeat WebSocket Fehler:', error);
      if (intervalId.current) {
        clearInterval(intervalId.current);
      }
    };

    // Cleanup-Funktion: WebSocket schließen und Interval löschen
    return () => {
      if (intervalId.current) {
        clearInterval(intervalId.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []); // Leeres Array, damit der Effekt nur einmal beim Mounten läuft
};

export default useHeartbeat;