import express, { Request, Response } from 'express';
import Anthropic from '@anthropic-ai/sdk';
import { DAI } from './daiAgent';
import { DAI_SYSTEM_PROMPT } from './daiSystemPrompt';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

let daiInstance: DAI | null = null;

async function initializeDAI(): Promise<DAI> {
  if (daiInstance) {
    return daiInstance;
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY environment variable is not set');
  }

  const anthropicClient = new Anthropic({ apiKey });
  daiInstance = new DAI(anthropicClient, DAI_SYSTEM_PROMPT);
  await daiInstance.initialize();

  return daiInstance;
}

app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    service: 'Director AI (DAI)',
    model: 'claude-opus-4-7',
    timestamp: new Date().toISOString()
  });
});

app.post('/dai', async (req: Request, res: Response) => {
  try {
    const { input } = req.body;

    if (!input || typeof input !== 'string') {
      return res.status(400).json({
        error: 'Invalid request',
        message: 'Request body must contain an "input" field with a string value'
      });
    }

    const dai = await initializeDAI();
    const response = await dai.handle(input);

    res.json(response);
  } catch (error) {
    console.error('Error processing DAI request:', error);

    res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    });
  }
});

app.get('/state', async (req: Request, res: Response) => {
  try {
    const dai = await initializeDAI();
    const state = await dai.getState();

    res.json(state);
  } catch (error) {
    console.error('Error retrieving state:', error);

    res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

app.get('/memory/project', async (req: Request, res: Response) => {
  try {
    const dai = await initializeDAI();
    const memory = await dai.getProjectMemory();

    res.json(memory);
  } catch (error) {
    console.error('Error retrieving project memory:', error);

    res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

app.get('/memory/company', async (req: Request, res: Response) => {
  try {
    const dai = await initializeDAI();
    const memory = await dai.getCompanyMemory();

    res.json(memory);
  } catch (error) {
    console.error('Error retrieving company memory:', error);

    res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

app.get('/memory/director', async (req: Request, res: Response) => {
  try {
    const dai = await initializeDAI();
    const memory = await dai.getDirectorMemory();

    res.json(memory);
  } catch (error) {
    console.error('Error retrieving director memory:', error);

    res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

app.listen(PORT, () => {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`Director AI (DAI) Server`);
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`Port: ${PORT}`);
  console.log(`Model: claude-opus-4-7`);
  console.log(`Health: http://localhost:${PORT}/health`);
  console.log(`Endpoint: POST http://localhost:${PORT}/dai`);
  console.log(`State: GET http://localhost:${PORT}/state`);
  console.log('═══════════════════════════════════════════════════════════════');
});

export default app;
