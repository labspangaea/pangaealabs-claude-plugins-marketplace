#!/usr/bin/env bun
/**
 * smoke — compile-only matrix runner for peruri-elysia-scaffolder (maintainer tool).
 *
 * The TS/Bun analogue of the Go plugin's tools/smoke. Renders each combo from the
 * live templates and type-checks it with `tsc --noEmit`, proving the templates
 * compile against @peruri/ts-lib across the parameter matrix. It does NOT run the
 * services (that's /integration-test-elysia-app).
 *
 * To stay fast it installs a SUPERSET of deps ONCE into scratch/_deps and symlinks
 * that node_modules into every combo dir (extra deps are harmless to tsc).
 *
 * Usage:
 *   bun tools/smoke/index.ts                 # all combos
 *   bun tools/smoke/index.ts api-pg-redis    # one combo by id
 *   PERURI_TS_LIB=/path/to/peruri-ts-lib bun tools/smoke/index.ts
 */
import { $ } from 'bun';
import { mkdir, rm, symlink, readFile, writeFile } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

const PLUGIN = join(import.meta.dir, '..', '..');
const REF = join(PLUGIN, 'skills', 'create-elysia-app', 'references');
const RENDERER = join(PLUGIN, 'tools', 'render-file', 'index.ts');

// Local peruri-ts-lib checkout to type-check against. Precedence:
//   PERURI_TS_LIB env > ~/.peruri-elysia-scaffolder/config.json (tsLibLocalPath)
//   > ~/projects/peruri-ts-lib. Only an explicit absolute tsLibLocalPath is honored
//   here — `tsLibDependency: file:../peruri-ts-lib` is relative to a *generated*
//   project, not to this maintainer tool, so it is intentionally not derived from.
function tsLibLocalFromConfig(): string | undefined {
  const cfgPath = join(process.env.HOME ?? '', '.peruri-elysia-scaffolder', 'config.json');
  if (!existsSync(cfgPath)) return undefined;
  try {
    const cfg = JSON.parse(readFileSync(cfgPath, 'utf8')) as { tsLibLocalPath?: unknown };
    if (typeof cfg.tsLibLocalPath === 'string' && cfg.tsLibLocalPath) return cfg.tsLibLocalPath;
  } catch {
    // malformed config is non-fatal — fall through to the default path
  }
  return undefined;
}
const LIB = process.env.PERURI_TS_LIB ?? tsLibLocalFromConfig() ?? join(process.env.HOME ?? '', 'projects', 'peruri-ts-lib');
const SCRATCH = join(import.meta.dir, 'scratch');

interface Combo {
  id: string;
  type: 'api' | 'consumer' | 'publisher';
  broker: 'kafka' | 'rabbitmq' | 'redis';
  database: 'drizzle-postgres' | 'drizzle-mysql' | 'none';
  cache: 'none' | 'redis' | 'memory' | 'couchbase';
}

const COMBOS: Combo[] = [
  { id: 'api-pg-redis', type: 'api', broker: 'kafka', database: 'drizzle-postgres', cache: 'redis' },
  { id: 'api-pg-memory', type: 'api', broker: 'kafka', database: 'drizzle-postgres', cache: 'memory' },
  { id: 'api-pg-couchbase', type: 'api', broker: 'kafka', database: 'drizzle-postgres', cache: 'couchbase' },
  { id: 'api-pg-none', type: 'api', broker: 'kafka', database: 'drizzle-postgres', cache: 'none' },
  { id: 'api-mysql-none', type: 'api', broker: 'kafka', database: 'drizzle-mysql', cache: 'none' },
  { id: 'consumer-kafka-pg-redis', type: 'consumer', broker: 'kafka', database: 'drizzle-postgres', cache: 'redis' },
  { id: 'consumer-rabbitmq-mysql-memory', type: 'consumer', broker: 'rabbitmq', database: 'drizzle-mysql', cache: 'memory' },
  { id: 'consumer-redis-pg-none', type: 'consumer', broker: 'redis', database: 'drizzle-postgres', cache: 'none' },
  { id: 'publisher-kafka', type: 'publisher', broker: 'kafka', database: 'none', cache: 'none' },
  { id: 'publisher-rabbitmq', type: 'publisher', broker: 'rabbitmq', database: 'none', cache: 'none' },
  { id: 'publisher-redis', type: 'publisher', broker: 'redis', database: 'none', cache: 'none' },
];

const FIELDS = [
  { Name: 'customerId', GoType: 'string', JSONName: 'customer_id', DBColumn: 'customer_id', Validate: 'required,max=64' },
  { Name: 'total', GoType: 'number', JSONName: 'total', DBColumn: 'total', Validate: 'required' },
  { Name: 'note', GoType: 'string | null', JSONName: 'note', DBColumn: 'note', Validate: '' },
];

