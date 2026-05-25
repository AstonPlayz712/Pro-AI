import Anthropic from '@anthropic-ai/sdk';
import { DAI_SYSTEM_PROMPT } from './daiSystemPrompt';
import { callDAI } from './daiClient';
import {
  loadState,
  updateState,
  loadProjectMemory,
  loadCompanyMemory,
  loadDirectorMemory,
  saveProjectMemory,
  saveCompanyMemory,
  saveDirectorMemory,
  addConversationToHistory,
  updateTaskInGraph,
  updateWorkerLoad,
  DAIState,
  ProjectMemory,
  CompanyMemory,
  DirectorMemory
} from './memory';

export interface DAIResponse {
  director_summary: string;
  request_analysis: {
    type: string;
    complexity: 'simple' | 'moderate' | 'complex';
    required_skills: string[];
  };
  routing_decision: {
    strategy: 'single_worker' | 'parallel' | 'sequential' | 'hybrid';
    assignments: Array<{
      worker_id: string;
      worker_name: string;
      task_description: string;
      priority: 'high' | 'medium' | 'low';
      estimated_duration: string;
    }>;
  };
  task_updates: Array<{
    task_id: string;
    status: 'pending' | 'in_progress' | 'blocked' | 'completed' | 'failed';
    assigned_to: string;
  }>;
  project_status: {
    active_tasks: number;
    completed_tasks: number;
    blocked_tasks: number;
  };
  next_steps: string[];
  director_notes: string;
}

export class DAI {
  private client: Anthropic;
  private systemPrompt: string;
  private state: DAIState | null = null;
  private projectMemory: ProjectMemory | null = null;
  private companyMemory: CompanyMemory | null = null;
  private directorMemory: DirectorMemory | null = null;

  constructor(client: Anthropic, systemPrompt?: string) {
    this.client = client;
    this.systemPrompt = systemPrompt || DAI_SYSTEM_PROMPT;
  }

  async initialize(): Promise<void> {
    this.state = await loadState();
    this.projectMemory = await loadProjectMemory();
    this.companyMemory = await loadCompanyMemory();
    this.directorMemory = await loadDirectorMemory();
  }

  async handle(input: string): Promise<DAIResponse> {
    if (!this.state) {
      await this.initialize();
    }

    const contextEnhancedInput = await this.buildContextEnhancedInput(input);

    const rawResponse = await callDAI(
      contextEnhancedInput,
      this.systemPrompt,
      { apiKey: process.env.ANTHROPIC_API_KEY }
    );

    const response = this.parseResponse(rawResponse);

    await this.processResponse(input, response);

    return response;
  }

  private async buildContextEnhancedInput(userInput: string): Promise<string> {
    const state = this.state!;
    const companyMemory = this.companyMemory!;
    const directorMemory = this.directorMemory!;

    const recentConversations = directorMemory.conversation_history.slice(-5);

    const contextBlock = {
      current_state: {
        active_projects_count: Object.keys(state.active_projects).length,
        task_queue_length: state.task_queue.length,
        completed_tasks_count: state.completed_tasks.length,
        blocked_tasks_count: state.blocked_tasks.length
      },
      worker_availability: Object.entries(state.worker_status).map(([id, worker]) => ({
        worker_id: id,
        status: worker.status,
        load: worker.load,
        capacity: worker.max_capacity
      })),
      recent_context: recentConversations.length > 0
        ? recentConversations.map(conv => ({
            user: conv.user_input.substring(0, 100),
            action: conv.director_response?.director_summary?.substring(0, 100)
          }))
        : []
    };

    return `USER REQUEST: ${userInput}

CURRENT CONTEXT:
${JSON.stringify(contextBlock, null, 2)}

Please analyze this request, make routing decisions, and return your response as pure JSON (no markdown, no text outside JSON).`;
  }

