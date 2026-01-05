export enum TaskStatus {
    PENDING = "pending",
    IN_PROGRESS = "in_progress",
    COMPLETED = "completed",
    FAILED = "failed",
    SKIPPED = "skipped"
}

export enum AgentType {
    MASTER = "master",
    WORKER = "worker"
}

export interface NewsTask {
    id: string;
    title: string;
    description: string;
    status: TaskStatus;
    agent_type: AgentType;
    result?: string;
}

export interface NewsPlan {
    tasks: NewsTask[];
}

export interface SentimentResult {
    ticker: string;
    sentiment: string;
    trend: "up" | "down" | "neutral";
    title: string;
    summary: string;
}

// Event Types matching backend schemas.py
export enum EventType {
    PLAN_UPDATE = "plan_update",
    TASK_UPDATE = "task_update",
    CONCLUSION = "conclusion",
    ERROR = "error"
}

export type PlanUpdatePayload = NewsPlan;

export interface TaskUpdatePayload {
    task_id: string;
    type: 'thought' | 'tool_call' | 'tool_result' | 'output';
    content: string;
    tool_name?: string;
    tool_input?: string;
    tool_output?: string;
    timestamp: number;
}

export type ConclusionPayload = SentimentResult;

// Unified Event Interface
export interface AgentEvent {
    type: EventType;
    payload: PlanUpdatePayload | TaskUpdatePayload | ConclusionPayload | string;
}
