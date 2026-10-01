const socket = io();
let state = null;
let cards = [];
let shows = [];
let selectedCard = null;
let selectedTargetSeat = null;
let selectedShows = [];
let selectedCardIds = new Set();
let previewShow = null;
let libraryStar = 'all';
let libraryShow = 'all';

const $ = id => document.getElementById(id);
const lobby = $('lobby'), waiting = $('waiting'), game = $('game');
const teamOfSeat = seat => Number(seat) % 2;
const teamLetter = seat => teamOfSeat(seat) === 0 ? 'A' : 'B';
const deckNeed = star => Number(state?.config?.cardsPerShow?.[String(star)] ?? ({3:10,4:5,5:1})[star]);
const poolSize = star => Number(state?.config?.poolCardsPerShow?.[String(star)] ?? ({3:15,4:7,5:2})[star]);

Promise.all([fetch('/api/cards').then(r=>r.json()), fetch('/api/shows').then(r=>r.json())]).then(([c,s]) => {
  cards = c; shows = s;
  renderShowPicker(); renderLibraryTabs(); renderLibrary();
});

$('createBtn').onclick = () => socket.emit('createRoom', {
  name: $('nameInput').value.trim() || 'Player',
  mode: $('modeSelect').value,
});
$('joinBtn').onclick = () => socket.emit('joinRoom', { code: $('roomInput').value, name: $('nameInput').value.trim() || 'Player' });
$('roomInput').addEventListener('keydown', e => { if (e.key === 'Enter') $('joinBtn').click(); });
$('punchBtn').onclick = () => {
  const targetSeat = getPunchTargetSeat();
  if (targetSeat == null) return toast('Choose another living player first.');
  socket.emit('punch', { targetSeat });
};
$('endBtn').onclick = () => socket.emit('endTurn');
$('copyCodeBtn').onclick = async () => { if (!state) return; await navigator.clipboard?.writeText(state.code); toast('Room code copied.'); };
$('targetSelect').onchange = e => { selectedTargetSeat = Number(e.target.value); syncDialogTarget(); };
$('cardTargetSelect').onchange = e => { selectedTargetSeat = Number(e.target.value); if ([...$('targetSelect').options].some(o=>Number(o.value)===selectedTargetSeat)) $('targetSelect').value = String(selectedTargetSeat); };
$('showSearch').oninput = renderShowPicker;
$('readyDeckBtn').onclick = () => {
  const problem = deckProblem();
  if (problem) return toast(problem);
  socket.emit('setDeck', { shows: selectedShows, cardIds: [...selectedCardIds] });
};

socket.on('state', s => {
  state = s;
  if (state.you?.ready) {
    selectedShows = [...(state.you.selectedShows || [])];
    selectedCardIds = new Set(state.you.selectedCardIds || []);
  }
  if (state.shows?.length) shows = state.shows;
  renderState();
});
socket.on('errorMessage', toast);

