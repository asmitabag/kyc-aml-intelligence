// Chart colours keyed by the words the backend uses. Unknown words get a neutral indigo/slate cycle.
const FIXED = [
  [/(critical|severe|high)/i, '#dc2626'],
  [/(medium|moderate|elevated)/i, '#d97706'],
  [/(low|minimal)/i, '#059669'],
  [/(reject|fail|block|unavailable)/i, '#dc2626'],
  [/(resolved|closed|approved|verified|completed)/i, '#059669'],
  [/(open|pending|new|review)/i, '#d97706'],
];
const CYCLE = ['#4f46e5', '#6366f1', '#818cf8', '#94a3b8', '#64748b', '#a5b4fc'];

export function colorFor(name, index = 0) {
  for (const [re, c] of FIXED) if (re.test(String(name))) return c;
  return CYCLE[index % CYCLE.length];
}
