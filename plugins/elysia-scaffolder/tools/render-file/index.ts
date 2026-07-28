#!/usr/bin/env bun
/**
 * render-file — zero-dependency template renderer for elysia-scaffolder.
 *
 * The TS/Bun analog of the Go plugin's tools/render-file/main.go. It compiles an
 * EJS-style `.tmpl` (`<%= expr %>` interpolation, `<% stmt %>` logic) into a JS
 * function and runs it against the `-params` JSON plus a set of helper functions,
 * so every conditional/loop is evaluated by a real engine — never "in the model's
 * head". Kept dependency-free on purpose: the plugin renders without `bun install`.
 *
 * Usage:
 *   bun render-file/index.ts -template <file.tmpl> -params '<json>' [-output <path>]
 *
 * Params shape mirrors the Go renderer's FieldDef/Params so the same JSON works
 * across both plugins:
 *   { Name, Module, Entity, EntityLower, ApperrBase, Type, Broker, Database, Cache,
 *     Fields: [ { Name, GoType, JSONName, DBColumn, Validate } ] }
 */

import { mkdir } from "node:fs/promises";
import { dirname } from "node:path";

interface FieldDef {
  Name: string;
  GoType: string; // TS type string: string | number | boolean | Date | "T | null"
  JSONName: string;
  DBColumn: string;
  Validate: string;
}

interface Params {
  Name?: string;
  Module?: string;
  Entity?: string;
  EntityLower?: string;
  ApperrBase?: number;
  Type?: string;
  Broker?: string;
  Database?: string;
  Cache?: string;
  Fields?: FieldDef[];
  [k: string]: unknown;
}

// ---- helper functions exposed to every template ---------------------------

const helpers = {
  /** seq(n) -> [0,1,...,n-1] */
  seq(n: number): number[] {
    return Array.from({ length: n }, (_, i) => i);
  },

  /** isRequired("required,max=64") -> true */
  isRequired(validate: string): boolean {
    return typeof validate === "string" && validate.includes("required");
  },

  /** parseMaxLength("required,max=64") -> 64 ; absent -> 0 */
  parseMaxLength(validate: string): number {
    const m = /max=(\d+)/.exec(validate ?? "");
    return m ? Number(m[1]) : 0;
  },

  /** true when the TS type is nullable ("T | null") */
  isNullable(goType: string): boolean {
    return /\|\s*null/.test(goType);
  },

  /** strip "| null" to the base TS type */
  baseType(goType: string): string {
    return goType.replace(/\s*\|\s*null\s*$/, "").trim();
  },

  /** drizzle dialect token for the chosen database */
  dbDialect(database: string): string {
    return database === "drizzle-mysql" ? "mysql" : "pg";
  },

  /** true if any field uses (or is a nullable of) the given base TS type */
  hasFieldType(goType: string, fields: FieldDef[]): boolean {
    return (fields ?? []).some((f) => helpers.baseType(f.GoType) === goType);
  },

  /** true if any field is nullable */
  hasNullableField(fields: FieldDef[]): boolean {
    return (fields ?? []).some((f) => helpers.isNullable(f.GoType));
  },

  /**
   * seedValue(goType, idx) -> a TS literal string for deterministic seed data.
   * Nullable types are emitted as the inner literal (never null) so seeded rows
   * are fully populated — matches the Go renderer's seedValue behavior.
   */
  seedValue(goType: string, idx: number): string {
    const base = helpers.baseType(goType);
    const n = idx + 1;
    switch (base) {
      case "string":
        return JSON.stringify(`sample-${n}`);
      case "number":
        return String(n * 10);
      case "boolean":
        return idx % 2 === 0 ? "true" : "false";
      case "Date":
        return "new Date()";
      default:
        return JSON.stringify(`sample-${n}`);
    }
  },

  /**
   * stubValue(goType) -> a TS expression string for a canned stub value that
   * varies by the loop index `i` (used by the service stub template inside a
   * `cannedEntity(i)` function). Nullable types alternate value/null by `i`.
   */
  stubValue(goType: string): string {
    const base = helpers.baseType(goType);
    const nullable = helpers.isNullable(goType);
    let v: string;
    switch (base) {
      case "string":
        v = "`sample-${i}`";
        break;
      case "number":
        v = "(i + 1) * 10";
        break;
      case "boolean":
        v = "i % 2 === 0";
        break;
      case "Date":
        v = "EPOCH";
        break;
      default:
        v = "`sample-${i}`";
    }
    return nullable ? `i % 2 === 0 ? ${v} : null` : v;
  },

  /**
   * seedSqlValue(goType) -> a TS expression string for a deterministic seed value
   * inside a `for (let i...)` loop, used by seed.ts.tmpl. Date fields become an
   * epoch-ms number (`now + i`), not a Date object, since the column is bigint.
   */
  seedSqlValue(goType: string): string {
    const base = helpers.baseType(goType);
    const nullable = helpers.isNullable(goType);
    let v: string;
    switch (base) {
      case "string":
        v = "`sample-${i + 1}`";
        break;
      case "number":
        v = "(i + 1) * 9.99";
        break;
      case "boolean":
        v = "i % 2 === 0";
        break;
      case "Date":
        v = "now + i";
        break;
      default:
        v = "`sample-${i + 1}`";
    }
    return nullable ? `i % 2 === 0 ? ${v} : null` : v;
  },

  /** PascalCase a kebab/snake string */
  pascal(s: string): string {
    return (s ?? "")
      .split(/[-_\s]+/)
      .filter(Boolean)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join("");
  },
};

