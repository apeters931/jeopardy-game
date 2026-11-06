export function normalize(value) {
  return String(value).trim().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/^(what|who|where|when)\s+(is|are|was|were)\s+/, '')
    .replace(/&/g, ' and ').replace(/[-–—]/g, ' ').replace(/[^a-z0-9\s]/g, '').replace(/^(a|an|the)\s+/, '').replace(/\s+/g, ' ').trim();
}
// Adjacent transpositions count as one typo, just like an insertion or deletion.
function typoDistance(a, b) {
  const rows = Array.from({length:a.length + 1}, () => Array(b.length + 1).fill(0));
  for(let i=0; i<=a.length; i++) rows[i][0] = i;
  for(let j=0; j<=b.length; j++) rows[0][j] = j;
  for(let i=1; i<=a.length; i++) {
    for(let j=1; j<=b.length; j++) {
      rows[i][j] = Math.min(rows[i-1][j] + 1, rows[i][j-1] + 1,
        rows[i-1][j-1] + (a[i-1] === b[j-1] ? 0 : 1));
      if(i>1 && j>1 && a[i-1] === b[j-2] && a[i-2] === b[j-1]) {
        rows[i][j] = Math.min(rows[i][j], rows[i-2][j-2] + 1);
      }
    }
  }
  return rows[a.length][b.length];
}
export function matches(answer, expected) {
  const value = normalize(answer), target = normalize(expected);
  if(!value || !target) return false;
  if(value === target) return true;
  if(value.length > 500 || target.length > 500) return false;
  if(JSON.stringify(value.match(/[0-9]+/g)) !== JSON.stringify(target.match(/[0-9]+/g))) return false;
  // Ignore word spacing, but require every word and digit to remain present.
  if(value.replace(/ /g, '') === target.replace(/ /g, '')) return true;
  const words = value.split(' '), expectedWords = target.split(' ');
  if(words.length !== expectedWords.length) return false;
  let totalTypos = 0;
  for(let i=0; i<words.length; i++) {
    if(words[i] === expectedWords[i]) continue;
    const length = Math.min(words[i].length, expectedWords[i].length);
    // Short words and numbers are too easy to turn into a different answer.
    if(length < 5 || /[0-9]/.test(words[i] + expectedWords[i])) return false;
    const limit = length >= 10 ? 2 : 1;
    if(Math.abs(words[i].length - expectedWords[i].length) > limit) return false;
    const typos = typoDistance(words[i], expectedWords[i]);
    if(typos > limit) return false;
    totalTypos += typos;
  }
  return totalTypos <= (target.replace(/ /g, '').length >= 10 ? 2 : 1);
}
export function countAsCorrect(answer) {
  if(answer.correct || answer.passed || !answer.response.trim()) return answer;
  return {...answer, correct:true, delta:answer.amount, selfGraded:true};
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
