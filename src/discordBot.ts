import { Client, GatewayIntentBits, Message, Events } from 'discord.js';
import Anthropic from '@anthropic-ai/sdk';
import { DAI } from './daiAgent';
import { DAI_SYSTEM_PROMPT } from './daiSystemPrompt';

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

function formatDAIResponseForDiscord(response: any): string {
  const summary = response.director_summary || 'No summary available';

  let message = `**Director AI Response**\n\n`;
  message += `${summary}\n\n`;

  if (response.routing_decision?.assignments?.length > 0) {
    message += `**Task Assignments:**\n`;
    for (const assignment of response.routing_decision.assignments) {
      message += `• **${assignment.worker_name}** (${assignment.worker_id}): ${assignment.task_description}\n`;
      message += `  Priority: ${assignment.priority} | Est. Duration: ${assignment.estimated_duration}\n`;
    }
    message += `\n`;
  }

  if (response.project_status) {
    message += `**Project Status:**\n`;
    message += `• Active: ${response.project_status.active_tasks}\n`;
    message += `• Completed: ${response.project_status.completed_tasks}\n`;
    message += `• Blocked: ${response.project_status.blocked_tasks}\n\n`;
  }

  if (response.next_steps?.length > 0) {
    message += `**Next Steps:**\n`;
    for (const step of response.next_steps) {
      message += `• ${step}\n`;
    }
  }

  if (message.length > 2000) {
    message = message.substring(0, 1997) + '...';
  }

  return message;
}

export async function startDiscordBot(): Promise<void> {
  const discordToken = process.env.DISCORD_BOT_TOKEN;

  if (!discordToken) {
    console.error('ERROR: DISCORD_BOT_TOKEN environment variable is not set');
    console.error('Please set it to run the Discord bot');
    process.exit(1);
  }

  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.DirectMessages
    ]
  });

  client.once(Events.ClientReady, (readyClient) => {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`Director AI Discord Bot Ready`);
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`Logged in as: ${readyClient.user.tag}`);
    console.log(`Bot ID: ${readyClient.user.id}`);
    console.log(`Guilds: ${readyClient.guilds.cache.size}`);
    console.log('═══════════════════════════════════════════════════════════════');
  });

  client.on(Events.MessageCreate, async (message: Message) => {
    if (message.author.bot) return;

    const botMention = `<@${client.user?.id}>`;
    const isMentioned = message.mentions.has(client.user!);
    const isDM = message.channel.isDMBased();

    if (!isMentioned && !isDM) return;

    let userInput = message.content;

    if (isMentioned) {
      userInput = userInput.replace(botMention, '').trim();
    }

    if (!userInput) {
      await message.reply('Please provide a request for me to process.');
      return;
    }

    try {
      await message.channel.sendTyping();

      const dai = await initializeDAI();
      const response = await dai.handle(userInput);

      const formattedResponse = formatDAIResponseForDiscord(response);

      await message.reply(formattedResponse);
    } catch (error) {
      console.error('Error processing Discord message:', error);

      const errorMessage = error instanceof Error
        ? `Error: ${error.message}`
        : 'An unknown error occurred';

      await message.reply(`Sorry, I encountered an error: ${errorMessage}`);
    }
  });

  client.on(Events.Error, (error) => {
    console.error('Discord client error:', error);
  });

  await client.login(discordToken);
}

if (require.main === module) {
  startDiscordBot().catch((error) => {
    console.error('Fatal error starting Discord bot:', error);
    process.exit(1);
  });
}
