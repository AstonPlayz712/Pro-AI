import * as fs from 'fs-extra';
import * as path from 'path';

const MEMORY_DIR = path.join(process.cwd(), 'memory');

interface ProjectMemory {
  active_projects: {
    [project_id: string]: {
      name: string;
      status: 'active' | 'paused' | 'completed';
      tasks: string[];
      priority: 'high' | 'medium' | 'low';
      created_at: string;
      updated_at: string;
    };
  };
}

interface CompanyMemory {
  worker_status: {
    [worker_id: string]: {
      status: 'available' | 'busy' | 'offline';
      current_tasks: string[];
      load: number;
      max_capacity: number;
    };
  };
  task_graph: {
    [task_id: string]: {
      task_id: string;
      type: string;
      status: 'pending' | 'in_progress' | 'blocked' | 'completed' | 'failed';
      assigned_to: string | null;
      created_at: string;
      updated_at: string;
      parent_task: string | null;
      child_tasks: string[];
      dependencies: string[];
      priority: 'high' | 'medium' | 'low';
      metadata: Record<string, any>;
    };
  };
}

interface DirectorMemory {
  conversation_history: Array<{
    timestamp: string;
    user_input: string;
    director_response: any;
  }>;
  routing_patterns: Array<{
    request_type: string;
    assigned_workers: string[];
    success: boolean;
    timestamp: string;
  }>;
  user_preferences: Record<string, any>;
}

interface DAIState {
  active_projects: ProjectMemory['active_projects'];
  worker_status: CompanyMemory['worker_status'];
  task_queue: string[];
  completed_tasks: string[];
  blocked_tasks: string[];
}

export async function ensureMemoryDir(): Promise<void> {
  await fs.ensureDir(MEMORY_DIR);
}

export async function readMemory<T>(filename: string, defaultValue: T): Promise<T> {
  await ensureMemoryDir();
  const filepath = path.join(MEMORY_DIR, filename);

  try {
    if (await fs.pathExists(filepath)) {
      const content = await fs.readFile(filepath, 'utf-8');
      return JSON.parse(content);
    }
  } catch (error) {
    console.error(`Error reading memory file ${filename}:`, error);
  }

  return defaultValue;
}

export async function writeMemory<T>(filename: string, data: T): Promise<void> {
  await ensureMemoryDir();
  const filepath = path.join(MEMORY_DIR, filename);

  try {
    await fs.writeFile(filepath, JSON.stringify(data, null, 2), 'utf-8');
  } catch (error) {
    console.error(`Error writing memory file ${filename}:`, error);
    throw error;
  }
}

export async function loadProjectMemory(): Promise<ProjectMemory> {
  return readMemory<ProjectMemory>('project_memory.json', {
    active_projects: {}
  });
}

export async function saveProjectMemory(memory: ProjectMemory): Promise<void> {
  await writeMemory('project_memory.json', memory);
}

export async function loadCompanyMemory(): Promise<CompanyMemory> {
  const defaultWorkers: CompanyMemory['worker_status'] = {
    worker_001: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_002: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_003: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_004: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_005: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_006: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_007: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_008: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 },
    worker_009: { status: 'available', current_tasks: [], load: 0, max_capacity: 5 }
  };

  return readMemory<CompanyMemory>('company_memory.json', {
    worker_status: defaultWorkers,
    task_graph: {}
  });
}

export async function saveCompanyMemory(memory: CompanyMemory): Promise<void> {
  await writeMemory('company_memory.json', memory);
}

export async function loadDirectorMemory(): Promise<DirectorMemory> {
  return readMemory<DirectorMemory>('director_memory.json', {
    conversation_history: [],
    routing_patterns: [],
    user_preferences: {}
  });
}

export async function saveDirectorMemory(memory: DirectorMemory): Promise<void> {
  await writeMemory('director_memory.json', memory);
}

export async function loadState(): Promise<DAIState> {
  const projectMemory = await loadProjectMemory();
  const companyMemory = await loadCompanyMemory();

  const taskQueue: string[] = [];
  const completedTasks: string[] = [];
  const blockedTasks: string[] = [];

  for (const [taskId, task] of Object.entries(companyMemory.task_graph)) {
    if (task.status === 'pending') {
      taskQueue.push(taskId);
    } else if (task.status === 'completed') {
      completedTasks.push(taskId);
    } else if (task.status === 'blocked') {
      blockedTasks.push(taskId);
    }
  }

  return {
    active_projects: projectMemory.active_projects,
    worker_status: companyMemory.worker_status,
    task_queue: taskQueue,
    completed_tasks: completedTasks,
    blocked_tasks: blockedTasks
  };
}

export async function updateState(state: DAIState): Promise<void> {
  const projectMemory: ProjectMemory = {
    active_projects: state.active_projects
  };

  const companyMemory = await loadCompanyMemory();
  companyMemory.worker_status = state.worker_status;

  await saveProjectMemory(projectMemory);
  await saveCompanyMemory(companyMemory);
}

export async function updateTaskInGraph(
  taskId: string,
  updates: Partial<CompanyMemory['task_graph'][string]>
): Promise<void> {
  const companyMemory = await loadCompanyMemory();

  if (companyMemory.task_graph[taskId]) {
    companyMemory.task_graph[taskId] = {
      ...companyMemory.task_graph[taskId],
      ...updates,
      updated_at: new Date().toISOString()
    };
  } else {
    companyMemory.task_graph[taskId] = {
      task_id: taskId,
      type: 'unknown',
      status: 'pending',
      assigned_to: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      parent_task: null,
      child_tasks: [],
      dependencies: [],
      priority: 'medium',
      metadata: {},
      ...updates
    };
  }

  await saveCompanyMemory(companyMemory);
}

export async function addConversationToHistory(
  userInput: string,
  directorResponse: any
): Promise<void> {
  const directorMemory = await loadDirectorMemory();

  directorMemory.conversation_history.push({
    timestamp: new Date().toISOString(),
    user_input: userInput,
    director_response: directorResponse
  });

  if (directorMemory.conversation_history.length > 100) {
    directorMemory.conversation_history = directorMemory.conversation_history.slice(-100);
  }

  await saveDirectorMemory(directorMemory);
}

export async function updateWorkerLoad(
  workerId: string,
  taskId: string,
  operation: 'add' | 'remove'
): Promise<void> {
  const companyMemory = await loadCompanyMemory();

  if (!companyMemory.worker_status[workerId]) {
    throw new Error(`Worker ${workerId} not found`);
  }

  const worker = companyMemory.worker_status[workerId];

  if (operation === 'add') {
    if (!worker.current_tasks.includes(taskId)) {
      worker.current_tasks.push(taskId);
      worker.load = worker.current_tasks.length;
      worker.status = worker.load >= worker.max_capacity ? 'busy' : 'available';
    }
  } else if (operation === 'remove') {
    worker.current_tasks = worker.current_tasks.filter(id => id !== taskId);
    worker.load = worker.current_tasks.length;
    worker.status = worker.load > 0 ? 'busy' : 'available';
  }

  await saveCompanyMemory(companyMemory);
}

export {
  ProjectMemory,
  CompanyMemory,
  DirectorMemory,
  DAIState
};
