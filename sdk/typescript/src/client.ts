import axios, { AxiosInstance } from "axios";
import WebSocket from "ws";

export class NeuroMeshClient {
  private baseUrl: string;
  private wsUrl: string;
  private http: AxiosInstance;

  constructor(baseUrl: string = "http://localhost:8000", token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    
    // WebSocket url conversion
    const wsPrefix = this.baseUrl.startsWith("https://") ? "wss://" : "ws://";
    const cleanHost = this.baseUrl.replace("https://", "").replace("http://", "");
    this.wsUrl = `${wsPrefix}${cleanHost}/api/ws`;

    this.http = axios.create({
      baseURL: `${this.baseUrl}/api/v1`,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  }

  public async createWorkflow(name: string, definition: any): Promise<any> {
    const response = await this.http.post("/workflows/", { name, definition });
    return response.data;
  }

  public async runWorkflow(workflowId: string, idempotencyKey?: string): Promise<any> {
    const headers = idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {};
    const response = await this.http.post(`/workflows/${workflowId}/run`, {}, { headers });
    return response.data;
  }

  public async approveStep(runId: string, stepId: string, approvalData: any): Promise<any> {
    const response = await this.http.post(`/workflows/runs/${runId}/steps/${stepId}/approve`, {
      approval_data: approvalData,
    });
    return response.data;
  }

  public subscribeRunTraces(runId: string, callback: (event: any) => void): WebSocket {
    const socket = new WebSocket(`${this.wsUrl}/runs/${runId}`);

    socket.on("message", (data: WebSocket.Data) => {
      try {
        const parsed = JSON.parse(data.toString());
        callback(parsed);
      } catch (err) {
        console.error("Failed to parse WebSocket trace message:", err);
      }
    });

    socket.on("error", (err) => {
      console.error("WebSocket trace stream error:", err);
    });

    return socket;
  }
}
