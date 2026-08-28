#!/usr/bin/env node
/**
 * Deploy HTML presentation - merge slides into a single deployable package
 */

import { readdir, readFile, writeFile, mkdir, copyFile } from 'fs/promises';
import { resolve, dirname, basename, join, extname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

interface DeployOptions {
  slidesDir: string;
  outputDir: string;
  title?: string;
}

/**
 * Deploy presentation by creating an index.html that links all slides
 */
export async function deployPresentation(options: DeployOptions): Promise<string> {
  const {
    slidesDir,
    outputDir,
    title = 'Presentation'
  } = options;

  const absoluteSlidesDir = resolve(process.cwd(), slidesDir);
  const absoluteOutputDir = resolve(process.cwd(), outputDir);

  console.log(`[DeployPresentation] Slides: ${absoluteSlidesDir}`);
  console.log(`[DeployPresentation] Output: ${absoluteOutputDir}`);

  try {
    // Ensure output directory exists
    if (!existsSync(absoluteOutputDir)) {
      await mkdir(absoluteOutputDir, { recursive: true });
    }

    // Find all slide HTML files
    const files = await readdir(absoluteSlidesDir);
    const slideFiles = files
      .filter(f => f.match(/^slide-\d+\.html?$/i))
      .sort();

    if (slideFiles.length === 0) {
      throw new Error('No slide files found (expected slide-01.html, slide-02.html, etc.)');
    }

    console.log(`[DeployPresentation] Found ${slideFiles.length} slide(s)`);

    // Copy slide files to output
    for (const slideFile of slideFiles) {
      const srcPath = join(absoluteSlidesDir, slideFile);
      const dstPath = join(absoluteOutputDir, slideFile);
      await copyFile(srcPath, dstPath);
    }

    // Copy images directory if exists
    const imgsSrc = join(absoluteSlidesDir, 'imgs');
    const imgsDst = join(absoluteOutputDir, 'imgs');
    if (existsSync(imgsSrc)) {
      if (!existsSync(imgsDst)) {
        await mkdir(imgsDst, { recursive: true });
      }
      const imgFiles = await readdir(imgsSrc);
      for (const imgFile of imgFiles) {
        await copyFile(join(imgsSrc, imgFile), join(imgsDst, imgFile));
      }
      console.log(`[DeployPresentation] Copied ${imgFiles.length} image(s)`);
    }

    // Create index.html navigation
    const indexHtml = generateIndexHtml(slideFiles, title);
    const indexPath = join(absoluteOutputDir, 'index.html');
    await writeFile(indexPath, indexHtml, 'utf-8');

    // Create navigation script
    const navScript = generateNavigationScript();
    const navPath = join(absoluteOutputDir, 'navigation.js');
    await writeFile(navPath, navScript, 'utf-8');

    console.log('[DeployPresentation] ✓ Presentation deployed successfully');
    console.log(`[DeployPresentation] Open ${indexPath} in browser to view`);

    return absoluteOutputDir;
  } catch (error: any) {
    console.error('[DeployPresentation] ✗ Deployment failed');
    console.error('[DeployPresentation] Error:', error.message);
    throw new Error(`Deployment failed: ${error.message}`);
  }
}

/**
 * Generate index.html with slide navigation
 */
function generateIndexHtml(slideFiles: string[], title: string): string {
  const slideLinks = slideFiles.map((file, index) => {
    const num = index + 1;
    return `<button class="nav-btn" onclick="loadSlide(${num})">${num}</button>`;
  }).join('\n      ');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: #1a1a1a;
      color: #fff;
      overflow: hidden;
    }
    
    .presentation-container {
      width: 100vw;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    
    .slide-frame {
      flex: 1;
      border: none;
      background: #000;
    }
    
    .nav-bar {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 12px;
      background: #2a2a2a;
      border-top: 1px solid #3a3a3a;
    }
    
    .nav-btn {
      padding: 8px 16px;
      background: #3a3a3a;
      color: #fff;
      border: 1px solid #4a4a4a;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s;
    }
    
    .nav-btn:hover {
      background: #4a4a4a;
      border-color: #5a5a5a;
    }
    
    .nav-btn.active {
      background: #0070F3;
      border-color: #0070F3;
    }
    
    .nav-info {
      color: #999;
      font-size: 14px;
      margin-left: 16px;
    }
    
    .nav-arrow {
      padding: 8px 12px;
      background: #3a3a3a;
      color: #fff;
      border: 1px solid #4a4a4a;
      border-radius: 6px;
      cursor: pointer;
      font-size: 16px;
    }
    
    .nav-arrow:hover {
      background: #4a4a4a;
    }
  </style>
</head>
<body>
  <div class="presentation-container">
    <iframe id="slideFrame" class="slide-frame" src="${slideFiles[0]}"></iframe>
    <div class="nav-bar">
      <button class="nav-arrow" onclick="prevSlide()">←</button>
      <div id="slideNav">
        ${slideLinks}
      </div>
      <button class="nav-arrow" onclick="nextSlide()">→</button>
      <div class="nav-info">
        <span id="currentSlide">1</span> / <span id="totalSlides">${slideFiles.length}</span>
      </div>
    </div>
  </div>
  
  <script src="navigation.js"></script>
</body>
</html>`;
}

/**
 * Generate navigation JavaScript
 */
function generateNavigationScript(): string {
  return `// Presentation Navigation
let currentSlide = 1;
let totalSlides = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  const navButtons = document.querySelectorAll('.nav-btn');
  totalSlides = navButtons.length;
  updateNavigation();
  
  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') {
      nextSlide();
    } else if (e.key === 'ArrowLeft') {
      prevSlide();
    } else if (e.key >= '1' && e.key <= '9') {
      const num = parseInt(e.key);
      if (num <= totalSlides) {
        loadSlide(num);
      }
    }
  });
});

function loadSlide(num) {
  if (num < 1 || num > totalSlides) return;
  
  currentSlide = num;
  const frame = document.getElementById('slideFrame');
  frame.src = \`slide-\${String(num).padStart(2, '0')}.html\`;
  
  updateNavigation();
}

function nextSlide() {
  if (currentSlide < totalSlides) {
    loadSlide(currentSlide + 1);
  }
}

function prevSlide() {
  if (currentSlide > 1) {
    loadSlide(currentSlide - 1);
  }
}

function updateNavigation() {
  // Update active button
  const buttons = document.querySelectorAll('.nav-btn');
  buttons.forEach((btn, index) => {
    if (index + 1 === currentSlide) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  
  // Update counter
  document.getElementById('currentSlide').textContent = currentSlide;
}`;
}

// CLI interface
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  
  interface ParsedArgs {
    slidesDir?: string;
    outputDir?: string;
    title?: string;
  }
  
  const parsed: ParsedArgs = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--slides' || arg === '-s') {
      parsed.slidesDir = args[++i];
    } else if (arg === '--output' || arg === '-o') {
      parsed.outputDir = args[++i];
    } else if (arg === '--title' || arg === '-t') {
      parsed.title = args[++i];
    }
  }
  
  if (!parsed.slidesDir || !parsed.outputDir) {
    console.error('Usage: deploy_presentation.ts --slides ./slides --output ./dist [--title "My Presentation"]');
    process.exit(1);
  }
  
  deployPresentation(parsed as DeployOptions)
    .then((outputPath) => {
      console.log(JSON.stringify({ success: true, outputPath }));
      process.exit(0);
    })
    .catch((error) => {
      console.error(JSON.stringify({ success: false, error: error.message }));
      process.exit(1);
    });
}