import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Axios client mapping versioned API calls
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Helper setting authorization header dynamically
export const setAuthToken = (token: string | null) => {
  if (token) {
    apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common["Authorization"];
  }
};

// WebSocket run connection factory
export const connectToRunWS = (runId: string, onMessage: (event: any) => void): WebSocket => {
  const wsPrefix = API_BASE_URL.startsWith("https://") ? "wss://" : "ws://";
  const cleanHost = API_BASE_URL.replace("https://", "").replace("http://", "");
  const wsUrl = `${wsPrefix}${cleanHost}/api/ws/runs/${runId}`;

  const socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      console.error("Error parsing WebSocket event payload:", err);
    }
  };

  socket.onerror = (err) => {
    console.error("WebSocket run trace connection error:", err);
  };

  return socket;
};
