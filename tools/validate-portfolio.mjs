#!/usr/bin/env node
/**
 * Validates data/projects.json before the site is published (run by .github/workflows/validate.yml).
 * The key rule: this portfolio shows SOFTWARE only. Games belong to https://ahshika.github.io/games/.
 * No dependencies; mirrors validateGeneralFile() of the automation's @ada/portfolio package.
 *   node tools/validate-portfolio.mjs [path/to/projects.json]
 */
import { readFileSync } from 'node:fs';

const PLATFORMS = new Set(['WINDOWS', 'MACOS', 'LINUX', 'ANDROID', 'IOS', 'WEB', 'CONSOLE']);
const LAYERS = new Set(['ai', 'web', 'desktop', 'mobile']);
const ID = /^[a-z0-9][a-z0-9-]{0,62}$/;
const isStr = (v, max = 2000) => typeof v === 'string' && v.trim().length > 0 && v.length <= max;
const isUrl = (v) => {
  if (typeof v !== 'string' || v.length > 2048) return false;
  try { return new URL(v).protocol === 'https:'; } catch { return false; }
};
const repoKey = (u) => u.trim().replace(/\/+$/, '').toLowerCase();

export function validate(f) {
  const errors = [];
  if (!f || typeof f !== 'object') return ['file must be a JSON object'];
  if (f.version !== 1) errors.push('version must be 1');
  if (!Array.isArray(f.projects)) return [...errors, 'projects must be a list'];
  if (f.projects.length > 500) errors.push('at most 500 projects');
  const ids = new Set();
  const repos = new Set();
  f.projects.forEach((e, i) => {
    const w = `projects[${i}]${e && typeof e.id === 'string' ? ` (${e.id})` : ''}`;
    if (!e || typeof e !== 'object') return void errors.push(`${w}: must be an object`);
    if (e.family !== 'SOFTWARE') errors.push(`${w}: only SOFTWARE belongs in this portfolio (got ${e.family}); games go to the games portfolio`);
    if (typeof e.id !== 'string' || !ID.test(e.id)) errors.push(`${w}: id must be lowercase letters, digits and dashes`);
    else if (ids.has(e.id)) errors.push(`${w}: duplicate id`);
    else ids.add(e.id);
    if (!isStr(e.name, 120)) errors.push(`${w}: name is required`);
    if (!isStr(e.tagline, 400)) errors.push(`${w}: tagline is required`);
    if (!LAYERS.has(e.layer)) errors.push(`${w}: layer must be ai, web, desktop or mobile`);
    if (!Array.isArray(e.points) || e.points.some((p) => !isStr(p))) errors.push(`${w}: points must be a list of text`);
    if (!Array.isArray(e.props) || e.props.some((p) => !Array.isArray(p) || p.length !== 2 || !isStr(p[0], 40) || !isStr(p[1], 120))) errors.push(`${w}: props must be [label, value] pairs`);
    if (!Array.isArray(e.stack) || e.stack.some((s) => !isStr(s, 60))) errors.push(`${w}: stack must be a list of text`);
    if (!isStr(e.dim, 80)) errors.push(`${w}: dim is required`);
    if (!Array.isArray(e.platforms) || e.platforms.some((p) => !PLATFORMS.has(p))) errors.push(`${w}: unknown platform`);
    if (e.repo !== undefined) {
      if (!isUrl(e.repo)) errors.push(`${w}: repo must be an https URL`);
      else if (repos.has(repoKey(e.repo))) errors.push(`${w}: repository listed twice`);
      else repos.add(repoKey(e.repo));
    }
    if (e.live !== undefined && !isUrl(e.live)) errors.push(`${w}: live must be an https URL`);
    if (e.extra !== undefined && (!Array.isArray(e.extra) || e.extra.some((x) => !Array.isArray(x) || x.length !== 2 || !isStr(x[0], 80) || !isUrl(x[1])))) errors.push(`${w}: extra links must be [label, https URL]`);
    if (e.downloads !== undefined && (!Array.isArray(e.downloads) || e.downloads.some((d) => !d || !isStr(d.label, 80) || !isUrl(d.url)))) errors.push(`${w}: downloads need a label and an https URL`);
    if (e.source !== 'ada' && e.source !== 'manual') errors.push(`${w}: source must be "ada" or "manual"`);
  });
  return errors;
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('validate-portfolio.mjs')) {
  const path = process.argv[2] ?? 'data/projects.json';
  let data;
  try {
    data = JSON.parse(readFileSync(path, 'utf8'));
  } catch (e) {
    console.error(`${path}: not valid JSON (${e.message})`);
    process.exit(1);
  }
  const errors = validate(data);
  // The page must load projects from the data file, never re-add repositories on its own.
  const html = readFileSync('index.html', 'utf8');
  if (/const\s+PROJECTS\s*=\s*\[/.test(html)) errors.push('index.html: projects must come from data/projects.json, not a hard-coded list');
  if (/api\.github\.com\/users\/[^/]+\/repos/.test(html)) errors.push('index.html: automatic repository import is not allowed (it bypasses classification)');
  if (errors.length) {
    console.error(`Portfolio validation failed (${errors.length}):\n- ${errors.join('\n- ')}`);
    process.exit(1);
  }
  console.log(`OK: ${data.projects.length} software projects, no games.`);
}
