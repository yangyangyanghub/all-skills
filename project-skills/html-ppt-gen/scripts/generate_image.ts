#!/usr/bin/env node
/**
 * Generate images for HTML presentation slides
 * Wrapper around baoyu-image-gen skill
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const execAsync = promisify(exec);

const __dirname = dirname(fileURLToPath(import.meta.url));

interface GenerateImageOptions {
  prompt: string;
  output: string;
  aspectRatio?: string;
  quality?: 'normal' | '2k';
  provider?: 'google' | 'openai' | 'dashscope' | 'replicate';
  model?: string;
}

/**
 * Generate an image using baoyu-image-gen skill
 */
export async function generateImage(options: GenerateImageOptions): Promise<string> {
  const {
    prompt,
    output,
    aspectRatio = '16:9',
    quality = '2k',
    provider = 'google',
    model
  } = options;

  // Resolve absolute path for output
  const outputPath = resolve(process.cwd(), output);
  
  // Build command
  const skillDir = 'C:\\Users\\HP\\.config\\opencode\\skill\\baoyu-image-gen';
  const scriptPath = `${skillDir}/scripts/main.ts`;
  
  let command = `npx -y bun "${scriptPath}" --prompt "${prompt.replace(/"/g, '\\"')}" --image "${outputPath}" --ar ${aspectRatio} --quality ${quality} --provider ${provider}`;
  
  if (model) {
    command += ` --model ${model}`;
  }

  console.log(`[GenerateImage] Generating image for: "${prompt.substring(0, 50)}..."`);
  console.log(`[GenerateImage] Output: ${outputPath}`);
  
  try {
    const { stdout, stderr } = await execAsync(command, {
      maxBuffer: 10 * 1024 * 1024, // 10MB buffer
      cwd: process.cwd()
    });
    
    if (stderr && !stderr.includes('Successfully')) {
      console.error('[GenerateImage] stderr:', stderr);
    }
    
    console.log('[GenerateImage] ✓ Image generated successfully');
    return outputPath;
  } catch (error: any) {
    console.error('[GenerateImage] ✗ Failed to generate image');
    console.error('[GenerateImage] Error:', error.message);
    throw new Error(`Image generation failed: ${error.message}`);
  }
}

// CLI interface
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  
  interface ParsedArgs {
    prompt?: string;
    output?: string;
    aspectRatio?: string;
    quality?: 'normal' | '2k';
    provider?: 'google' | 'openai' | 'dashscope' | 'replicate';
    model?: string;
  }
  
  const parsed: ParsedArgs = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--prompt' || arg === '-p') {
      parsed.prompt = args[++i];
    } else if (arg === '--output' || arg === '-o') {
      parsed.output = args[++i];
    } else if (arg === '--ar' || arg === '--aspect-ratio') {
      parsed.aspectRatio = args[++i];
    } else if (arg === '--quality') {
      parsed.quality = args[++i] as 'normal' | '2k';
    } else if (arg === '--provider') {
      parsed.provider = args[++i] as 'google' | 'openai' | 'dashscope' | 'replicate';
    } else if (arg === '--model' || arg === '-m') {
      parsed.model = args[++i];
    }
  }
  
  if (!parsed.prompt || !parsed.output) {
    console.error('Usage: generate_image.ts --prompt "..." --output path.png [--ar 16:9] [--quality 2k] [--provider google] [--model ...]');
    process.exit(1);
  }
  
  generateImage(parsed as GenerateImageOptions)
    .then((path) => {
      console.log(JSON.stringify({ success: true, path }));
      process.exit(0);
    })
    .catch((error) => {
      console.error(JSON.stringify({ success: false, error: error.message }));
      process.exit(1);
    });
}