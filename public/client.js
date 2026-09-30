const socket = io();
let state = null;
let cards = [];
let shows = [];
let selectedCard = null;
let selectedTargetSeat = null;
let selectedShows = [];
let previewShow = null;
let libraryStar = 'all';
let libraryShow = 'all';

const $ = id => document.getElementById(id);
const lobby = $('lobby'), waiting = $('waiting'), game = $('game');
const teamOfSeat = seat => Number(seat) % 2;
const teamLetter = seat => teamOfSeat(seat) === 0 ? 'A' : 'B';

Promise.all([fetch('/api/cards').then(r=>r.json()), fetch('/api/shows').then(r=>r.json())]).then(([c,s]) => {
  cards = c; shows = s;
  renderShowPicker(); renderLibraryTabs(); renderLibrary();
});

$('createBtn').onclick = () => socket.emit('createRoom', { name: $('nameInput').value.trim() || 'Player' });
$('joinBtn').onclick = () => socket.emit('joinRoom', { code: $('roomInput').value, name: $('nameInput').value.trim() || 'Player' });
$('roomInput').addEventListener('keydown', e => { if (e.key === 'Enter') $('joinBtn').click(); });
$('punchBtn').onclick = () => {
  const targetSeat = getPunchTargetSeat();
  if (targetSeat == null) return toast('Choose a living teammate or enemy first.');
  socket.emit('punch', { targetSeat });
};
$('endBtn').onclick = () => socket.emit('endTurn');
$('copyCodeBtn').onclick = async () => { if (!state) return; await navigator.clipboard?.writeText(state.code); toast('Room code copied.'); };
$('targetSelect').onchange = e => { selectedTargetSeat = Number(e.target.value); syncDialogTarget(); };
$('cardTargetSelect').onchange = e => { selectedTargetSeat = Number(e.target.value); if ([...$('targetSelect').options].some(o=>Number(o.value)===selectedTargetSeat)) $('targetSelect').value = String(selectedTargetSeat); };
$('showSearch').oninput = renderShowPicker;
$('readyDeckBtn').onclick = () => {
  if (selectedShows.length !== 3) return toast('Choose exactly 3 shows.');
  socket.emit('setDeck', { shows: selectedShows });
};

socket.on('state', s => {
  state = s;
  if (state.you?.selectedShows?.length && !state.you.ready) selectedShows = [...state.you.selectedShows];
  if (state.you?.ready) selectedShows = [...state.you.selectedShows];
  if (state.shows?.length) shows = state.shows;
  renderState();
});
socket.on('errorMessage', toast);

function renderState() {
  if (!state) return;
  if (state.phase === 'waiting') {
    lobby.classList.add('hidden'); game.classList.add('hidden'); waiting.classList.remove('hidden');
    $('waitingCode').textContent = state.code;
    const count = state.players?.length || 1;
    const ready = (state.players || []).filter(p => p.ready).length;
    $('waitingStatus').textContent = count < 4 ? `Waiting for ${4-count} more player${4-count===1?'':'s'} · ${ready}/${count} decks ready` : `${ready}/4 decks ready — match starts automatically when everyone locks a deck.`;
    renderWaitingRoster(); renderShowPicker(); renderSelectedShows(); renderShowPreview();
    $('readyDeckBtn').disabled = state.you.ready || selectedShows.length !== 3;
    $('readyDeckBtn').textContent = state.you.ready ? 'Deck locked ✓' : 'Lock deck & ready';
    return;
  }

  waiting.classList.add('hidden'); lobby.classList.add('hidden'); game.classList.remove('hidden');
  $('roomCode').textContent = state.code;
  $('turnNumber').textContent = state.turn.number;
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
  (state.players||[]).slice().sort((a,b)=>a.seat-b.seat).forEach(p=>{
    const d=document.createElement('div'); d.className=`roster-seat team-${teamLetter(p.seat).toLowerCase()}`;
    d.innerHTML=`<span>Team ${teamLetter(p.seat)} · P${Math.floor(p.seat/2)+1}</span><b>${escapeHtml(p.name)}</b>${p.isSelf?'<em>YOU</em>':''}<span class="${p.ready?'ready-badge':'not-ready-badge'}">${p.ready?'READY':`${p.selectedShowCount||0}/3 SHOWS`}</span>`;
    el.appendChild(d);
  });
  for(let i=(state.players||[]).length;i<4;i++){
    const d=document.createElement('div'); d.className='roster-seat empty'; d.innerHTML='<span>OPEN SEAT</span><b>Waiting…</b>'; el.appendChild(d);
  }
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
        if(selectedShows.includes(show)) selectedShows=selectedShows.filter(x=>x!==show);
        else if(selectedShows.length<3) selectedShows.push(show);
        else toast('You can only choose 3 shows.');
      }
      renderShowPicker(); renderSelectedShows(); renderShowPreview();
      if (state?.phase==='waiting') $('readyDeckBtn').disabled = state.you.ready || selectedShows.length!==3;
    };
    el.appendChild(b);
  });
}

function renderSelectedShows(){
  const el=$('selectedShows'); if(!el)return; el.innerHTML='';
  selectedShows.forEach(show=>{ const s=document.createElement('span'); s.className='selected-show'; s.textContent=show; el.appendChild(s); });
  $('deckSelectionTitle').textContent=`${selectedShows.length} / 3 shows selected${selectedShows.length===3?' · 48 cards':''}`;
}

function renderShowPreview(){
  const el=$('showPreview'); if(!el)return; el.innerHTML='';
  const show=previewShow || selectedShows[selectedShows.length-1];
  if(!show){ el.innerHTML='<p class="micro">Click a show to preview its 16 cards.</p>'; return; }
  cards.filter(c=>(c.show||c.origin)===show).sort((a,b)=>a.stars-b.stars||a.id-b.id).forEach(c=>el.appendChild(makeCard(c)));
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
  $('librarySummary').textContent=libraryShow==='all'?`${list.length} cards across ${shows.length} shows`:`${libraryShow}: ${list.length} shown · full package is 10×3★, 5×4★, 1×5★`;
}
function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));}