// ---- the EJS-style compiler ------------------------------------------------

function compile(tmpl: string): (scope: Record<string, unknown>) => string {
  let code = "let __o='';\n";
  // `<%= expr %>` interpolation, `<% stmt %>` logic; a trailing `-` (`-%>`) trims
  // the newline that immediately follows the tag, so conditional/loop blocks don't
  // leave blank lines in the output.
  const re = /<%([=]?)([\s\S]*?)(-?)%>/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let trimNext = false;
  const emit = (s: string) => {
    code += "__o+=" + JSON.stringify(s) + ";\n";
  };
  while ((m = re.exec(tmpl)) !== null) {
    let lit = tmpl.slice(last, m.index);
    if (trimNext) lit = lit.replace(/^\r?\n/, "");
    emit(lit);
    const body = m[2].trim();
    if (m[1] === "=") {
      code += "__o+=String((" + body + ") ?? '');\n";
    } else {
      code += body + "\n";
    }
    trimNext = m[3] === "-";
    last = re.lastIndex;
  }
  let tail = tmpl.slice(last);
  if (trimNext) tail = tail.replace(/^\r?\n/, "");
  emit(tail);
  code += "return __o;";
  // The scope keys become local variable names inside the template.
  return (scope: Record<string, unknown>) => {
    const keys = Object.keys(scope);
    // eslint-disable-next-line no-new-func
    const fn = new Function(...keys, code);
    return fn(...keys.map((k) => scope[k])) as string;
  };
}

// ---- CLI -------------------------------------------------------------------

function parseArgs(argv: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("-")) {
      const key = a.replace(/^-+/, "");
      const val = argv[i + 1];
      if (val === undefined || val.startsWith("-")) {
        out[key] = "true";
      } else {
        out[key] = val;
        i++;
      }
    }
  }
  return out;
}

async function main() {
  const args = parseArgs(Bun.argv.slice(2));
  const templatePath = args.template;
  const paramsRaw = args.params;
  const outputPath = args.output;

  if (!templatePath || !paramsRaw) {
    console.error(
      "usage: bun render-file/index.ts -template <file.tmpl> -params '<json>' [-output <path>]",
    );
    process.exit(2);
  }

  const tmpl = await Bun.file(templatePath).text();
  let params: Params;
  try {
    params = JSON.parse(paramsRaw) as Params;
  } catch (e) {
    console.error(`render-file: invalid -params JSON: ${(e as Error).message}`);
    process.exit(2);
    return;
  }

  const scope = { ...helpers, ...params };
  let rendered: string;
  try {
    rendered = compile(tmpl)(scope);
  } catch (e) {
    console.error(
      `render-file: error rendering ${templatePath}: ${(e as Error).message}`,
    );
    process.exit(1);
    return;
  }

  if (outputPath) {
    await mkdir(dirname(outputPath), { recursive: true });
    await Bun.write(outputPath, rendered);
  } else {
    process.stdout.write(rendered);
  }
}

main();
