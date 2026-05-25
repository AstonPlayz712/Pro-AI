#!/usr/bin/env node

/**
 * DAI Quick Start Test
 *
 * This script demonstrates basic DAI functionality without requiring
 * a full build. Run with: npm run cli
 *
 * Prerequisites:
 * 1. npm install
 * 2. Set ANTHROPIC_API_KEY environment variable
 * 3. Run: ts-node src/quickstart.ts
 */

import Anthropic from '@anthropic-ai/sdk';
import { DAI } from './daiAgent';
import { DAI_SYSTEM_PROMPT } from './daiSystemPrompt';

async function quickTest() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('DAI Quick Start Test');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    console.error('ERROR: ANTHROPIC_API_KEY environment variable not set');
    console.error('Please set it with: export ANTHROPIC_API_KEY="your-key"');
    process.exit(1);
  }

  console.log('✓ API key found');
  console.log('✓ Initializing DAI...\n');

  const client = new Anthropic({ apiKey });
  const dai = new DAI(client, DAI_SYSTEM_PROMPT);

  await dai.initialize();
  console.log('✓ DAI initialized\n');

  const testRequests = [
    'Build a REST API for user authentication with JWT tokens',
    'Fix a memory leak in the session handler',
    'Write documentation for the new authentication API',
    'What is the current project status?'
  ];

  for (let i = 0; i < testRequests.length; i++) {
    const request = testRequests[i];
    console.log('─────────────────────────────────────────────────────────────');
    console.log(`Test ${i + 1}/${testRequests.length}: ${request}`);
    console.log('─────────────────────────────────────────────────────────────\n');

    try {
      console.log('Processing...');
      const response = await dai.handle(request);

      console.log('\n✓ Response received:\n');
      console.log('Summary:', response.director_summary);
      console.log('\nRequest Type:', response.request_analysis.type);
      console.log('Complexity:', response.request_analysis.complexity);
      console.log('Required Skills:', response.request_analysis.required_skills.join(', '));

      if (response.routing_decision.assignments.length > 0) {
        console.log('\nTask Assignments:');
        for (const assignment of response.routing_decision.assignments) {
          console.log(`  • ${assignment.worker_name} (${assignment.worker_id})`);
          console.log(`    Task: ${assignment.task_description}`);
          console.log(`    Priority: ${assignment.priority}`);
          console.log(`    Est. Duration: ${assignment.estimated_duration}`);
        }
      }

      console.log('\nProject Status:');
      console.log(`  Active: ${response.project_status.active_tasks}`);
      console.log(`  Completed: ${response.project_status.completed_tasks}`);
      console.log(`  Blocked: ${response.project_status.blocked_tasks}`);

      console.log('\n');
    } catch (error) {
      console.error('✗ Error:', error instanceof Error ? error.message : 'Unknown error');
    }

    if (i < testRequests.length - 1) {
      console.log('Waiting 2 seconds before next test...\n');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  console.log('═══════════════════════════════════════════════════════════════');
  console.log('All tests completed!');
  console.log('═══════════════════════════════════════════════════════════════');

  const finalState = await dai.getState();
  console.log('\nFinal System State:');
  console.log(`  Active Projects: ${Object.keys(finalState.active_projects).length}`);
  console.log(`  Task Queue Length: ${finalState.task_queue.length}`);
  console.log(`  Completed Tasks: ${finalState.completed_tasks.length}`);
  console.log(`  Blocked Tasks: ${finalState.blocked_tasks.length}`);

  console.log('\nWorker Status:');
  for (const [workerId, worker] of Object.entries(finalState.worker_status)) {
    if (worker.load > 0) {
      console.log(`  ${workerId}: ${worker.status} (load: ${worker.load}/${worker.max_capacity})`);
    }
  }

  console.log('\n✓ Quick start test complete!');
  console.log('\nNext steps:');
  console.log('  • Run: npm run cli (for interactive CLI)');
  console.log('  • Run: npm run dev (for HTTP server)');
  console.log('  • Run: npm run discord (for Discord bot)');
  console.log('  • Check memory files in ./memory/ directory');
}

if (require.main === module) {
  quickTest().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { quickTest };
