
import * as fs from 'fs-extra';
import path from 'path';
import dotenv from 'dotenv';
import TurndownService from 'turndown';
import slugify from 'slugify';
import { getArticles } from './api.ts';
import type { Article } from './types.ts';

dotenv.config({ path: path.join(__dirname, '..', '.env') });

const zendeskDomain = process.env.BASE_URL!.replace(/^https?:\/\//, '').replace(/\/$/, '');
const internalLinkRegex = new RegExp(
  `https?:\\/\\/${zendeskDomain.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\/hc\\/en-us\\/articles\\/(\\d+)(?:-[a-zA-Z0-9-]+)?`,
  'g'
);

function slugFor(article: Article): string {
  const slug = slugify(article.name, { lower: true, strict: true, locale: 'en' });
  return slug || String(article.id);
}

const turndownService = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  emDelimiter: '_',
  strongDelimiter: '**'
});


turndownService.addRule('remove-nav-and-anchors', {
  filter: (node) => {
    return node.nodeName === 'A' && !node.textContent?.trim() && !node.getAttribute('href');
  },
  replacement: () => ''
});

turndownService.addRule('clean-headings', {
  filter: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
  replacement: (content, node) => {
    const hLevel = node.nodeName.toLowerCase();
    // FAQ questions are marked up as <h4><strong>...</strong></h4>; demote them to H3
    // so they nest correctly under the FAQ's H2 section instead of skipping a level.
    const level = hLevel === 'h4' ? 3 : Number(hLevel[1]);
    const hashes = '#'.repeat(level);
    const cleanContent = content.trim().replace(/^\*\*+(.*?)\*\*+$/, '$1').replace(/^__+(.*?)__+$/, '$1');
    return `\n\n${hashes} ${cleanContent}\n\n`;
  }
});

function postProcessMarkdown(markdown: string): string {
  let result = markdown;

  // Unescape hyphens that turndown escapes as "\-".
  result = result.replace(/\\-/g, '-');

  // Split images that ended up glued directly onto preceding text, e.g. "text![alt](src)".
  result = result.replace(/([^\s\n])(!\[)/g, '$1\n$2');

  // Normalize non-breaking spaces to regular spaces.
  result = result.replace(/ /g, ' ');

  // Strip trailing whitespace from every line.
  result = result
    .split('\n')
    .map((line) => line.trimEnd())
    .join('\n');

  return result;
}

async function migrateArticles(outputDir: string) {
  try {
    await fs.ensureDir(outputDir);

    const articles = await getArticles();

    // Resolve internal links by the same filename each article is written under (slug, not id).
    const idToFileName = new Map<number, string>();
    for (const article of articles) {
      idToFileName.set(article.id, `${slugFor(article)}.md`);
    }

    for (const article of articles) {
      try {
        const fileName = idToFileName.get(article.id)!;
        const outputPath = path.join(outputDir, fileName);

        const frontmatter = [
          '---',
          `id: ${article.id}`,
          `title: "${article.name.replace(/"/g, '\\"')}"`,
          `original_url: ${article.html_url}`,
          `created_at: ${article.created_at}`,
          `updated_at: ${article.updated_at}`,
          '---\n\n'
        ].join('\n');

        let markdownBody = turndownService.turndown(article.body || '');

        markdownBody = markdownBody.replace(
          internalLinkRegex,
          (match, id) => idToFileName.get(Number(id)) ? `./${idToFileName.get(Number(id))}` : match
        );

        markdownBody = postProcessMarkdown(markdownBody);

        const finalFileContent = frontmatter + markdownBody;

        await fs.writeFile(outputPath, finalFileContent, 'utf-8');
      } catch (error) {
        console.error(`Error migrating article ${article.id} (${article.name}):`, error);
      }
    }


  } catch (error) {
    console.error('Error during migration:', error);
  }
}

const OUTPUT_DIRECTORY = path.join(__dirname, 'dist_markdown');

migrateArticles(OUTPUT_DIRECTORY);