function renderState() {
  if (!state) return;
  $('brandMode').textContent = state.mode?.toUpperCase() || '1v1 / 2v2';
  if (state.phase === 'waiting') {
    lobby.classList.add('hidden'); game.classList.add('hidden'); waiting.classList.remove('hidden');
    $('waitingCode').textContent = state.code;
    $('waitingModeLabel').textContent = `${(state.mode || '2v2').toUpperCase()} ROOM`;
    const count = state.players?.length || 1;
    const need = state.requiredPlayers || 4;
    const ready = (state.players || []).filter(p => p.ready).length;
    $('waitingStatus').textContent = count < need
      ? `Waiting for ${need-count} more player${need-count===1?'':'s'} · ${ready}/${count} decks ready`
      : `${ready}/${need} decks ready — match starts automatically when everyone locks a deck.`;
    renderWaitingRoster(); renderShowPicker(); renderSelectedShows(); renderShowPreview();
    $('readyDeckBtn').disabled = state.you.ready || !!deckProblem();
    $('readyDeckBtn').textContent = state.you.ready ? 'Deck locked ✓' : 'Lock deck & ready';
    return;
  }

  waiting.classList.add('hidden'); lobby.classList.add('hidden'); game.classList.remove('hidden');
  $('roomCode').textContent = state.code;
  $('turnNumber').textContent = state.turn.number;
  $('vsMode').innerHTML = state.mode === '1v1' ? '1 <span>VS</span> 1' : '2 <span>VS</span> 2';
  const myTurn = state.turn.seat === state.you.seat && state.phase === 'playing';
  $('turnText').textContent = state.phase === 'finished' ? `${state.winner}` : myTurn ? 'Your turn' : `${state.turn.currentName}'s turn`;
  $('matchBanner').textContent = state.phase === 'finished' ? `${state.winner}` : myTurn ? 'YOUR TURN' : `Waiting for ${state.turn.currentName}`;
  $('yourTeamLetter').textContent = teamLetter(state.you.seat);
  $('enemyTeamLetter').textContent = teamLetter(state.you.seat) === 'A' ? 'B' : 'A';
  renderTargets(); renderBoard(); renderHand(state.you.hand || [], myTurn); renderLog();
  $('deckCount').textContent = `${state.you.deckCount} deck`;

  $('punchBtn').disabled = !myTurn || (state.turn.mainActionUsed && !state.turn.extraPunchAllowed);
  $('endBtn').disabled = !myTurn;
  $('actionHint').textContent = !myTurn ? 'Another player is choosing…'
    : state.turn.goldenPairRequired ? `Must play ${state.turn.goldenPairRequired}`
    : state.turn.cardsPlayed < state.turn.cardPlayLimit ? `${state.turn.cardPlayLimit - state.turn.cardsPlayed} card play${state.turn.cardPlayLimit - state.turn.cardsPlayed === 1 ? '' : 's'} available`
    : !state.turn.mainActionUsed ? 'Choose one card or punch' : 'Main action used — end turn when ready';
  if (state.phase === 'finished') $('punchBtn').disabled = $('endBtn').disabled = true;
}

function renderWaitingRoster() {
  const el = $('waitingRoster'); el.innerHTML='';
  const need = state.requiredPlayers || 4;
  (state.players||[]).slice().sort((a,b)=>a.seat-b.seat).forEach(p=>{
    const d=document.createElement('div'); d.className=`roster-seat team-${teamLetter(p.seat).toLowerCase()}`;
    const slot = state.mode === '1v1' ? 'SOLO' : `P${Math.floor(p.seat/2)+1}`;
    d.innerHTML=`<span>Team ${teamLetter(p.seat)} · ${slot}</span><b>${escapeHtml(p.name)}</b>${p.isSelf?'<em>YOU</em>':''}<span class="${p.ready?'ready-badge':'not-ready-badge'}">${p.ready?'READY':`${p.selectedCardCount||0}/48 CARDS`}</span>`;
    el.appendChild(d);
  });
  for(let i=(state.players||[]).length;i<need;i++){
    const d=document.createElement('div'); d.className='roster-seat empty'; d.innerHTML='<span>OPEN SEAT</span><b>Waiting…</b>'; el.appendChild(d);
  }
}

