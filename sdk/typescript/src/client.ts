import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import WebSocket from "ws";

export class TSWorkflowClient {
  constructor(private client: NeuroMeshClient) {}

  public async create(name: string, definition: any): Promise<any> {
    return this.client.request({
      method: "POST",
      url: "/workflows/",
      data: { name, definition },
    });
  }

  public async run(workflowId: string, idempotencyKey?: string): Promise<any> {
    const headers = idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {};
    return this.client.request({
      method: "POST",
      url: `/workflows/${workflowId}/run`,
      headers,
    });
  }
}

export class TSAgentClient {
  constructor(private client: NeuroMeshClient) {}

  public async list(): Promise<any> {
    return this.client.request({
      method: "GET",
      url: "/agents/",
    });
  }
}

export class TSRunClient {
  constructor(private client: NeuroMeshClient) {}

  public async approveStep(runId: string, stepId: string, approvalData: any): Promise<any> {
    return this.client.request({
      method: "POST",
      url: `/workflows/runs/${runId}/steps/${stepId}/approve`,
      data: { approval_data: approvalData },
    });
  }

  public async getSteps(runId: string): Promise<any> {
    return this.client.request({
      method: "GET",
      url: `/workflows/runs/${runId}/steps`,
    });
  }
}

export class TSSecretsClient {
  constructor(private client: NeuroMeshClient) {}

  public async setSecret(key: string, value: string): Promise<any> {
    return this.client.request({
      method: "POST",
      url: "/secrets/",
      data: { key, value },
    });
  }
}

export class NeuroMeshClient {
  private baseUrl: string;
  private wsUrl: string;
  private http: AxiosInstance;

  public workflows: TSWorkflowClient;
  public agents: TSAgentClient;
  public runs: TSRunClient;
  public secrets: TSSecretsClient;

  constructor(baseUrl: string = "http://localhost:8000", token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    
    const wsPrefix = this.baseUrl.startsWith("https://") ? "wss://" : "ws://";
    const cleanHost = this.baseUrl.replace("https://", "").replace("http://", "");
    this.wsUrl = `${wsPrefix}${cleanHost}/api/ws`;

    this.http = axios.create({
      baseURL: `${this.baseUrl}/api/v1`,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      timeout: 10000,
    });

    this.workflows = new TSWorkflowClient(this);
    this.agents = new TSAgentClient(this);
    this.runs = new TSRunClient(this);
    this.secrets = new TSSecretsClient(this);
  }

  public async request(config: AxiosRequestConfig): Promise<any> {
    const response = await this.http(config);
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
