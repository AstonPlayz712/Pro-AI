import Anthropic from '@anthropic-ai/sdk';

const MODEL = 'claude-opus-4-7';

export interface DAIClientOptions {
  apiKey?: string;
  maxTokens?: number;
}

export async function callDAI(
  input: string,
  systemPrompt: string,
  options: DAIClientOptions = {}
): Promise<string> {
  const apiKey = options.apiKey || process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY is not set');
  }

  const anthropic = new Anthropic({
    apiKey: apiKey
  });

  try {
    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: options.maxTokens || 4096,
      system: systemPrompt,
      messages: [
        {
          role: 'user',
          content: input
        }
      ]
    });

    if (response.content && response.content.length > 0) {
      const firstContent = response.content[0];
      if (firstContent.type === 'text') {
        return firstContent.text;
      }
    }

    throw new Error('No text content in response');
  } catch (error) {
    console.error('Error calling Anthropic API:', error);
    throw error;
  }
}

export async function callDAIStreaming(
  input: string,
  systemPrompt: string,
  onChunk: (chunk: string) => void,
  options: DAIClientOptions = {}
): Promise<string> {
  const apiKey = options.apiKey || process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY is not set');
  }

  const anthropic = new Anthropic({
    apiKey: apiKey
  });

  try {
    const stream = await anthropic.messages.create({
      model: MODEL,
      max_tokens: options.maxTokens || 4096,
      system: systemPrompt,
      messages: [
        {
          role: 'user',
          content: input
        }
      ],
      stream: true
    });

    let fullResponse = '';

    for await (const event of stream) {
      if (event.type === 'content_block_delta') {
        if (event.delta.type === 'text_delta') {
          const chunk = event.delta.text;
          fullResponse += chunk;
          onChunk(chunk);
        }
      }
    }

    return fullResponse;
  } catch (error) {
    console.error('Error calling Anthropic API (streaming):', error);
    throw error;
  }
}
