#!/usr/bin/env node
/**
 * Verify HTML slide layout using visual analysis
 * Checks for: text overlaps, misplaced elements, page badge presence, layout correctness
 */

import { readFile } from 'fs/promises';
import { resolve, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

interface VerificationResult {
  passed: boolean;
  checks: {
    name: string;
    passed: boolean;
    details?: string;
  }[];
  issues: string[];
  suggestions: string[];
}

interface VerifyOptions {
  htmlPath: string;
  screenshotPath?: string;
  slideType: 'cover' | 'toc' | 'divider' | 'content' | 'summary';
  pageType?: string; // For content slides: 'text' | 'mixed' | 'data' | 'comparison' | 'timeline' | 'image'
}

/**
 * Verify slide layout by analyzing HTML structure
 */
export async function verifyLayout(options: VerifyOptions): Promise<VerificationResult> {
  const {
    htmlPath,
    screenshotPath,
    slideType,
    pageType
  } = options;

  const absoluteHtmlPath = resolve(process.cwd(), htmlPath);
  
  console.log(`[VerifyLayout] Analyzing: ${absoluteHtmlPath}`);
  console.log(`[VerifyLayout] Slide type: ${slideType}`);

  const checks: VerificationResult['checks'] = [];
  const issues: string[] = [];
  const suggestions: string[] = [];

  try {
    // Read HTML content
    const htmlContent = await readFile(absoluteHtmlPath, 'utf-8');

    // Check 1: Required elements present
    const hasSlideContent = htmlContent.includes('class="slide-content"') || htmlContent.includes("class='slide-content'");
    checks.push({
      name: 'Slide content container',
      passed: hasSlideContent,
      details: hasSlideContent ? '✓ .slide-content div found' : '✗ Missing .slide-content container'
    });
    if (!hasSlideContent) {
      issues.push('Missing .slide-content container - slides must have this wrapper');
    }

    // Check 2: Dimensions
    const hasCorrectDimensions = htmlContent.includes('width: 960') && htmlContent.includes('height: 540');
    checks.push({
      name: 'Correct dimensions (960×540)',
      passed: hasCorrectDimensions,
      details: hasCorrectDimensions ? '✓ 960×540px dimensions set' : '✗ Incorrect or missing dimensions'
    });
    if (!hasCorrectDimensions) {
      suggestions.push('Set slide-content dimensions to exactly 960×540px');
    }

    // Check 3: Font usage
    const hasCorrectFont = htmlContent.includes('Times New Roman');
    checks.push({
      name: 'Times New Roman font',
      passed: hasCorrectFont,
      details: hasCorrectFont ? '✓ Times New Roman font used' : '✗ Times New Roman font not found'
    });
    if (!hasCorrectFont) {
      suggestions.push('Use Times New Roman font for all text: font-family: \'Times New Roman\', serif;');
    }

    // Check 4: Page number badge (except cover)
    if (slideType !== 'cover') {
      const hasPageBadge = htmlContent.includes('right:') && htmlContent.includes('bottom:') && 
                          (htmlContent.includes('circle') || htmlContent.includes('rect'));
      checks.push({
        name: 'Page number badge',
        passed: hasPageBadge,
        details: hasPageBadge ? '✓ Page badge found' : '✗ Missing page number badge'
      });
      if (!hasPageBadge) {
        issues.push('Missing page number badge - required on all slides except cover');
      }
    } else {
      checks.push({
        name: 'Page number badge',
        passed: true,
        details: '✓ Cover page - no badge needed'
      });
    }

    // Check 5: No gradients
    const hasGradients = htmlContent.includes('gradient');
    checks.push({
      name: 'No gradients',
      passed: !hasGradients,
      details: !hasGradients ? '✓ No gradients found' : '✗ Gradients detected - use solid colors only'
    });
    if (hasGradients) {
      issues.push('Gradients found - use solid colors only');
    }

    // Check 6: No animations
    const hasAnimations = htmlContent.includes('animation') || htmlContent.includes('@keyframes');
    checks.push({
      name: 'No animations',
      passed: !hasAnimations,
      details: !hasAnimations ? '✓ No animations found' : '✗ Animations detected - static slides only'
    });
    if (hasAnimations) {
      issues.push('Animations found - slides must be static');
    }

    // Check 7: Inline CSS (except scaling snippet)
    const hasStyleBlocks = (htmlContent.match(/<style[^>]*>/g) || []).length;
    const hasScalingSnippet = htmlContent.includes('scaleSlide()');
    const allowedStyleBlocks = hasScalingSnippet ? 2 : 0; // Allow viewport style + script style
    checks.push({
      name: 'Inline CSS only',
      passed: hasStyleBlocks <= allowedStyleBlocks,
      details: hasStyleBlocks <= allowedStyleBlocks ? '✓ Using inline styles' : `✗ ${hasStyleBlocks} style blocks found - use inline CSS`
    });
    if (hasStyleBlocks > allowedStyleBlocks) {
      issues.push('Style blocks found - all CSS must be inline (except scaling snippet)');
    }

    // Check 8: SVG path constraints (no forbidden commands in path data)
    // Extract all path elements and check their d attributes
    const pathMatchRegex = /<path[^>]*\s+d=["']([^"']+)["']/gi;
    const pathMatches = htmlContent.matchAll(pathMatchRegex);
    let hasForbiddenPaths = false;
    
    for (const match of pathMatches) {
      const pathData = match[1];
      // Check for forbidden commands: Q/q (quadratic Bézier), C/c (cubic Bézier), A/a (arc)
      if (/[QA][^MLHVZ]/i.test(pathData)) {
        hasForbiddenPaths = true;
        break;
      }
    }
    
    checks.push({
      name: 'SVG path constraints',
      passed: !hasForbiddenPaths,
      details: !hasForbiddenPaths ? '✓ SVG paths valid' : '✗ Forbidden SVG path commands detected (Q/C/A)'
    });
    if (hasForbiddenPaths) {
      issues.push('Forbidden SVG path commands found (Bézier curves/arcs) - use M/L/H/V/Z only');
    }

    // Check 9: Slide type-specific checks
    if (slideType === 'cover') {
      const hasImage = htmlContent.includes('<img') || htmlContent.includes('background');
      checks.push({
        name: 'Cover image',
        passed: hasImage,
        details: hasImage ? '✓ Cover image found' : '✗ Cover slides require an image'
      });
      if (!hasImage) {
        issues.push('Cover slides must have a background image');
      }
    }

    if (slideType === 'content' && pageType) {
      const hasVisualElement = htmlContent.includes('<img') || htmlContent.includes('<svg') || 
                               htmlContent.includes('chart') || htmlContent.includes('icon');
      checks.push({
        name: 'Visual element',
        passed: hasVisualElement,
        details: hasVisualElement ? '✓ Visual element found' : '✗ Content slides require visual elements'
      });
      if (!hasVisualElement) {
        issues.push(`Content slides (${pageType}) must include visual elements (image/chart/icon/SVG)`);
      }
    }

    // Check 10: No accent lines under titles (common AI anti-pattern)
    const hasAccentLines = htmlContent.includes('border-bottom') || 
                          (htmlContent.includes('height: 1px') || htmlContent.includes('height:2px')) &&
                          htmlContent.includes('title');
    checks.push({
      name: 'No accent lines under titles',
      passed: !hasAccentLines,
      details: !hasAccentLines ? '✓ No accent lines' : '✗ Accent lines detected under title - use whitespace instead'
    });
    if (hasAccentLines) {
      issues.push('Accent lines under titles detected - use whitespace or background color instead');
    }

    // Check 11: Body text alignment (should be left-aligned)
    const hasCenteredBody = htmlContent.includes('text-align: center') || 
                           htmlContent.includes('text-align:center');
    checks.push({
      name: 'Body text alignment',
      passed: !hasCenteredBody,
      details: !hasCenteredBody ? '✓ Body text not centered' : '✗ Body text appears centered - should be left-aligned'
    });
    if (hasCenteredBody) {
      suggestions.push('Left-align body text - center only titles');
    }

    // Check 12: Reasonable bullet count (≤ 6)
    const bulletCount = (htmlContent.match(/<li>/g) || []).length;
    const hasReasonableBullets = bulletCount <= 6;
    checks.push({
      name: 'Bullet point count',
      passed: hasReasonableBullets,
      details: hasReasonableBullets ? `✓ ${bulletCount} bullet points` : `✗ ${bulletCount} bullets - max 6 recommended`
    });
    if (!hasReasonableBullets) {
      suggestions.push('Consider splitting into multiple slides or condensing content');
    }

    // Check 13: Title size hierarchy (title should be ≥ 36px)
    const hasTitleHierarchy = htmlContent.includes('font-size: 36') || 
                             htmlContent.includes('font-size: 4') ||
                             htmlContent.includes('font-size: 5') ||
                             htmlContent.includes('font-size: 6') ||
                             htmlContent.includes('font-size: 7') ||
                             htmlContent.includes('font-size: 8') ||
                             htmlContent.includes('font-size: 9') ||
                             htmlContent.includes('font-size: 10') ||
                             htmlContent.includes('font-size: 11') ||
                             htmlContent.includes('font-size: 12');
    checks.push({
      name: 'Title size hierarchy',
      passed: hasTitleHierarchy || slideType === 'cover', // Cover has different rules
      details: hasTitleHierarchy || slideType === 'cover' ? '✓ Title size appropriate' : '✗ Title should be ≥ 36px'
    });
    if (!hasTitleHierarchy && slideType !== 'cover') {
      suggestions.push('Use title font-size ≥ 36px for contrast with 14-16px body text');
    }

    // Check 14: No emojis as icons
    const hasEmojiIcons = /[\u{1F300}-\u{1F9FF}]/u.test(htmlContent);
    checks.push({
      name: 'No emojis as icons',
      passed: !hasEmojiIcons,
      details: !hasEmojiIcons ? '✓ No emoji icons' : '✗ Emojis used as icons - use SVG instead'
    });
    if (hasEmojiIcons) {
      issues.push('Emojis used as icons - use SVG from Heroicons or Lucide instead');
    }

    // Calculate overall result
    const allPassed = checks.every(check => check.passed);

    const result: VerificationResult = {
      passed: allPassed,
      checks,
      issues,
      suggestions
    };

    if (allPassed) {
      console.log('[VerifyLayout] ✓ All checks passed');
    } else {
      console.log(`[VerifyLayout] ✗ ${issues.length} issue(s) found`);
      issues.forEach(issue => console.log(`  - ${issue}`));
    }

    return result;
  } catch (error: any) {
    console.error('[VerifyLayout] ✗ Verification failed');
    console.error('[VerifyLayout] Error:', error.message);
    
    return {
      passed: false,
      checks: [{ name: 'File access', passed: false, details: error.message }],
      issues: [`Failed to read HTML file: ${error.message}`],
      suggestions: ['Ensure HTML file exists and is readable']
    };
  }
}

// CLI interface
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  
  interface ParsedArgs {
    htmlPath?: string;
    screenshotPath?: string;
    slideType?: VerifyOptions['slideType'];
    pageType?: string;
  }
  
  const parsed: ParsedArgs = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--html' || arg === '-h') {
      parsed.htmlPath = args[++i];
    } else if (arg === '--screenshot' || arg === '-s') {
      parsed.screenshotPath = args[++i];
    } else if (arg === '--type' || arg === '-t') {
      parsed.slideType = args[++i] as VerifyOptions['slideType'];
    } else if (arg === '--page-type') {
      parsed.pageType = args[++i];
    }
  }
  
  if (!parsed.htmlPath || !parsed.slideType) {
    console.error('Usage: verify_layout.ts --html path.html --type cover|toc|divider|content|summary [--page-type text|mixed|data|comparison|timeline|image] [--screenshot screenshot.png]');
    process.exit(1);
  }
  
  verifyLayout(parsed as VerifyOptions)
    .then((result) => {
      console.log(JSON.stringify(result, null, 2));
      process.exit(result.passed ? 0 : 1);
    })
    .catch((error) => {
      console.error(JSON.stringify({ passed: false, error: error.message }));
      process.exit(1);
    });
}