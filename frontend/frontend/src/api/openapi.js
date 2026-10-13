import { api } from './client';

// The backend is FastAPI, so it publishes its real request schemas at
// /openapi.json. Forms are generated from those schemas so the UI never
// invents request fields. Cached for the lifetime of the page.
let specPromise = null;

export function loadSpec() {
  if (!specPromise) {
    specPromise = api
      .get('/openapi.json', { timeout: 8000, skipAuthRedirect: true })
      .then((r) => r.data)
      .catch((e) => {
        specPromise = null;
        throw e;
      });
  }
  return specPromise;
}

function resolveRef(spec, ref) {
  if (!ref || !ref.startsWith('#/')) return {};
  return (
    ref
      .slice(2)
      .split('/')
      .reduce((node, part) => (node ? node[part] : undefined), spec) || {}
  );
}

// Resolves $ref / allOf / anyOf(nullable) into one flat schema.
export function normalizeSchema(spec, schema, depth = 0) {
  if (!schema || depth > 6) return {};
  if (schema.$ref) return normalizeSchema(spec, resolveRef(spec, schema.$ref), depth + 1);

  if (schema.allOf) {
    const merged = { ...schema };
    delete merged.allOf;
    for (const part of schema.allOf) {
      const n = normalizeSchema(spec, part, depth + 1);
      const properties = { ...(merged.properties || {}), ...(n.properties || {}) };
      const required = [...(merged.required || []), ...(n.required || [])];
      Object.assign(merged, n, { properties, required });
    }
    return merged;
  }

  const union = schema.anyOf || schema.oneOf;
  if (union) {
    const nonNull = union.filter((s) => s.type !== 'null');
    const base = nonNull.length ? normalizeSchema(spec, nonNull[0], depth + 1) : {};
    return {
      ...base,
      title: schema.title || base.title,
      description: schema.description || base.description,
      default: schema.default !== undefined ? schema.default : base.default,
      nullable: nonNull.length !== union.length,
    };
  }
  return schema;
}

export function getOperation(spec, path, method) {
  return spec?.paths?.[path]?.[method.toLowerCase()] || null;
}

function toField(spec, name, rawSchema, requiredSet) {
  const s = normalizeSchema(spec, rawSchema);
  const items = s.items ? normalizeSchema(spec, s.items) : null;
  let type = s.type || 'string';
  if (!s.type && s.properties) type = 'object';
  return {
    name,
    title: s.title || null,
    description: s.description || null,
    type,
    format: s.format || null,
    enum: s.enum || null,
    default: s.default,
    nullable: !!s.nullable,
    required: requiredSet.has(name),
    minimum: s.minimum ?? s.exclusiveMinimum,
    maximum: s.maximum ?? s.exclusiveMaximum,
    minLength: s.minLength,
    maxLength: s.maxLength,
    pattern: s.pattern,
    writeOnly: !!s.writeOnly,
    itemType: items?.type || 'string',
    itemEnum: items?.enum || null,
  };
}

// Returns { hasOperation, hasBody, contentType, fields | null }
export function describeRequestBody(spec, path, method) {
  const op = getOperation(spec, path, method);
  if (!op) return { hasOperation: false, hasBody: false, contentType: null, fields: null };
  const body = op.requestBody;
  if (!body) return { hasOperation: true, hasBody: false, contentType: null, fields: [] };

  const contentTypes = Object.keys(body.content || {});
  const contentType = contentTypes.includes('application/json') ? 'application/json' : contentTypes[0] || null;
  if (contentType !== 'application/json') {
    return { hasOperation: true, hasBody: true, contentType, fields: null };
  }

  const schema = normalizeSchema(spec, body.content[contentType].schema);
  if (!schema.properties) {
    return { hasOperation: true, hasBody: true, contentType, fields: null };
  }
  const required = new Set(schema.required || []);
  const fields = Object.entries(schema.properties).map(([name, s]) => toField(spec, name, s, required));
  return { hasOperation: true, hasBody: true, contentType, fields };
}