function showCards(show, star=null) {
  return cards.filter(c => (c.show||c.origin)===show && (star == null || Number(c.stars)===Number(star))).sort((a,b)=>a.stars-b.stars||a.id-b.id);
}
function selectedCount(show, star) {
  return showCards(show, star).filter(c=>selectedCardIds.has(c.id)).length;
}
function autoSelectShow(show) {
  for (const star of [3,4,5]) {
    showCards(show,star).slice(0, deckNeed(star)).forEach(c=>selectedCardIds.add(c.id));
  }
}
function removeShowCards(show) {
  showCards(show).forEach(c=>selectedCardIds.delete(c.id));
}
function deckProblem() {
  if (selectedShows.length !== 3) return 'Choose exactly 3 shows.';
  if (selectedCardIds.size !== 48) return `Your deck needs exactly 48 cards. You currently have ${selectedCardIds.size}.`;
  for (const show of selectedShows) {
    for (const star of [3,4,5]) {
      const got = selectedCount(show,star), need = deckNeed(star);
      if (got !== need) return `${show} needs exactly ${need} ${star}★ card${need===1?'':'s'}; you selected ${got}.`;
    }
  }
  return '';
}
function toggleDeckCard(card) {
  if (state?.you?.ready) return;
  const show = card.show || card.origin;
  if (!selectedShows.includes(show)) return toast('Select this show first.');
  if (selectedCardIds.has(card.id)) selectedCardIds.delete(card.id);
  else {
    const current = selectedCount(show,card.stars);
    const max = deckNeed(card.stars);
    if (current >= max) return toast(`You already selected ${max} ${card.stars}★ cards from ${show}. Remove one first.`);
    selectedCardIds.add(card.id);
  }
  renderSelectedShows(); renderShowPreview();
  $('readyDeckBtn').disabled = state.you.ready || !!deckProblem();
}

function renderShowPicker(){
  if (!$('showPicker')) return;
  const q=($('showSearch')?.value||'').toLowerCase();
  const el=$('showPicker'); el.innerHTML='';
  shows.filter(s=>s.toLowerCase().includes(q)).forEach(show=>{
    const b=document.createElement('button'); b.className=`show-chip ${selectedShows.includes(show)?'selected':''}`; b.textContent=show;
    b.onclick=()=>{
      previewShow=show;
      if (!state?.you?.ready) {
        if(selectedShows.includes(show)) { selectedShows=selectedShows.filter(x=>x!==show); removeShowCards(show); }
        else if(selectedShows.length<3) { selectedShows.push(show); autoSelectShow(show); }
        else toast('You can only choose 3 shows.');
      }
      renderShowPicker(); renderSelectedShows(); renderShowPreview();
      if (state?.phase==='waiting') $('readyDeckBtn').disabled = state.you.ready || !!deckProblem();
    };
    el.appendChild(b);
  });
}

function renderSelectedShows(){
  const el=$('selectedShows'); if(!el)return; el.innerHTML='';
  selectedShows.forEach(show=>{
    const s=document.createElement('span'); s.className='selected-show';
    s.textContent=`${show} · ${showCards(show).filter(c=>selectedCardIds.has(c.id)).length}/16`;
    el.appendChild(s);
  });
  $('deckSelectionTitle').textContent=`${selectedShows.length} / 3 shows · ${selectedCardIds.size} / 48 cards`;
}

function renderShowPreview(){
  const el=$('showPreview'); if(!el)return; el.innerHTML='';
  const meta=$('showPreviewMeta'); if(meta) meta.innerHTML='';
  const show=previewShow || selectedShows[selectedShows.length-1];
  if(!show){ el.innerHTML='<p class="micro">Click a show to preview its 24-card pool.</p>'; return; }
  const isChosen=selectedShows.includes(show);
  if(meta){
    const parts=[3,4,5].map(star=>`${selectedCount(show,star)}/${deckNeed(star)} selected from ${poolSize(star)} ${star}★`);
    meta.innerHTML=`<b>${escapeHtml(show)}</b><span>${parts.join(' · ')}</span><small>${isChosen?'Click a card to add/remove it from your 16-card show package.':'Select this show above before choosing cards.'}</small>`;
  }
  showCards(show).forEach(c=>{
    const n=makeCard(c);
    n.classList.add('deck-pool-card');
    n.classList.toggle('deck-selected',selectedCardIds.has(c.id));
    n.classList.toggle('deck-unselected',isChosen && !selectedCardIds.has(c.id));
    n.onclick=()=> isChosen ? toggleDeckCard(c) : showCard(c,false);
    el.appendChild(n);
  });
}

