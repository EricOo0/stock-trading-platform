
export interface Transaction {
    date: string;
    action: 'BUY' | 'SELL';
    price: number;
    quantity: number;
    amount: number;
    reason: string;
}

export interface Analysis {
    technical_score: number;
    fundamental_score: number;
    sentiment_score: number;
    macro_score: number;
    reasoning: string;
}

export interface DailyRecord {
    date: string;
    price: number;
    holdings: number;
    cash: number;
    total_value: number;
    avg_cost?: number;
    unrealized_pl?: number;
    quantity?: number; // Added quantity
    action_taken: string;
    reason: string;
    analysis?: Analysis; // Optional detailed analysis
}

export interface SimulationTask {
    id: string;
    symbol: string;
    created_at: string;
    initial_capital: number;
    current_cash: number;
    holdings: number;
    total_value: number;
    avg_cost?: number; // Current average cost
    transactions: Transaction[];
    daily_records: DailyRecord[];
    status: string;
}

export interface SimulationResponse<T> {
    status: 'success' | 'error';
    data?: T;
    message?: string;
}

class SimulationAPIService {
    private baseURL = 'http://localhost:8000/api/simulation';

    async getAllTasks(): Promise<SimulationTask[]> {
        try {
            const response = await fetch(`${this.baseURL}/tasks`);
            const result = await response.json();
            if (result.status === 'success') {
                return result.data;
            }
            return [];
        } catch (error) {
            console.error('Failed to fetch simulation tasks:', error);
            return [];
        }
    }

    async getTask(taskId: string): Promise<SimulationTask | null> {
        try {
            const response = await fetch(`${this.baseURL}/task/${taskId}`);
            const result = await response.json();
            if (result.status === 'success') {
                return result.data;
            }
            return null;
        } catch (error) {
            console.error(`Failed to fetch task ${taskId}:`, error);
            return null;
        }
    }

    async createTask(symbol: string): Promise<SimulationTask | null> {
        try {
            const response = await fetch(`${this.baseURL}/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol })
            });
            const result = await response.json();
            if (result.status === 'success') {
                return result.data;
            }
            return null;
        } catch (error) {
            console.error('Failed to create simulation task:', error);
            return null;
        }
    }

    async runDailySimulation(taskId: string): Promise<any> {
        try {
            const response = await fetch(`${this.baseURL}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: taskId })
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to run simulation:', error);
            return { status: 'error', message: 'Network error' };
        }
    }
}

export const simulationAPI = new SimulationAPIService();
