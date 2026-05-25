#!/usr/bin/env node

import * as readline from 'readline';
import Anthropic from '@anthropic-ai/sdk';
import { DAI } from './daiAgent';
import { DAI_SYSTEM_PROMPT } from './daiSystemPrompt';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: 'DAI> '
});

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('Director AI (DAI) - Interactive CLI');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('Model: claude-opus-4-7');
  console.log('Type your requests and DAI will route them to appropriate workers.');
  console.log('Commands: /exit, /quit, /state, /help');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    console.error('ERROR: ANTHROPIC_API_KEY environment variable is not set.');
    console.error('Please set it before running the CLI.');
    process.exit(1);
  }

  const anthropicClient = new Anthropic({ apiKey });
  const dai = new DAI(anthropicClient, DAI_SYSTEM_PROMPT);

  console.log('Initializing DAI...');
  await dai.initialize();
  console.log('DAI ready!\n');

  rl.prompt();

  rl.on('line', async (line: string) => {
    const input = line.trim();

    if (!input) {
      rl.prompt();
      return;
    }

    if (input === '/exit' || input === '/quit') {
      console.log('\nShutting down DAI. Goodbye!');
      rl.close();
      process.exit(0);
    }

    if (input === '/help') {
      console.log('\nAvailable commands:');
      console.log('  /exit, /quit  - Exit the CLI');
      console.log('  /state        - Show current DAI state');
      console.log('  /help         - Show this help message');
      console.log('\nOtherwise, type any request and DAI will process it.\n');
      rl.prompt();
      return;
    }

    if (input === '/state') {
      try {
        const state = await dai.getState();
        console.log('\n═══════════════════════════════════════════════════════════════');
        console.log('Current DAI State:');
        console.log('═══════════════════════════════════════════════════════════════');
        console.log(JSON.stringify(state, null, 2));
        console.log('═══════════════════════════════════════════════════════════════\n');
      } catch (error) {
        console.error('Error retrieving state:', error);
      }
      rl.prompt();
      return;
    }

    try {
      console.log('\nProcessing...\n');
      const response = await dai.handle(input);

      console.log('═══════════════════════════════════════════════════════════════');
      console.log('DAI Response:');
      console.log('═══════════════════════════════════════════════════════════════');
      console.log(JSON.stringify(response, null, 2));
      console.log('═══════════════════════════════════════════════════════════════\n');
    } catch (error) {
      console.error('Error processing request:', error);
    }

    rl.prompt();
  });

  rl.on('close', () => {
    console.log('\nDAI CLI closed.');
    process.exit(0);
  });
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