function renderTargets(){
  const others=(state.players||[]).filter(p=>!p.isSelf&&p.hp>0).sort((a,b)=>a.seat-b.seat);
  const cardCandidates=(state.players||[]).filter(p=>p.hp>0).sort((a,b)=>a.seat-b.seat);
  if(!cardCandidates.some(p=>p.seat===selectedTargetSeat)){
    const firstEnemy=others.find(p=>teamOfSeat(p.seat)!==teamOfSeat(state.you.seat));
    selectedTargetSeat=firstEnemy?.seat??others[0]?.seat??state.you?.seat??null;
  }
  fillTargetSelect($('targetSelect'),others);
  fillTargetSelect($('cardTargetSelect'),cardCandidates);
}
function fillTargetSelect(select,candidates){
  select.innerHTML='';
  candidates.forEach(p=>{
    const o=document.createElement('option'); o.value=p.seat;
    const rel=p.isSelf?'You':teamOfSeat(p.seat)===teamOfSeat(state.you.seat)?'Teammate':'Enemy';
    o.textContent=`${p.name} — ${rel} (${p.hp} HP)`; o.selected=p.seat===selectedTargetSeat; select.appendChild(o);
  });
}
function syncDialogTarget(){ if(selectedTargetSeat!=null)$('cardTargetSelect').value=String(selectedTargetSeat); }
function getPunchTargetSeat(){ const x=(state.players||[]).find(p=>p.seat===Number(selectedTargetSeat)&&!p.isSelf&&p.hp>0); return x?.seat??(state.players||[]).find(p=>!p.isSelf&&p.hp>0)?.seat??null; }

function renderBoard(){
  const enemyGrid=$('enemyGrid'),allyGrid=$('allyGrid'); enemyGrid.innerHTML=''; allyGrid.innerHTML='';
  (state.enemies||[]).sort((a,b)=>a.seat-b.seat).forEach(p=>enemyGrid.appendChild(makePlayerTile(p,'enemy')));
  [state.you,state.teammate].filter(Boolean).sort((a,b)=>a.seat-b.seat).forEach(p=>allyGrid.appendChild(makePlayerTile(p,p.isSelf?'self':'ally')));
}
function makePlayerTile(p,kind){
  const tile=document.createElement('article'); tile.className=`player-tile glass ${kind} ${p.hp<=0?'dead':''} ${state.turn.seat===p.seat&&state.phase==='playing'?'active-turn':''}`;
  const pct=Math.max(0,Math.min(100,p.hp/state.config.startingHp*100));
  const handPreview=p.hand?.length?`<div class="revealed-hand">${p.hand.map(c=>`<span>${escapeHtml(c.name)}</span>`).join('')}</div>`:`<div class="mini-backs">${Array.from({length:Math.min(p.handCount,10)},()=>'<i></i>').join('')}${p.handCount>10?`<b>+${p.handCount-10}</b>`:''}</div>`;
  const buffs=(p.buffs||[]).map(b=>`<span class="buff">${escapeHtml(b)}</span>`).join('');
  const relation=p.isSelf?'YOU':teamOfSeat(p.seat)===teamOfSeat(state.you.seat)?'TEAMMATE':'ENEMY';
  tile.innerHTML=`<div class="player-line"><div><span class="label">TEAM ${teamLetter(p.seat)} · ${relation}</span><h2>${escapeHtml(p.name)}</h2></div><div class="hp-number"><b>${p.hp}</b><span>HP</span></div></div><div class="hpbar"><div style="width:${pct}%"></div></div><div class="status-row">${p.armor?`<span class="armor">◆ ${p.armor} armor</span>`:''}<div class="buffs">${buffs}</div></div><div class="tile-bottom"><div>${handPreview}</div><span class="discard-mini">Deck ${p.deckCount} · Discard ${p.discardCount}</span></div>`;
  if(!p.isSelf&&p.hp>0) tile.onclick=()=>{selectedTargetSeat=p.seat;renderTargets();tile.classList.add('target-flash');setTimeout(()=>tile.classList.remove('target-flash'),250);};
  return tile;
}