  private parseResponse(rawResponse: string): DAIResponse {
    let jsonText = rawResponse.trim();

    if (jsonText.startsWith('```json')) {
      jsonText = jsonText.replace(/^```json\n?/, '').replace(/\n?```$/, '');
    } else if (jsonText.startsWith('```')) {
      jsonText = jsonText.replace(/^```\n?/, '').replace(/\n?```$/, '');
    }

    const lines = jsonText.split('\n');
    const jsonLines = lines.filter(line => {
      const trimmed = line.trim();
      return trimmed.startsWith('{') || trimmed.startsWith('[') ||
             trimmed.startsWith('"') || trimmed.startsWith('}') ||
             trimmed.startsWith(']') || trimmed.includes(':') ||
             trimmed.includes(',') || trimmed === '';
    });
    jsonText = jsonLines.join('\n').trim();

    const jsonStart = jsonText.indexOf('{');
    if (jsonStart > 0) {
      jsonText = jsonText.substring(jsonStart);
    }

    const jsonEnd = jsonText.lastIndexOf('}');
    if (jsonEnd !== -1 && jsonEnd < jsonText.length - 1) {
      jsonText = jsonText.substring(0, jsonEnd + 1);
    }

    try {
      return JSON.parse(jsonText);
    } catch (error) {
      console.error('Failed to parse DAI response as JSON:', error);
      console.error('Raw response:', rawResponse);
      console.error('Cleaned response:', jsonText);

      return {
        director_summary: 'Error: Could not parse response. Returning fallback.',
        request_analysis: {
          type: 'unknown',
          complexity: 'simple',
          required_skills: []
        },
        routing_decision: {
          strategy: 'single_worker',
          assignments: []
        },
        task_updates: [],
        project_status: {
          active_tasks: this.state?.task_queue.length || 0,
          completed_tasks: this.state?.completed_tasks.length || 0,
          blocked_tasks: this.state?.blocked_tasks.length || 0
        },
        next_steps: ['Retry request with clearer input'],
        director_notes: `Parse error: ${error instanceof Error ? error.message : 'Unknown error'}. Raw response length: ${rawResponse.length}`
      };
    }
  }

  private async processResponse(userInput: string, response: DAIResponse): Promise<void> {
    if (response.task_updates && response.task_updates.length > 0) {
      for (const taskUpdate of response.task_updates) {
        await updateTaskInGraph(taskUpdate.task_id, {
          status: taskUpdate.status,
          assigned_to: taskUpdate.assigned_to
        });

        if (taskUpdate.status === 'in_progress' && taskUpdate.assigned_to) {
          await updateWorkerLoad(taskUpdate.assigned_to, taskUpdate.task_id, 'add');
        } else if (taskUpdate.status === 'completed' && taskUpdate.assigned_to) {
          await updateWorkerLoad(taskUpdate.assigned_to, taskUpdate.task_id, 'remove');
        }
      }
    }

    if (response.routing_decision?.assignments) {
      for (const assignment of response.routing_decision.assignments) {
        const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        await updateTaskInGraph(taskId, {
          type: response.request_analysis.type,
          status: 'in_progress',
          assigned_to: assignment.worker_id,
          priority: assignment.priority,
          metadata: {
            task_description: assignment.task_description,
            estimated_duration: assignment.estimated_duration
          }
        });

        await updateWorkerLoad(assignment.worker_id, taskId, 'add');
      }
    }

    this.state = await loadState();

    await addConversationToHistory(userInput, response);

    await updateState(this.state);
  }

  async getState(): Promise<DAIState> {
    if (!this.state) {
      await this.initialize();
    }
    return this.state!;
  }

  async getProjectMemory(): Promise<ProjectMemory> {
    if (!this.projectMemory) {
      await this.initialize();
    }
    return this.projectMemory!;
  }

  async getCompanyMemory(): Promise<CompanyMemory> {
    if (!this.companyMemory) {
      await this.initialize();
    }
    return this.companyMemory!;
  }

  async getDirectorMemory(): Promise<DirectorMemory> {
    if (!this.directorMemory) {
      await this.initialize();
    }
    return this.directorMemory!;
  }
}
