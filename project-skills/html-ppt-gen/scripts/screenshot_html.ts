#!/usr/bin/env node
/**
 * Screenshot HTML presentation slides using Playwright
 */

import { chromium, Browser, Page } from 'playwright';
import { resolve, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { existsSync, mkdirSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

interface ScreenshotOptions {
  htmlPath: string;
  outputPath?: string;
  width?: number;
  height?: number;
  fullPage?: boolean;
}

/**
 * Take a screenshot of an HTML file
 */
export async function screenshotHTML(options: ScreenshotOptions): Promise<string> {
  const {
    htmlPath,
    outputPath,
    width = 960,
    height = 540,
    fullPage = false
  } = options;

  const absoluteHtmlPath = resolve(process.cwd(), htmlPath);
  const fileUrl = `file:///${absoluteHtmlPath.replace(/\\/g, '/')}`;
  
  // Determine output path
  const screenshotPath = outputPath
    ? resolve(process.cwd(), outputPath)
    : absoluteHtmlPath.replace(/\.html?$/i, '.png');

  // Ensure output directory exists
  const outputDir = dirname(screenshotPath);
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  console.log(`[ScreenshotHTML] Loading: ${fileUrl}`);
  console.log(`[ScreenshotHTML] Output: ${screenshotPath}`);

  let browser: Browser | null = null;
  
  try {
    // Launch browser
    browser = await chromium.launch({
      headless: true
    });

    const context = await browser.newContext({
      viewport: { width, height },
      deviceScaleFactor: 2 // For high-quality screenshots
    });

    const page = await context.newPage();

    // Navigate to HTML file
    await page.goto(fileUrl, {
      waitUntil: 'networkidle',
      timeout: 10000
    });

    // Wait for slide content to render
    await page.waitForSelector('.slide-content', { timeout: 5000 });

    // Take screenshot
    await page.screenshot({
      path: screenshotPath,
      fullPage,
      type: 'png'
    });

    console.log('[ScreenshotHTML] ✓ Screenshot captured successfully');
    return screenshotPath;
  } catch (error: any) {
    console.error('[ScreenshotHTML] ✗ Failed to capture screenshot');
    console.error('[ScreenshotHTML] Error:', error.message);
    throw new Error(`Screenshot failed: ${error.message}`);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// CLI interface
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  
  interface ParsedArgs {
    htmlPath?: string;
    outputPath?: string;
    width?: number;
    height?: number;
    fullPage?: boolean;
  }
  
  const parsed: ParsedArgs = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--html' || arg === '-h') {
      parsed.htmlPath = args[++i];
    } else if (arg === '--output' || arg === '-o') {
      parsed.outputPath = args[++i];
    } else if (arg === '--width' || arg === '-w') {
      parsed.width = parseInt(args[++i], 10);
    } else if (arg === '--height' || arg === '-h') {
      parsed.height = parseInt(args[++i], 10);
    } else if (arg === '--full-page') {
      parsed.fullPage = true;
    }
  }
  
  if (!parsed.htmlPath) {
    console.error('Usage: screenshot_html.ts --html path.html [--output screenshot.png] [--width 960] [--height 540] [--full-page]');
    process.exit(1);
  }
  
  screenshotHTML(parsed as ScreenshotOptions)
    .then((path) => {
      console.log(JSON.stringify({ success: true, path }));
      process.exit(0);
    })
    .catch((error) => {
      console.error(JSON.stringify({ success: false, error: error.message }));
      process.exit(1);
    });
}