function renderHand(hand,myTurn){
  const el=$('yourHand'); el.innerHTML=''; $('handCount').textContent=`${hand.length} card${hand.length===1?'':'s'}`;
  hand.forEach(card=>{const n=makeCard(card); n.onclick=()=>showCard(card,myTurn&&state.phase==='playing'); el.appendChild(n);});
}
function makeCard(card){
  const d=document.createElement('article'); d.className=`tcg-card ${card.stars===3?'three':card.stars===4?'four':'five'}`;
  d.innerHTML=`<div class="stars">${'★'.repeat(card.stars)}</div><h4>${escapeHtml(card.name)}</h4><div class="origin">${escapeHtml(card.show||card.origin||'Fanmade')}</div><p>${escapeHtml(card.effect)}</p><span class="corner">#${card.id}</span>`; return d;
}
function showCard(card,playable){
  selectedCard=playable?card:null; const cls=card.stars===3?'three':card.stars===4?'four':'five';
  $('cardDetail').innerHTML=`<div class="card-detail-card ${cls}"><div class="stars">${'★'.repeat(card.stars)}</div><h2>${escapeHtml(card.name)}</h2><div class="series">${escapeHtml(card.show||card.origin||'Fanmade')}</div><p>${escapeHtml(card.effect)}</p></div>`;
  $('playCardBtn').classList.toggle('hidden',!playable); $('cardTargetRow').classList.toggle('hidden',!playable||!(state?.players?.length>1)); syncDialogTarget(); $('cardDialog').showModal();
}
$('cancelCardBtn').onclick=()=>$('cardDialog').close();
$('playCardBtn').onclick=()=>{if(selectedCard)socket.emit('playCard',{cardId:selectedCard.id,targetSeat:selectedTargetSeat});$('cardDialog').close();};

function renderLog(){const el=$('battleLog');el.innerHTML='';[...(state.log||[])].reverse().forEach(x=>{const d=document.createElement('div');d.className='log-item';d.textContent=x.text;el.appendChild(d);});}
function toast(message){const t=$('toast');t.textContent=message;t.classList.remove('hidden');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>t.classList.add('hidden'),3200);}
$('clearToastBtn').onclick=()=>$('toast').classList.add('hidden');

$('libraryBtn').onclick=()=>{$('libraryDialog').showModal();renderLibraryTabs();renderLibrary();};
$('closeLibraryBtn').onclick=()=>$('libraryDialog').close();
$('cardSearch').oninput=renderLibrary;
document.querySelectorAll('.filters button').forEach(btn=>btn.onclick=()=>{libraryStar=btn.dataset.star;document.querySelectorAll('.filters button').forEach(b=>b.classList.toggle('active',b===btn));renderLibrary();});
function renderLibraryTabs(){
  const el=$('libraryShowTabs');if(!el)return;el.innerHTML='';
  ['all',...shows].forEach(show=>{const b=document.createElement('button');b.textContent=show==='all'?'All shows':show;b.classList.toggle('active',show===libraryShow);b.onclick=()=>{libraryShow=show;renderLibraryTabs();renderLibrary();};el.appendChild(b);});
}
function renderLibrary(){
  if(!cards.length)return; const q=($('cardSearch')?.value||'').toLowerCase();
  const list=cards.filter(c=>(libraryStar==='all'||String(c.stars)===libraryStar)&&(libraryShow==='all'||(c.show||c.origin)===libraryShow)&&`${c.name} ${c.show||c.origin} ${c.effect}`.toLowerCase().includes(q));
  const grid=$('libraryGrid');grid.innerHTML='';list.forEach(c=>{const n=makeCard(c);n.onclick=()=>showCard(c,false);grid.appendChild(n);});
  $('librarySummary').textContent=libraryShow==='all'?`${list.length} cards across ${shows.length} shows`:`${libraryShow}: ${list.length} shown · pool 15×3★, 7×4★, 2×5★ · deck picks 10/5/1`;
}
function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));}
