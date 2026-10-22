export function normalize(value) {
  return String(value).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/^(what|who|where|when)\s+(is|are|was|were)\s+/, '')
    .replace(/&/g, ' and ').replace(/[^a-z0-9\s]/g, '').replace(/^(a|an|the)\s+/, '').replace(/\s+/g, ' ').trim();
}
export function matches(answer, expected) {
  const value = normalize(answer);
  return Boolean(value) && value === normalize(expected);
}
export function scoreChange(correct, passed, amount) { return passed ? 0 : correct ? amount : -amount; }
export function maxWager(score, questions, final = false) {
  return final ? Math.max(0, score) : Math.max(score, ...questions.map(q => q.point_value), 1);
}
export function validWager(value, max, final = false) {
  return String(value).trim() !== '' && Number.isInteger(Number(value)) && Number(value) >= (final ? 0 : 1) && Number(value) <= max;
}
export function roundOrder(value) {
  if (/final/i.test(value) || String(value) === '3') return 3;
  if (/double/i.test(value) || String(value) === '2') return 2;
  return 1;
}