/** templatesFor returns the [template, outputPath] pairs for a combo. */
function templatesFor(c: Combo): Array<[string, string]> {
  const out: Array<[string, string]> = [
    ['config.ts.tmpl', 'config/config.ts'],
    ['domain.ts.tmpl', 'src/domain/order.ts'],
    ['package.json.tmpl', 'package.json'],
    ['tsconfig.json.tmpl', 'tsconfig.json'],
    // Docs render for every type — included so a bad EJS edit is caught here too.
    ['README.md.tmpl', 'README.md'],
    ['CLAUDE.md.tmpl', 'CLAUDE.md'],
  ];
  const hasDb = c.database !== 'none';
  if (c.type === 'publisher') {
    out.push(['publisher.ts.tmpl', 'src/adapter/outbound/publisher/publisher.ts']);
    out.push(['index_publisher.ts.tmpl', 'src/index.ts']);
    return out;
  }
  // api + consumer share the core layers
  out.push(['port.ts.tmpl', 'src/port/order.ts']);
  out.push(['port_service.ts.tmpl', 'src/port/order-service.ts']);
  out.push(['service.ts.tmpl', 'src/service/order.ts']);
  out.push(['apperr.ts.tmpl', 'src/apperr/order.ts']);
  if (hasDb) {
    out.push(['schema.ts.tmpl', 'src/db/schema/order.ts']);
    out.push(['repository.ts.tmpl', 'src/adapter/outbound/repository/order.ts']);
  }
  if (c.type === 'api') {
    out.push(['service_stub.ts.tmpl', 'src/service/stub/order.ts']);
    out.push(['service_factory.ts.tmpl', 'src/service/factory.ts']);
    out.push(['dto.ts.tmpl', 'src/adapter/inbound/http/order.dto.ts']);
    out.push(['controller.ts.tmpl', 'src/adapter/inbound/http/order.ts']);
    out.push(['health.ts.tmpl', 'src/adapter/inbound/http/health.ts']);
    out.push(['index_api.ts.tmpl', 'src/index.ts']);
  } else {
    out.push(['subscriber.ts.tmpl', 'src/adapter/inbound/subscriber/handler.ts']);
    out.push(['index_consumer.ts.tmpl', 'src/index.ts']);
  }
  return out;
}

function params(c: Combo): string {
  return JSON.stringify({
    Name: c.id, Module: `@peruri/${c.id}`, Entity: 'Order', EntityLower: 'order',
    ApperrBase: 1000, Type: c.type, Broker: c.broker, Database: c.database, Cache: c.cache,
    Fields: FIELDS,
  });
}

/** Shared deps: a superset package.json installed once and symlinked everywhere. */
async function ensureDeps(): Promise<string> {
  const deps = join(SCRATCH, '_deps');
  if (existsSync(join(deps, 'node_modules'))) return join(deps, 'node_modules');
  await mkdir(deps, { recursive: true });
  await writeFile(join(deps, 'package.json'), JSON.stringify({
    name: 'smoke-deps', private: true, type: 'module',
    dependencies: {
      '@peruri/ts-lib': `file:${LIB}`,
      '@elysiajs/openapi': '^1.4.0', '@sinclair/typebox': '^0.34.0', 'drizzle-orm': '^0.38.0',
      elysia: '^1.2.0', ioredis: '^5.4.1', pino: '^9.5.0', kafkajs: '^2.2.4',
      amqplib: '^2.0.1', couchbase: '^4.7.0',
    },
    devDependencies: { '@types/bun': 'latest', '@types/amqplib': '^0.10.8', typescript: '^5.7.0' },
  }, null, 2));
  console.log('  installing shared deps (once)…');
  await $`cd ${deps} && bun install`.quiet();
  return join(deps, 'node_modules');
}

async function renderCombo(c: Combo, nodeModules: string): Promise<void> {
  const dir = join(SCRATCH, c.id);
  await rm(dir, { recursive: true, force: true });
  await mkdir(dir, { recursive: true });
  const p = params(c);
  for (const [tmpl, outRel] of templatesFor(c)) {
    const outAbs = join(dir, outRel);
    await mkdir(dirname(outAbs), { recursive: true });
    await $`bun ${RENDERER} -template ${join(REF, tmpl)} -params ${p} -output ${outAbs}`.quiet();
  }
  // Share the single installed node_modules.
  await symlink(nodeModules, join(dir, 'node_modules'), 'dir').catch(() => {});
}

async function main(): Promise<void> {
  const filter = process.argv[2];
  const combos = filter ? COMBOS.filter((c) => c.id === filter) : COMBOS;
  if (combos.length === 0) {
    console.error(`no combo matches "${filter}". Known: ${COMBOS.map((c) => c.id).join(', ')}`);
    process.exit(2);
  }
  if (!existsSync(LIB)) {
    console.error(`@peruri/ts-lib not found at ${LIB} (set PERURI_TS_LIB)`);
    process.exit(2);
  }
  await mkdir(SCRATCH, { recursive: true });
  const nodeModules = await ensureDeps();

  let pass = 0;
  let fail = 0;
  for (const c of combos) {
    await renderCombo(c, nodeModules);
    const dir = join(SCRATCH, c.id);
    const res = await $`cd ${dir} && ./node_modules/.bin/tsc --noEmit`.nothrow().quiet();
    if (res.exitCode === 0) {
      console.log(`  [pass] ${c.id}`);
      pass++;
    } else {
      console.log(`  [FAIL] ${c.id}`);
      console.log(res.stdout.toString().split('\n').slice(0, 8).map((l) => `    ${l}`).join('\n'));
      fail++;
    }
  }
  console.log(`\n${pass} passed, ${fail} failed (total ${combos.length})`);
  process.exit(fail === 0 ? 0 : 1);
}

main();
