import {matches, scoreChange, maxWager, validWager, roundOrder} from './logic.mjs';
const app = document.querySelector('#app');
const money = n => `${n < 0 ? '−' : ''}$${Math.abs(n).toLocaleString()}`;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let episode, rounds, state, key, active = null, wager = null, result = null, storageWarning = false;
const score = () => Object.values(state.answers).reduce((sum, a) => sum + a.delta, 0);
const questions = () => episode.questions.filter(q => q.round === rounds[state.round]);
const isFinal = () => roundOrder(rounds[state.round]) === 3;
const done = () => questions().every(q => state.answers[q.id]);
const save = () => { try { localStorage.setItem(key, JSON.stringify(state)); } catch { storageWarning = true; } };
const date = value => new Date(`${value.slice(0,10)}T12:00:00`).toLocaleDateString(undefined, {month:'long', day:'numeric', year:'numeric'});
function top() {
  return `<div class="episode-meta">${episode.demo ? 'DEMO · ' : ''}${esc(date(episode.air_date))}</div>${episode.refresh_warning ? `<p class="hint" role="status">${esc(episode.refresh_warning)}</p>` : ''}`;
}
function bottom() {
  return `<div class="scorebar"><span class="eyebrow">YOUR SCORE</span><strong>${money(score())}</strong></div>${storageWarning ? '<p class="hint">Browser storage is unavailable. Progress will reset on refresh.</p>' : ''}`;
}
function board() {
  active = null; result = null; wager = null;
  const categories = [...new Set(questions().map(q => q.category))];
  app.innerHTML = top() + `<div class="categories ${isFinal()?'final-board':''}">${categories.map((name, i) =>
    `<section class="category"><button class="category-title" data-category="${i}" aria-haspopup="dialog"><h2>${esc(name)}</h2></button></section>`
  ).join('')}</div>${done()?`<div class="round-finish"><p>${state.round < rounds.length-1?'Board cleared. Ready for the next round?':'That’s the game. Nicely played.'}</p><button id="next" class="primary">${state.round < rounds.length-1?'Next round →':'See your results →'}</button></div>`:''}` + bottom();
  app.querySelectorAll('[data-category]').forEach(button => button.onclick = () => showCategory(categories[button.dataset.category]));
  const next = document.querySelector('#next');
  if(next) next.onclick = () => { if(state.round<rounds.length-1) {state.round++;save();board();} else summary(); };
  if(done() && state.round === rounds.length-1) addNewGameButton(app.querySelector('.round-finish'));
}
function showCategory(name) {
  const list = questions().filter(q => q.category === name).sort((a,b) => a.point_value-b.point_value);
  const dialog = document.createElement('dialog');
  dialog.className = 'category-picker';
  dialog.setAttribute('aria-labelledby', 'picker-title');
  dialog.innerHTML = `<h2 id="picker-title">${esc(name)}</h2><div class="values">${list.map(q => `<button class="value" data-question="${esc(q.id)}" ${state.answers[q.id]?'disabled':''}>${isFinal()?'Final clue':money(q.point_value)}${state.answers[q.id]?'<span>PLAYED</span>':''}</button>`).join('')}</div><button class="secondary" data-close>Back to categories</button>`;
  app.append(dialog);
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  dialog.addEventListener('close', () => dialog.remove(), {once:true});
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if(event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
  dialog.querySelectorAll('[data-question]').forEach(button => button.onclick = () => {
    active = list.find(q => q.id === button.dataset.question);
    dialog.close();
    clue();
  });
  dialog.showModal();
}
function clue() {
  const betting = active.is_daily_double || isFinal();
  if(betting && wager===null) return wagerScreen();
  app.innerHTML = top() + `<section class="clue-panel question-panel"><p class="clue-text">${esc(active.question)}</p><form id="answer-form"><input id="answer" name="answer" aria-label="Your answer" autocomplete="off" placeholder="Type your answer…" maxlength="500"><div class="actions"><button class="primary" type="submit">Submit</button>${!betting?'<button type="button" id="pass" class="secondary">Skip</button>':''}</div></form></section>` + bottom();
  document.querySelector('#answer-form').onsubmit = e => {e.preventDefault();grade(document.querySelector('#answer').value,false);};
  const pass = document.querySelector('#pass'); if(pass) pass.onclick=()=>grade('',true);
  document.querySelector('#answer').focus();
}
function wagerScreen() {
  const max=maxWager(score(),questions(),isFinal());
  app.innerHTML=top()+`<section class="clue-panel wager-panel"><span class="star">✦</span><p class="eyebrow">${isFinal()?'FINAL JEOPARDY':'YOU FOUND A DAILY DOUBLE'}</p><h2>Back yourself.</h2><p class="wager-category">${esc(active.category)}</p><p>Choose your wager before seeing the clue.</p><form id="wager-form"><label for="wager">Your wager · ${isFinal()?'0':'1'}–${money(max)}</label><input id="wager" type="number" min="${isFinal()?0:1}" max="${max}" step="1" required value="${Math.min(max,active.point_value||100)}"><p id="wager-error" role="alert"></p><button class="primary">Lock in wager →</button></form></section>`+bottom();
  document.querySelector('#wager-form').onsubmit=e=>{ e.preventDefault(); const value=document.querySelector('#wager').value;if(!validWager(value,max,isFinal())) {document.querySelector('#wager-error').textContent='Enter a whole number within the wager limits.';return;}wager=Number(value);clue();};
}
function grade(response,passed) {
  if(state.answers[active.id]) return;
  const correct=matches(response,active.answer), amount=wager??active.point_value;
  result={response,passed,correct,amount,delta:scoreChange(correct,passed,amount)};
  state.answers[active.id]=result;save();reveal();
}
function reveal() {
  app.innerHTML=top()+`<section class="clue-panel question-panel reveal"><p class="clue-text">${esc(active.answer)}</p><div class="actions"><button id="return" class="primary" aria-label="Back to the board">← Back</button></div></section>`+bottom();
  document.querySelector('#return').onclick=board;
  document.querySelector('#return').focus();
}

function summary() {
  const answers=Object.values(state.answers);
  app.innerHTML=top()+`<section class="clue-panel summary"><span class="star">✦</span><p class="eyebrow">EPISODE COMPLETE</p><h2>${money(score())}</h2><p>${answers.filter(a=>a.correct).length} correct · ${answers.filter(a=>!a.correct&&!a.passed).length} incorrect · ${answers.filter(a=>a.passed).length} passed</p><p>Ready for another board?</p><button class="secondary" id="review">Return to board</button></section>`+bottom();
  document.querySelector('#review').onclick=board;
  addNewGameButton(app.querySelector('.summary'));
}
async function fetchEpisode() {
  const response = await fetch('/api/episode', {cache:'no-store'});
  const data = await response.json();
  if(!response.ok) throw new Error(data.error || 'The episode could not be loaded.');
  if(!data.questions?.length) throw new Error('This episode has no questions.');
  return data;
}
function addNewGameButton(container) {
  const button = document.createElement('button');
  button.className = 'secondary';
  button.textContent = 'Check for a new game';
  const message = document.createElement('p');
  message.className = 'hint';
  message.setAttribute('role', 'status');
  container.append(button, message);
  button.onclick = async () => {
    button.disabled = true;
    message.textContent = 'Checking for a new board…';
    try {
      const next = await fetchEpisode();
      if(next.id === episode.id) {
        message.textContent = next.refresh_warning || 'No new board has been published yet. Check again after the next daily build.';
      } else {
        startEpisode(next);
      }
    } catch(error) {
      message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  };
}
function startEpisode(data) {
  episode = data;
  rounds=[...new Set(episode.questions.map(q=>q.round))].sort((a,b)=>roundOrder(a)-roundOrder(b));
  key=`daily-board-v1-${episode.id}`;state={round:0,answers:{}};
  try{const saved=JSON.parse(localStorage.getItem(key));if(saved&&Number.isInteger(saved.round)&&saved.round>=0&&saved.round<rounds.length&&saved.answers&&typeof saved.answers==='object')state=saved;}catch{storageWarning=true;}
  board();
}
try {
  startEpisode(await fetchEpisode());
} catch(error){app.innerHTML=`<section class="clue-panel"><h1>The board isn’t ready.</h1><p>${esc(error.message)}</p><p>Check your connection and the server terminal, then try again.</p><button class="primary" onclick="location.reload()">Try again</button></section>`;}
