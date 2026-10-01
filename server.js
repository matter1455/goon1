const path = require('path');
const http = require('http');
const express = require('express');
const { Server } = require('socket.io');
const CARDS = require('./data/cards.json');
const SETTINGS = require('./game-settings.json');

// Core rules are sourced from game-settings.json.
const PORT = process.env.PORT || 3000;
const STARTING_HP = SETTINGS.startingHp;
const BASE_PUNCH_DAMAGE = SETTINGS.basePunchDamage;
const STARTING_HAND_SIZE = SETTINGS.startingHandSize;
const SHOWS_PER_DECK = SETTINGS.showsPerDeck;
const DECK_SIZE = SETTINGS.deckSize;
const CARDS_PER_SHOW = SETTINGS.cardsPerShow;
const POOL_CARDS_PER_SHOW = SETTINGS.poolCardsPerShow || { '3': 20, '4': 10, '5': 3 };
const MIN_ENVIRONMENTS_PER_SHOW = Number(SETTINGS.minEnvironmentsPerShow || 3);
const SHOWS = [...new Set(CARDS.map(c => c.show || c.origin))].sort();
// Card-specific gamble effects still use these internal odds; there is no base gamble action.
const STANDARD_GAMBLE = {3: 0.70, 4: 0.25, 5: 0.05};
const BETTER_GAMBLE = {3: 0.50, 4: 0.35, 5: 0.15};

const FRIENDLY_FIRE_DAMAGE_CARDS = new Set([
  'explosion', 'rassengan', 'hit the nape', 'pull the chord', 'kagune',
  'thunder spear', 'one punch', 'seeing stars', 'excalibur'
]);

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });
app.use(express.static(path.join(__dirname, 'public')));
app.get('/api/cards', (_req, res) => res.json(CARDS));
app.get('/api/config', (_req, res) => res.json({ startingHp: STARTING_HP, basePunchDamage: BASE_PUNCH_DAMAGE, startingHandSize: STARTING_HAND_SIZE, showsPerDeck: SHOWS_PER_DECK, deckSize: DECK_SIZE, cardsPerShow: CARDS_PER_SHOW, poolCardsPerShow: POOL_CARDS_PER_SHOW, minEnvironmentsPerShow: MIN_ENVIRONMENTS_PER_SHOW }));
app.get('/api/shows', (_req, res) => res.json(SHOWS));

const rooms = new Map();

function roomCode() {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  for (let tries = 0; tries < 100; tries++) {
    let code = '';
    for (let i = 0; i < 5; i++) code += alphabet[Math.floor(Math.random() * alphabet.length)];
    if (!rooms.has(code)) return code;
  }
  return Math.random().toString(36).slice(2, 7).toUpperCase();
}

function shuffle(items) {
  const a = [...items];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function blankBuffs() {
  return {
    untargetableUntilOwnTurn: false,
    nextDamageMultiplier: 1,
    nextDamageFlatReduction: 0,
    nextAttackMultiplier: 1,
    nextAttackFlatBonus: 0,
    nextAttackMarkedBonus: 0,
    punchDamageOverrideTurns: 0,
    punchDamageOverride: BASE_PUNCH_DAMAGE,
    punchImmunityCharges: 0,
    punchesTakeOne: false,
    infinityCharges: 0,
    berserkReflect: false,
    reviveAt80: false,
    cannotHealTurns: 0,
    damageCap: null,
    damageCapUntilOwnTurn: false,
    cannotDropBelowOne: false,
    cannotDropBelowOneUntilOwnTurn: false,
    deathNoteTurns: null,
    deathNoteSourceSeat: null,
    delayedTeamRocket: [],
    zoltraakTicks: 0,
    heliocentricPunish: false,
    skipTurns: 0,
    forceSelfPunch: false,
    blockCardId: null,
    randomNextCard: false,
    bondForger: false,
    worldItemUntilOwnTurn: false,
    attackBoostTurns: 0,
    damageTakenMultiplierTurns: 0,
    persistentDamageTakenMultiplier: 1,
    persistentAttackMultiplier: 1,
    overleveledUntilOwnTurn: false,
    overloadReturnDamage: 0,
    undertakerArmed: false,
    delayedDamage: [],
    bonusNextDraw: 0,
    mustPunchTurns: 0,
  };
}

function makePlayer(socket, name, seat) {
  return {
    socketId: socket.id,
    name: String(name || `Player ${seat + 1}`).slice(0, 24),
    seat,
    hp: STARTING_HP,
    armor: 0,
    hand: [],
    discard: [],
    deck: [],
    selectedShows: [],
    selectedCardIds: [],
    ready: false,
    rematchReady: false,
    firstTurnTaken: false,
    buffs: blankBuffs(),
  };
}

function defaultCardIdsForShows(shows) {
  const ids = [];
  for (const show of shows) {
    const pool = CARDS.filter(c => (c.show || c.origin) === show).sort((a,b)=>a.id-b.id);
    const picked = [];
    // Make the default deck environment-heavy enough to demonstrate the board fight.
    const envs = pool.filter(c => c.cardType === 'environment');
    picked.push(...envs.slice(0, MIN_ENVIRONMENTS_PER_SHOW));
    for (const star of [3,4,5]) {
      const need = Number(CARDS_PER_SHOW[String(star)]);
      const already = picked.filter(c => Number(c.stars) === star).length;
      const fill = pool.filter(c => Number(c.stars) === star && !picked.some(x => x.id === c.id)).slice(0, Math.max(0, need - already));
      picked.push(...fill);
    }
    ids.push(...picked.map(c=>c.id));
  }
  return ids;
}

function buildDeckForSelection(shows, cardIds) {
  if (!Array.isArray(shows) || shows.length !== SHOWS_PER_DECK) return null;
  const uniqueShows = [...new Set(shows)];
  if (uniqueShows.length !== SHOWS_PER_DECK || uniqueShows.some(x => !SHOWS.includes(x))) return null;

  let ids = Array.isArray(cardIds) ? [...new Set(cardIds.map(Number).filter(Number.isFinite))] : [];
  if (!ids.length) ids = defaultCardIdsForShows(uniqueShows);
  if (ids.length !== DECK_SIZE) return null;

  const chosen = ids.map(getCard);
  if (chosen.some(c => !c)) return null;
  if (chosen.some(c => !uniqueShows.includes(c.show || c.origin))) return null;

  for (const show of uniqueShows) {
    const cards = chosen.filter(c => (c.show || c.origin) === show);
    const counts = {3:0,4:0,5:0};
    cards.forEach(c => counts[c.stars]++);
    if (counts[3] !== Number(CARDS_PER_SHOW['3']) || counts[4] !== Number(CARDS_PER_SHOW['4']) || counts[5] !== Number(CARDS_PER_SHOW['5'])) return null;
    if (cards.filter(c => c.cardType === 'environment').length < MIN_ENVIRONMENTS_PER_SHOW) return null;
  }
  return ids;
}

function preparePlayerDeck(p) {
  p.hp = STARTING_HP; p.armor = 0; p.hand = []; p.discard = []; p.buffs = blankBuffs(); p.firstTurnTaken = false; p.rematchReady = false;
  p.deck = shuffle(buildDeckForSelection(p.selectedShows, p.selectedCardIds) || []);
  for (let i = 0; i < STARTING_HAND_SIZE; i++) drawCard(p);
}

function getCard(id) { return CARDS.find(c => c.id === Number(id)); }
function teamOf(p) { return p.seat % 2; }
function terrainForTeam(room, team) {
  const env = room.environment || null;
  return env && Number(env.ownerTeam) === Number(team) ? env : null;
}
function setTerrain(room, p, card, action) {
  const team = teamOf(p);
  const previous = room.environment || null;
  if (previous) log(room, `${card.name} replaced ${previous.name} as the Environment.`);
  room.environment = {
    name: card.name,
    show: card.show || card.origin || '',
    kind: action.terrainKind,
    amount: Number(action.amount) || 0,
    ownerTeam: team,
  };
  log(room, `Team ${team===0?'A':'B'} controls the Environment: ${card.name}.`);
}
function tickTerrainAfterTurn(_room, _p) {
  // Environments persist until another Environment card replaces them.
}

function teammates(room, p) { return room.players.filter(x => x.socketId !== p.socketId && teamOf(x) === teamOf(p)); }
function teammate(room, p) { return teammates(room, p)[0] || null; }
function enemies(room, p) { return room.players.filter(x => teamOf(x) !== teamOf(p)); }
function aliveEnemies(room, p) { return enemies(room, p).filter(x => x.hp > 0); }
function playerBySeat(room, seat) { return room.players.find(x => x.seat === Number(seat)); }
function otherPlayer(room, p, preferredSeat = null) {
  const preferred = playerBySeat(room, preferredSeat);
  if (preferred && teamOf(preferred) !== teamOf(p) && preferred.hp > 0) return preferred;
  return aliveEnemies(room, p)[0] || enemies(room, p)[0] || null;
}
function allyTarget(room, p, preferredSeat = null) {
  const preferred = playerBySeat(room, preferredSeat);
  if (preferred && teamOf(preferred) === teamOf(p) && preferred.hp > 0) return preferred;
  return teammate(room, p) || p;
}
function currentPlayer(room) { return room.players.find(p => p.seat === room.turn.seat); }
function playerBySocket(room, socketId) { return room.players.find(p => p.socketId === socketId); }

function drawCard(player) {
  const id = player.deck.pop();
  if (id) player.hand.push(id);
  return id || null;
}

function drawCards(player, count = 1) {
  const gained = [];
  for (let i = 0; i < count; i++) { const id = drawCard(player); if (id) gained.push(id); }
  return gained;
}

function drawStar(player, stars) {
  const idx = [...player.deck].reverse().findIndex(id => getCard(id)?.stars === Number(stars));
  if (idx < 0) return null;
  const real = player.deck.length - 1 - idx;
  const [id] = player.deck.splice(real, 1);
  player.hand.push(id);
  return id;
}

function weightedStar(odds) {
  const r = Math.random(); let acc = 0;
  for (const st of [3,4,5]) { acc += odds[st]; if (r <= acc) return st; }
  return 3;
}
function gambleDraw(player, odds = STANDARD_GAMBLE, count = 1) {
  const gained = [];
  for (let i=0;i<count;i++) { const id = drawStar(player, weightedStar(odds)) || drawCard(player); if (id) gained.push(id); }
  return gained;
}

function log(room, text) {
  room.log.push({ id: `${Date.now()}-${Math.random()}`, text, at: Date.now() });
  if (room.log.length > 80) room.log.shift();
}

function newTurnState(seat, number) {
  return {
    seat,
    number,
    mainActionUsed: false,
    mainActionType: null,
    cardsPlayed: 0,
    cardPlayLimit: 1,
    noFiveStarExtraCards: false,
    extraPunchAllowed: false,
    extraGambleAllowed: false,
    goldenPairRequired: null,
    goldenPairStarted: false,
    firstCardWasQuintessential: false,
    extraCardMaxStars: null,
  };
}

function publicPlayer(p, viewer, room) {
  const self = p.socketId === viewer.socketId;
  const reveal = self || viewer.buffs.bondForger;
  return {
    seat: p.seat,
    name: p.name,
    hp: p.hp,
    armor: p.armor,
    handCount: p.hand.length,
    hand: reveal ? p.hand.map(id => getCard(id)) : [],
    discardCount: p.discard.length,
    discard: p.discard.map(id => getCard(id)).filter(Boolean),
    deckCount: p.deck.length,
    ready: p.ready,
    rematchReady: !!p.rematchReady,
    selectedShows: self ? [...p.selectedShows] : [],
    selectedCardIds: self ? [...p.selectedCardIds] : [],
    selectedShowCount: p.selectedShows.length,
    selectedCardCount: p.selectedCardIds.length,
    buffs: summarizeBuffs(p.buffs),
    isSelf: self,
  };
}

function summarizeBuffs(b) {
  const out = [];
  if (b.untargetableUntilOwnTurn) out.push('Untargetable');
  if (b.nextDamageMultiplier !== 1) out.push(`Next dmg taken ×${b.nextDamageMultiplier}`);
  if (b.nextDamageFlatReduction) out.push(`-${b.nextDamageFlatReduction} next dmg`);
  if (b.nextAttackMultiplier !== 1) out.push(`Next attack ×${b.nextAttackMultiplier}`);
  if (b.nextAttackFlatBonus) out.push(`+${b.nextAttackFlatBonus} next attack`);
  if (b.punchImmunityCharges) out.push(`Punch blocks: ${b.punchImmunityCharges}`);
  if (b.punchesTakeOne) out.push('Punches deal 10');
  if (b.infinityCharges) out.push(`Infinity: ${b.infinityCharges}`);
  if (b.berserkReflect) out.push('Berserk armed');
  if (b.reviveAt80) out.push('Return by Death armed');
  if (b.cannotHealTurns) out.push('Healing blocked');
  if (b.damageCap) out.push(`Damage cap ${b.damageCap}`);
  if (b.cannotDropBelowOne) out.push('Cannot drop below 1');
  if (b.deathNoteTurns != null) out.push(`Death Note: ${b.deathNoteTurns}`);
  if (b.zoltraakTicks) out.push(`Zoltraak: ${b.zoltraakTicks}`);
  if (b.skipTurns) out.push(`Skip turns: ${b.skipTurns}`);
  if (b.forceSelfPunch) out.push('Next action: self-punch');
  if (b.randomNextCard) out.push('Random next card');
  if (b.bonusNextDraw) out.push(`Next draw +${b.bonusNextDraw}`);
  if (b.mustPunchTurns) out.push(`Punch-only turns: ${b.mustPunchTurns}`);
  if (b.delayedDamage?.length) out.push(`Delayed damage: ${b.delayedDamage.length}`);
  return out;
}

function stateFor(room, viewer) {
  const mate = teammate(room, viewer);
  const foes = enemies(room, viewer);
  return {
    code: room.code,
    phase: room.phase,
    winner: room.winner,
    mode: room.mode,
    requiredPlayers: room.requiredPlayers,
    waitingFor: Math.max(0, room.requiredPlayers - room.players.length),
    turn: { ...room.turn, currentName: currentPlayer(room)?.name || '' },
    you: publicPlayer(viewer, viewer, room),
    teammate: mate ? publicPlayer(mate, viewer, room) : null,
    enemies: foes.map(x => publicPlayer(x, viewer, room)),
    players: room.players.map(x => publicPlayer(x, viewer, room)),
    log: room.log,
    shows: SHOWS,
    startingTeam: room.startingTeam,
    environment: room.environment || null,
    lastPlayed: room.lastPlayed || null,
    rematchReadyCount: room.players.filter(x => x.rematchReady).length,
    rematchNeeded: room.requiredPlayers,
    config: { startingHp: STARTING_HP, basePunchDamage: BASE_PUNCH_DAMAGE, startingHandSize: STARTING_HAND_SIZE, showsPerDeck: SHOWS_PER_DECK, deckSize: DECK_SIZE, cardsPerShow: CARDS_PER_SHOW, poolCardsPerShow: POOL_CARDS_PER_SHOW, minEnvironmentsPerShow: MIN_ENVIRONMENTS_PER_SHOW },
    pending: room.pending && room.pending.forSocket === viewer.socketId ? room.pending.public : null,
  };
}

function emitState(room) {
  for (const p of room.players) {
    io.to(p.socketId).emit('state', stateFor(room, p));
  }
}

function requireRoom(socket) {
  const code = socket.data.roomCode;
  if (!code) return null;
  return rooms.get(code) || null;
}

function isCurrent(room, p) { return currentPlayer(room)?.socketId === p.socketId; }
function canAct(room, p) { return room.phase === 'playing' && isCurrent(room, p) && p.hp > 0; }

function heal(room, p, amount, source = '') {
  if (p.buffs.cannotHealTurns > 0) {
    log(room, `${p.name} could not heal${source ? ` from ${source}` : ''}.`);
    return 0;
  }
  const before = p.hp;
  p.hp = Math.min(STARTING_HP, p.hp + Math.max(0, Math.round(amount)));
  const healed = p.hp - before;
  if (healed) log(room, `${p.name} healed ${healed} HP${source ? ` (${source})` : ''}.`);
  return healed;
}

function applyDamage(room, source, target, baseAmount, opts = {}) {
  if (!target || target.hp <= 0) return 0;
  let amount = Math.max(0, Number(baseAmount) || 0);
  const isPunch = !!opts.isPunch;
  const isAttack = opts.isAttack !== false;

  if (source && isAttack) {
    const field = terrainForTeam(room, teamOf(source));
    if (field?.kind === 'attack') amount += field.amount;
    if (isPunch && field?.kind === 'punch') amount += field.amount;
  }
  if (isAttack) {
    const field = terrainForTeam(room, teamOf(target));
    if (field?.kind === 'guard') amount = Math.max(0, amount - field.amount);
  }

  if (isPunch && target.buffs.punchImmunityCharges > 0) {
    target.buffs.punchImmunityCharges -= 1;
    log(room, `${target.name}'s True Warrior blocked the punch.`);
    return 0;
  }
  if (isPunch && target.buffs.punchesTakeOne) amount = 10;
  if (isAttack && target.buffs.infinityCharges > 0) {
    target.buffs.infinityCharges -= 1;
    log(room, `${target.name}'s Infinity blocked the attack.`);
    return 0;
  }

  if (source && isAttack) {
    if (source.buffs.attackBoostTurns > 0) amount *= source.buffs.persistentAttackMultiplier;
    if (!opts.fromFiveStar) {
      amount *= source.buffs.nextAttackMultiplier;
    }
    amount += source.buffs.nextAttackFlatBonus;
    source.buffs.nextAttackMultiplier = 1;
    source.buffs.nextAttackFlatBonus = 0;
  }

  if (target.buffs.nextDamageMultiplier !== 1) {
    amount *= target.buffs.nextDamageMultiplier;
    target.buffs.nextDamageMultiplier = 1;
  }
  if (target.buffs.nextDamageFlatReduction) {
    amount = Math.max(0, amount - target.buffs.nextDamageFlatReduction);
    target.buffs.nextDamageFlatReduction = 0;
  }
  if (target.buffs.damageTakenMultiplierTurns > 0) amount *= target.buffs.persistentDamageTakenMultiplier;
  if (target.buffs.overleveledUntilOwnTurn) amount = Math.max(0, amount - 20);
  if (target.buffs.damageCap != null) amount = Math.min(amount, target.buffs.damageCap);
  amount = Math.round(amount);

  if (source && target.buffs.nextAttackMarkedBonus) {
    amount += target.buffs.nextAttackMarkedBonus;
    target.buffs.nextAttackMarkedBonus = 0;
  }

  let remaining = amount;
  if (target.armor > 0) {
    const absorbed = Math.min(target.armor, remaining);
    target.armor -= absorbed;
    remaining -= absorbed;
  }

  let nextHp = target.hp - remaining;
  if (target.buffs.cannotDropBelowOne && nextHp < 1) nextHp = 1;
  const hpDamage = target.hp - Math.max(0, nextHp);
  target.hp = Math.max(0, nextHp);
  log(room, `${source ? source.name : 'Effect'} dealt ${amount} damage to ${target.name}${target.armor ? ` (${target.armor} armor left)` : ''}.`);

  if (target.buffs.berserkReflect && source && amount > 0) {
    target.buffs.berserkReflect = false;
    const reflect = Math.min(50, amount);
    log(room, `${target.name}'s Berserk reflected ${reflect} damage.`);
    applyDamage(room, target, source, reflect, { isAttack: false });
  }
  if (target.hp <= 0) handleDeath(room, target);
  return hpDamage;
}

function handleDeath(room, p) {
  // Death Note is cancelled if its caster dies before the timer resolves.
  for (const x of room.players) {
    if (x.buffs.deathNoteSourceSeat === p.seat) {
      x.buffs.deathNoteTurns = null;
      x.buffs.deathNoteSourceSeat = null;
      log(room, `${x.name}'s Death Note timer vanished because ${p.name} died.`);
    }
  }

  if (p.buffs.reviveAt80) {
    p.buffs.reviveAt80 = false;
    p.hp = 80;
    log(room, `${p.name} activated Return by Death and revived at 80 HP.`);
    return;
  }

  const mate = teammate(room, p);
  if (mate && mate.hp > 0 && mate.buffs.undertakerArmed) {
    mate.buffs.undertakerArmed = false;
    mate.hp += 50;
    log(room, `${mate.name}'s Undertaker activated when ${p.name} died: +50 HP.`);
  }

  const losingTeam = teamOf(p);
  const teamStillAlive = room.players.some(x => teamOf(x) === losingTeam && x.hp > 0);
  if (!teamStillAlive) {
    room.phase = 'finished';
    room.players.forEach(x => x.rematchReady = false);
    const winningTeam = losingTeam === 0 ? 1 : 0;
    const names = room.players.filter(x => teamOf(x) === winningTeam).map(x => x.name).join(' & ');
    room.winner = `Team ${winningTeam === 0 ? 'A' : 'B'} (${names})`;
    log(room, `${room.winner} wins the match!`);
  }
}

function startOfTurn(room, p) {
  p.buffs.untargetableUntilOwnTurn = false;
  p.buffs.overleveledUntilOwnTurn = false;
  if (p.buffs.damageCapUntilOwnTurn) { p.buffs.damageCap = null; p.buffs.damageCapUntilOwnTurn = false; }
  if (p.buffs.cannotDropBelowOneUntilOwnTurn) {
    p.buffs.cannotDropBelowOne = false; p.buffs.cannotDropBelowOneUntilOwnTurn = false;
    for (const foe of aliveEnemies(room, p)) applyDamage(room, p, foe, 30, { isAttack: false });
  }
  if (p.buffs.cannotHealTurns > 0) p.buffs.cannotHealTurns -= 1;
  if (p.buffs.punchDamageOverrideTurns > 0) p.buffs.punchDamageOverrideTurns -= 1;
  if (Array.isArray(p.buffs.delayedDamage) && p.buffs.delayedDamage.length) {
    for (const delayed of p.buffs.delayedDamage) delayed.turns -= 1;
    const due = p.buffs.delayedDamage.filter(x => x.turns <= 0);
    p.buffs.delayedDamage = p.buffs.delayedDamage.filter(x => x.turns > 0);
    for (const d of due) applyDamage(room, null, p, d.amount, { isAttack: d.attack !== false });
  }
  if (p.buffs.deathNoteTurns != null) {
    p.buffs.deathNoteTurns -= 1;
    if (p.buffs.deathNoteTurns <= 0) { p.buffs.deathNoteSourceSeat = null; p.hp = 0; log(room, `${p.name}'s Death Note timer reached zero.`); handleDeath(room, p); }
  }
  if (p.hp <= 0 && room.phase === 'playing') { setTimeout(() => advanceTurn(room), 250); return false; }
  if (p.buffs.zoltraakTicks > 0) { applyDamage(room, null, p, 10, { isAttack:false }); p.buffs.zoltraakTicks -= 1; }
  for (const delayed of p.buffs.delayedTeamRocket) delayed.turns -= 1;
  const due = p.buffs.delayedTeamRocket.filter(x => x.turns <= 0);
  for (const _ of due) applyDamage(room, null, p, 30, { isAttack:false });
  p.buffs.delayedTeamRocket = p.buffs.delayedTeamRocket.filter(x => x.turns > 0);
  if (p.buffs.skipTurns > 0 && room.phase === 'playing') { p.buffs.skipTurns -= 1; log(room, `${p.name}'s turn was skipped.`); setTimeout(() => advanceTurn(room), 250); return false; }

  const field = terrainForTeam(room, teamOf(p));
  if (field?.kind === 'heal') heal(room, p, field.amount, field.name);
  if (field?.kind === 'armor') { p.armor += field.amount; log(room, `${p.name} gained ${field.amount} armor from ${field.name}.`); }

  const skipOpeningDraw = SETTINGS.openingTeamSkipsFirstDraw && room.turn.number === 1 && teamOf(p) === room.startingTeam;
  if (skipOpeningDraw) log(room, `${p.name} skips the draw on the very first turn because Team ${room.startingTeam === 0 ? 'A' : 'B'} won the coin flip and went first.`);
  else {
    const drawCount = 1 + Math.max(0, Number(p.buffs.bonusNextDraw) || 0);
    const gained = drawCards(p, drawCount);
    p.buffs.bonusNextDraw = 0;
    if (gained.length) log(room, `${p.name} drew ${gained.length} card${gained.length === 1 ? '' : 's'} at the start of the turn.`);
    else log(room, `${p.name}'s deck is empty; no card was drawn.`);
  }
  p.firstTurnTaken = true;
  return true;
}

function advanceTurn(room) {
  if (room.phase !== 'playing') return;
  const seatOrder = room.mode === '1v1' ? [0,1] : [0,1,2,3];
  let idx = seatOrder.indexOf(room.turn.seat);
  let next = null;
  for (let i = 0; i < seatOrder.length; i++) {
    idx = (idx + 1) % seatOrder.length;
    const candidate = playerBySeat(room, seatOrder[idx]);
    if (candidate && candidate.hp > 0) { next = candidate; break; }
  }
  if (!next) return;
  room.turn = newTurnState(next.seat, room.turn.number + 1);
  log(room, `Turn ${room.turn.number}: ${next.name} (Team ${teamOf(next) === 0 ? 'A' : 'B'}).`);
  startOfTurn(room, next);
  emitState(room);
}

function discardCard(player, cardId) {
  const idx = player.hand.indexOf(Number(cardId));
  if (idx === -1) return false;
  const [id] = player.hand.splice(idx, 1);
  player.discard.push(id);
  return true;
}

function restoreFromDiscard(player, count, predicate = () => true) {
  const eligible = player.discard.filter(id => predicate(getCard(id)));
  const chosen = eligible.slice(-count);
  player.discard = player.discard.filter(id => !chosen.includes(id));
  player.hand.push(...chosen);
  return chosen;
}

function manual(room, p, card) {
  log(room, `Manual effect: ${card.name} — ${card.effect}`);
}


function targetSet(room, p, targetSeat, selector) {
  const chosen = playerBySeat(room, targetSeat);
  const mate = teammate(room, p);
  const foes = aliveEnemies(room, p);
  switch (selector) {
    case 'self': return [p];
    case 'ally': {
      if (chosen && chosen.hp > 0 && teamOf(chosen) === teamOf(p)) return [chosen];
      return [mate && mate.hp > 0 ? mate : p].filter(Boolean);
    }
    case 'team': return [p, mate].filter(x => x && x.hp > 0);
    case 'chosen_enemy': {
      if (chosen && chosen.hp > 0 && teamOf(chosen) !== teamOf(p)) return [chosen];
      return foes.slice(0,1);
    }
    case 'enemies': return foes;
    case 'chosen_other': {
      if (chosen && chosen.hp > 0 && chosen.socketId !== p.socketId) return [chosen];
      return foes.slice(0,1);
    }
    case 'all_others': return room.players.filter(x => x.hp > 0 && x.socketId !== p.socketId);
    default: return foes.slice(0,1);
  }
}

function structuredStep(room, p, card, targetSeat, step) {
  const targets = targetSet(room, p, targetSeat, step.target || 'self');
  const first = targets[0];
  const amount = Number(step.amount) || 0;
  if (step.op === 'damage') {
    for (const t of targets) applyDamage(room, step.target === 'self' ? p : p, t, amount, { isAttack: step.attack !== false, fromFiveStar: card.stars === 5 });
  } else if (step.op === 'heal') {
    for (const t of targets) heal(room, t, amount, card.name);
  } else if (step.op === 'armor') {
    for (const t of targets) { t.armor += amount; log(room, `${t.name} gained ${amount} armor (${card.name}).`); }
  } else if (step.op === 'draw') {
    const gained = drawCards(p, Number(step.count) || 1); log(room, `${p.name} drew ${gained.length} card${gained.length === 1 ? '' : 's'} (${card.name}).`);
  } else if (step.op === 'discard_star') {
    const stars = Number(step.stars);
    const count = Math.max(1, Number(step.count) || 1);
    for (const t of targets) {
      for (let i=0;i<count;i++) {
        const idx = t.hand.findIndex(id => getCard(id)?.stars === stars);
        if (idx < 0) break;
        const [id] = t.hand.splice(idx,1); t.discard.push(id);
        log(room, `${t.name} discarded ${getCard(id)?.name || `a ${stars}★ card`} (${card.name}).`);
      }
    }
  } else if (step.op === 'discard_random') {
    for (const t of targets) {
      const count = Math.min(Number(step.count) || 1, t.hand.length);
      for (let i=0;i<count;i++) {
        if (!t.hand.length) break;
        const idx=Math.floor(Math.random()*t.hand.length); const [id]=t.hand.splice(idx,1); t.discard.push(id);
        log(room, `${t.name} discarded ${getCard(id)?.name || 'a card'} at random (${card.name}).`);
      }
    }
  } else if (step.op === 'buff_attack') {
    for (const t of targets) { t.buffs.nextAttackFlatBonus += amount; log(room, `${t.name}'s next attack is ${amount >= 0 ? '+' : ''}${amount} damage (${card.name}).`); }
  } else if (step.op === 'attack_multiplier') {
    const mult = Number(step.mult) || 1;
    for (const t of targets) { t.buffs.nextAttackMultiplier *= mult; log(room, `${t.name}'s next attack is ×${mult} (${card.name}).`); }
  } else if (step.op === 'next_damage_multiplier') {
    const mult = Number(step.mult) || 1;
    for (const t of targets) { t.buffs.nextDamageMultiplier *= mult; log(room, `${t.name}'s next damage taken is ×${mult} (${card.name}).`); }
  } else if (step.op === 'reduce_next') {
    for (const t of targets) { t.buffs.nextDamageFlatReduction += amount; log(room, `${t.name} reduces their next incoming damage by ${amount} (${card.name}).`); }
  } else if (step.op === 'mark') {
    for (const t of targets) { t.buffs.nextAttackMarkedBonus += amount; log(room, `${t.name} is marked for +${amount} on the next damage they take (${card.name}).`); }
  } else if (step.op === 'prevent_heal') {
    for (const t of targets) t.buffs.cannotHealTurns = Math.max(t.buffs.cannotHealTurns, Number(step.turns) || 1);
  } else if (step.op === 'delayed_damage') {
    for (const t of targets) {
      if (!Array.isArray(t.buffs.delayedDamage)) t.buffs.delayedDamage=[];
      t.buffs.delayedDamage.push({ amount, turns:Number(step.turns)||1, attack:step.attack !== false });
      log(room, `${t.name} has ${amount} delayed damage coming in ${Number(step.turns)||1} turn(s) (${card.name}).`);
    }
  } else if (step.op === 'force_self_punch') {
    for (const t of targets) t.buffs.forceSelfPunch = true;
  } else if (step.op === 'untargetable') {
    for (const t of targets) t.buffs.untargetableUntilOwnTurn = true;
  } else if (step.op === 'return_discard') {
    const count=Number(step.count)||1; const stars=step.stars != null ? Number(step.stars) : null; const maxStars=step.maxStars != null ? Number(step.maxStars) : null;
    const restored=restoreFromDiscard(p,count,c => (!stars || c.stars===stars) && (!maxStars || c.stars<=maxStars));
    log(room, `${p.name} returned ${restored.length} card${restored.length===1?'':'s'} from discard (${card.name}).`);
  } else if (step.op === 'punch_immunity') {
    for (const t of targets) t.buffs.punchImmunityCharges += Number(step.charges)||1;
  } else if (step.op === 'extra_punch') {
    room.turn.extraPunchAllowed = true;
  } else if (step.op === 'extra_play') {
    const count=Number(step.count)||1;
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + count);
    if (step.maxStars != null) room.turn.extraCardMaxStars = Number(step.maxStars);
    log(room, `${p.name} gained ${count} extra card play${count===1?'':'s'} this turn${step.maxStars ? ` (max ${step.maxStars}★)` : ''}.`);
  } else if (step.op === 'skip_turn') {
    for (const t of targets) t.buffs.skipTurns += Number(step.count)||1;
  } else if (step.op === 'steal_random') {
    for (const t of targets) {
      const count=Math.min(Number(step.count)||1,t.hand.length);
      for(let i=0;i<count;i++){
        if(!t.hand.length) break; const idx=Math.floor(Math.random()*t.hand.length); const [id]=t.hand.splice(idx,1); p.hand.push(id);
        log(room, `${p.name} stole ${getCard(id)?.name || 'a card'} from ${t.name} (${card.name}).`);
      }
    }
  } else if (step.op === 'damage_cap') {
    for (const t of targets) { t.buffs.damageCap=amount; t.buffs.damageCapUntilOwnTurn=true; }
  } else if (step.op === 'swap_hp') {
    if (first && first.socketId !== p.socketId && first.hp > 0) { const temp=p.hp; p.hp=first.hp; first.hp=temp; log(room, `${p.name} swapped HP with ${first.name} (${card.name}).`); }
  } else if (step.op === 'revive') {
    for (const t of targets) if (t.hp <= 0) { t.hp=Math.max(1,amount); log(room, `${t.name} revived at ${t.hp} HP (${card.name}).`); }
  } else if (step.op === 'bonus_draw') {
    for (const t of targets) t.buffs.bonusNextDraw += Number(step.count)||1;
  }
}

function resolveStructuredAction(room,p,card,targetSeat,action){
  if (!action) return false;
  if (action.type === 'bundle') {
    resolveStructuredAction(room,p,card,targetSeat,action.main);
    for (const step of action.after || []) structuredStep(room,p,card,targetSeat,step);
    return true;
  }
  if (action.type === 'sequence') { for(const step of action.steps||[]) structuredStep(room,p,card,targetSeat,step); return true; }
  if (action.type === 'coin') {
    const heads=Math.random()<0.5; log(room, `${p.name} flipped ${heads?'heads':'tails'} (${card.name}).`);
    for(const step of (heads?action.heads:action.tails)||[]) structuredStep(room,p,card,targetSeat,step);
    return true;
  }
  if (action.type === 'terrain') {
    setTerrain(room,p,card,action);
    return true;
  }
  return false;
}

function resolveCard(room, p, opp, card, targetSeat = null) {
  const n = card.name.toLowerCase();
  const chosenAny = playerBySeat(room, targetSeat);
  // Friendly fire is allowed for manually targeted, single-target damage cards.
  // Cards that explicitly hit opponents/enemy teams still use enemy-only targeting.
  const selectedDamageTarget = FRIENDLY_FIRE_DAMAGE_CARDS.has(n) && chosenAny && chosenAny.hp > 0 && chosenAny.socketId !== p.socketId
    ? chosenAny
    : opp;
  const damage = (amount, target = selectedDamageTarget) => applyDamage(room, p, target, amount, { isAttack: true, fromFiveStar: card.stars === 5 });
  const damageEnemies = amount => aliveEnemies(room, p).forEach(target => damage(amount, target));
  const mate = teammate(room, p);
  const ally = allyTarget(room, p, targetSeat);

  if (card.action) {
    const a = card.action;
    if (resolveStructuredAction(room, p, card, targetSeat, a)) return 'ok';
    const anyOther = chosenAny && chosenAny.socketId !== p.socketId && chosenAny.hp > 0 ? chosenAny : (opp || mate);
    const friendly = chosenAny && chosenAny.hp > 0 && teamOf(chosenAny) === teamOf(p) ? chosenAny : (mate || p);
    if (a.type === 'damage') damage(a.amount, anyOther);
    else if (a.type === 'split_enemies') damageEnemies(a.amount);
    else if (a.type === 'heal') heal(room, a.target === 'self' ? p : friendly, a.amount, card.name);
    else if (a.type === 'armor') { const t = a.target === 'self' ? p : friendly; t.armor += a.amount; log(room, `${t.name} gained ${a.amount} armor.`); }
    else if (a.type === 'damage_draw') { damage(a.amount, anyOther); drawCards(p, a.draw || 1); }
    else if (a.type === 'heal_armor') { heal(room, friendly, a.heal, card.name); friendly.armor += a.armor; log(room, `${friendly.name} gained ${a.armor} armor.`); }
    else if (a.type === 'reduce_next') { p.buffs.nextDamageFlatReduction += a.amount; }
    else if (a.type === 'draw_discard') { drawCards(p, a.draw || 2); const candidates = p.hand.filter(id => id !== card.id); if (candidates.length) discardCard(p, candidates[Math.floor(Math.random()*candidates.length)]); }
    else if (a.type === 'discard_draw') { const candidates = p.hand.filter(id => id !== card.id); if (candidates.length) discardCard(p, candidates[Math.floor(Math.random()*candidates.length)]); drawCards(p, a.draw || 2); }
    else if (a.type === 'discard_star_draw') { const cid = p.hand.find(id => getCard(id)?.stars === a.stars); if (cid) discardCard(p, cid); drawCards(p, a.draw || 2); }
    else if (a.type === 'mark') { if (anyOther) anyOther.buffs.nextAttackMarkedBonus += a.amount; }
    else if (a.type === 'buff_attack') { friendly.buffs.nextAttackFlatBonus += a.amount; }
    else if (a.type === 'armor_draw') { friendly.armor += a.amount; drawCards(p, a.draw || 1); log(room, `${friendly.name} gained ${a.amount} armor.`); }
    return 'ok';
  }

  if (n === 'zoltraak') { aliveEnemies(room, p).forEach(x => x.buffs.zoltraakTicks = Math.max(x.buffs.zoltraakTicks, 3)); }
  else if (n === 'kyubey' || n === 'rage shield') damageEnemies(20);
  else if (n === 'team rocket') aliveEnemies(room, p).forEach(x => x.buffs.delayedTeamRocket.push({ turns: 3 }));
  else if (n === 'i mustn’t run away') { p.buffs.punchDamageOverrideTurns = 2; p.buffs.punchDamageOverride = 50; p.buffs.mustPunchTurns = Math.max(p.buffs.mustPunchTurns, 2); }
  else if (n === 'explosion') damage(30);
  else if (n === 'social anxiety') p.buffs.untargetableUntilOwnTurn = true;
  else if (n === 'apology') { applyDamage(room, p, p, 20, { isAttack:false }); if (mate) heal(room, mate, 40, card.name); drawCards(p,1); }
  else if (n === 'star eye' || n === 'unlimited blade works') { p.buffs.bonusNextDraw += 1; }
  else if (n === 'boredom') {
    const t = opp; const id = t ? drawCard(t) : null;
    if (id && getCard(id)?.stars === 3) { const idx=t.hand.indexOf(id); if(idx>=0)t.hand.splice(idx,1); p.hand.push(id); log(room, `${t.name} drew a 3★ and gave ${getCard(id).name} to ${p.name}.`); }
    else if (id) log(room, `${t.name} drew ${getCard(id).name} and kept it.`);
  }
  else if (n === 'murasame') opp.buffs.nextAttackMarkedBonus = 20;
  else if (n === 'magicless') p.buffs.nextDamageMultiplier = 0.75;
  else if (n === 'wendy') heal(room, ally, 40, card.name);
  else if (n === 'petting a dog' || n === 'petting pochita' || n === 'pizzahut') heal(room, p, 40, card.name);
  else if (n === 'sukunas finger' || n === "sukuna's finger") {
    if (Math.random() < 0.5) { p.buffs.nextAttackMultiplier *= 1.5; log(room, `${p.name} flipped tails: next attack ×1.5.`); }
    else { log(room, `${p.name} flipped heads and takes 40.`); applyDamage(room, p, p, 40, { isAttack: false }); }
  }
  else if (n === 'fire dragon roar') { damage(20); aliveEnemies(room, p).filter(x => !opp || x.seat !== opp.seat).forEach(x => damage(10, x)); }
  else if (n === 'meteor fall') room.players.filter(x => x.socketId !== p.socketId && x.hp > 0).forEach(x => applyDamage(room, p, x, 20, { isAttack: true }));
  else if (n === 'crippling depression') room.players.filter(x => x.hp > 0).forEach(x => applyDamage(room, p, x, 10, { isAttack: false }));
  else if (n === 'overleveled') p.buffs.overleveledUntilOwnTurn = true;
  else if (n === 'digivolve' || n === 'breathing technique') {
    const candidates = p.hand.filter(id => id !== card.id);
    if (candidates.length) {
      const discardId = candidates[Math.floor(Math.random() * candidates.length)];
      discardCard(p, discardId);
      log(room, `${p.name} discarded ${getCard(discardId).name}.`);
    }
    const gained = drawCards(p, 2);
    log(room, `${p.name} drew ${gained.length} cards.`);
  }
  else if (n === 'para-raid') { const t = mate || p; t.buffs.nextAttackFlatBonus += 20; log(room, `${t.name}'s next attacks are empowered by Para-RAID (simplified as +20 to next attack).`); }
  else if (n === 'rassengan' || n === 'rasengan' || n === 'hit the nape') damage(30);
  else if (n === 'titan hardening') { p.armor += 30; log(room, `${p.name} gained 30 armor.`); }
  else if (n === 'heliocentrical heresy') { aliveEnemies(room, p).forEach(x => { damage(10, x); x.buffs.heliocentricPunish = true; }); }
  else if (n === 'pull the chord') { applyDamage(room, p, p, 10, { isAttack: false }); damage(40); }
  else if (n === 'agnes tachyon') {
    const restored = restoreFromDiscard(p, 1, c => c.stars === 3);
    drawCards(p, 1);
    log(room, `${p.name} restored ${restored.length} three-star card and drew 1 card.`);
  }
  else if (n === 'pot of greed') { drawStar(p, 3); drawStar(p, 3); log(room, `${p.name} drew two 3-star cards.`); }
  else if (n === 'true warrior') p.buffs.punchImmunityCharges += 3;
  else if (n === 'kagune') damage(selectedDamageTarget && selectedDamageTarget.hp < STARTING_HP / 2 ? 30 : 20);
  else if (n === 'poison detection') aliveEnemies(room, p).forEach(x => x.buffs.cannotHealTurns = Math.max(x.buffs.cannotHealTurns, 1));
  else if (n === 'requip') { p.armor += 60; log(room, `${p.name} gained 60 armor.`); }
  else if (n === 'boogie woogie') { const target = chosenAny && chosenAny.hp > 0 ? chosenAny : opp; if (target) { const a = p.hp; p.hp = target.hp; target.hp = a; log(room, `${p.name} swapped HP with ${target.name}.`); } }
  else if (n === 'i have no enemies') p.buffs.punchesTakeOne = true;
  else if (n === 'how cute') damageEnemies(40);
  else if (n === 'sandevistan') { opp.buffs.skipTurns += 1; room.turn.extraPunchAllowed = true; }
  else if (n === 'thunder spear') damage(60);
  else if (n === 'arise') { const r = restoreFromDiscard(p, 2, c => c.stars < 5); log(room, `${p.name} restored ${r.length} cards.`); }
  else if (n === 'you’re next' || n === "you're next") { p.buffs.nextAttackFlatBonus += 30; if (mate) mate.buffs.nextAttackFlatBonus += 30; }
  else if (n === 'berserk') p.buffs.berserkReflect = true;
  else if (n === 'the gray monster') { const mult = p.hp < 30 ? 1.5 : 1.25; p.buffs.nextAttackMultiplier *= mult; if (mate) mate.buffs.nextAttackMultiplier *= mult; }
  else if (n === 'undertaker') p.buffs.undertakerArmed = true;
  else if (n === 'hinokami kagura') damageEnemies(40);
  else if (n === 'one punch') damage(60);
  else if (n === 'quintessential quintuplets') {
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, 2);
    room.turn.noFiveStarExtraCards = true;
    room.turn.firstCardWasQuintessential = true;
    log(room, `${p.name} may play two additional non-5-star cards this turn.`);
  }
  else if (n === 'seeing stars') { damage(20); if (selectedDamageTarget) selectedDamageTarget.buffs.randomNextCard = true; }
  else if (n === 'aura, kill yourself') opp.buffs.forceSelfPunch = true;
  else if (n === 'golden ball 1' || n === 'golden ball 2') {
    const counterpart = n.endsWith('1') ? 'Golden ball 2' : 'Golden ball 1';
    if (!room.turn.goldenPairStarted) {
      room.turn.goldenPairStarted = true;
      room.turn.goldenPairRequired = counterpart;
      room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
      log(room, `${p.name} must play ${counterpart} this turn to activate the pair.`);
    } else {
      heal(room, ally, 70, 'Golden Ball pair');
      p.buffs.nextAttackMultiplier *= 1.5;
      p.buffs.attackBoostTurns = Math.max(p.buffs.attackBoostTurns, 2);
      room.turn.goldenPairRequired = null;
      log(room, `${p.name} completed the Golden Ball pair.`);
    }
  }
  else if (n === 'geass') {
    const stealable = opp.hand;
    if (stealable.length) {
      const id = stealable[Math.floor(Math.random() * stealable.length)];
      opp.hand.splice(opp.hand.indexOf(id), 1); p.hand.push(id);
      log(room, `${p.name} stole ${getCard(id).name} with Geass.`);
    }
  }
  else if (n === 'death note') { opp.buffs.deathNoteTurns = 5; opp.buffs.deathNoteSourceSeat = p.seat; log(room, `${opp.name} will die in 5 of their turns unless ${p.name} dies first.`); }
  else if (n === 'return by death') { p.buffs.reviveAt80 = true; if (mate) mate.buffs.reviveAt80 = true; }
  else if (n === 'excalibur') damage(100);
  else if (n === 'time leap machine') {
    const snap = room.history.length >= 2 ? room.history[room.history.length - 2] : room.history[0];
    if (snap) {
      restoreSnapshot(room, snap);
      log(room, `${p.name} rewound the game two turn-start snapshots.`);
      return 'rewound';
    }
  }
  else if (n === 'flourite eye’s song' || n === "flourite eye's song") {
    drawCards(p, 1);
    p.buffs.nextAttackMultiplier *= 1.5;
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
    room.turn.extraCardMaxStars = 4;
    log(room, `${p.name} drew 1 card, gained ×1.5 on their next attack, and may play one additional non-5★ card this turn.`);
  }
  else if (n === 'infinity') p.buffs.infinityCharges += 2;
  else if (n === 'the place above the grey fog') {
    const gained = drawCards(p, 3);
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
    room.turn.extraCardMaxStars = 4;
    log(room, `${p.name} drew ${gained.length} cards and may play one additional non-5★ card.`);
  }
  else if (n === 'the overlord of centuries end') { p.buffs.cannotDropBelowOne = true; p.buffs.cannotDropBelowOneUntilOwnTurn = true; }
  else if (n === 'the father') {
    const restored = restoreFromDiscard(p, 2, c => c.stars < 5);
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
    room.turn.extraCardMaxStars = 4;
    log(room, `${p.name} restored ${restored.length} cards and may play one additional non-5★ card.`);
  }
  else if (n === 'piss dragon') { damageEnemies(30); [p, mate].filter(Boolean).forEach(x => { x.buffs.damageCap = 50; x.buffs.damageCapUntilOwnTurn = true; }); }
  else if (n === 'the world') { aliveEnemies(room, p).forEach(x => x.buffs.skipTurns += 1); applyDamage(room, p, p, 40, { isAttack:false }); }
  else if (n === 'bond forger') { p.buffs.bondForger = true; drawCards(p,2); log(room, `${p.name} can inspect opponents' card abilities for the rest of the game and drew 2 cards.`); }
  else if (n === 'world item') { p.buffs.worldItemUntilOwnTurn = true; p.armor += 20; log(room, `${p.name} is protected from non-5★ status/multiplier effects until their next turn and gained 20 armor.`); }
  else if (n === 'have you ever played golf with your life on the line?') { applyDamage(room, p, p, 20, { isAttack: false }); p.buffs.nextAttackFlatBonus += 30; }
  else if (n === 'perfect warrior') { const t = mate || p; t.buffs.persistentAttackMultiplier = 1.25; t.buffs.persistentDamageTakenMultiplier = 0.75; t.buffs.attackBoostTurns = Math.max(t.buffs.attackBoostTurns, 2); t.buffs.damageTakenMultiplierTurns = Math.max(t.buffs.damageTakenMultiplierTurns, 2); log(room, `${t.name} gains 1.25× attack and takes 0.75× damage for their next 2 turns.`); }
  else manual(room, p, card);
  return 'ok';
}

function snapshotRoom(room) {
  return {
    turn: JSON.parse(JSON.stringify(room.turn)),
    environment: JSON.parse(JSON.stringify(room.environment || null)),
    players: room.players.map(p => ({
      hp: p.hp, armor: p.armor, hand: [...p.hand], discard: [...p.discard], deck: [...p.deck], firstTurnTaken: p.firstTurnTaken, buffs: JSON.parse(JSON.stringify(p.buffs))
    }))
  };
}
function restoreSnapshot(room, snap) {
  room.turn = JSON.parse(JSON.stringify(snap.turn));
  room.environment = JSON.parse(JSON.stringify(snap.environment || null));
  room.players.forEach((p, i) => {
    Object.assign(p, JSON.parse(JSON.stringify(snap.players[i])));
  });
}
function saveTurnSnapshot(room) {
  room.history.push(snapshotRoom(room));
  if (room.history.length > 8) room.history.shift();
}

function hasPunchTarget(room, p) {
  return room.players.some(x => x.socketId !== p.socketId && x.hp > 0 && !x.buffs.untargetableUntilOwnTurn);
}

function hasLegalCardPlay(room, p) {
  return p.hand.some(id => {
    const card = getCard(id);
    return card && !canPlayCard(room, p, card);
  });
}

function hasRemainingActions(room, p) {
  if (!canAct(room, p)) return false;
  if (!room.turn.mainActionUsed) return hasPunchTarget(room, p) || hasLegalCardPlay(room, p) || p.buffs.forceSelfPunch;
  if (room.turn.extraPunchAllowed && hasPunchTarget(room, p)) return true;
  if (room.turn.cardsPlayed < room.turn.cardPlayLimit && hasLegalCardPlay(room, p)) return true;
  return false;
}

function finishTurn(room, p, auto = false) {
  if (!canAct(room, p)) return false;
  if (room.turn.goldenPairRequired) {
    log(room, `${p.name} ended the turn without completing the Golden Ball pair; no pair bonus was gained.`);
  }
  if (p.buffs.mustPunchTurns > 0) p.buffs.mustPunchTurns -= 1;
  if (p.buffs.attackBoostTurns > 0) {
    p.buffs.attackBoostTurns -= 1;
    if (p.buffs.attackBoostTurns <= 0) p.buffs.persistentAttackMultiplier = 1;
  }
  if (p.buffs.damageTakenMultiplierTurns > 0) {
    p.buffs.damageTakenMultiplierTurns -= 1;
    if (p.buffs.damageTakenMultiplierTurns <= 0) p.buffs.persistentDamageTakenMultiplier = 1;
  }
  tickTerrainAfterTurn(room, p);
  if (auto) log(room, `${p.name} has no actions left, so the turn ended automatically.`);
  saveTurnSnapshot(room);
  advanceTurn(room);
  return true;
}

function scheduleAutoEnd(room, p) {
  if (room.phase !== 'playing' || !isCurrent(room, p) || hasRemainingActions(room, p)) return;
  const seat = room.turn.seat;
  const number = room.turn.number;
  setTimeout(() => {
    if (room.phase !== 'playing' || room.turn.seat !== seat || room.turn.number !== number) return;
    const current = currentPlayer(room);
    if (!current || current.socketId !== p.socketId || hasRemainingActions(room, p)) return;
    finishTurn(room, p, true);
  }, 650);
}

function beginMatch(room, isRematch = false) {
  room.players.forEach(preparePlayerDeck);
  room.environment = null;
  room.lastPlayed = null;
  room.winner = null;
  room.pending = null;
  room.history = [];
  if (isRematch) room.log = [];
  room.startingTeam = Math.random() < 0.5 ? 0 : 1;
  const firstSeat = room.startingTeam === 0 ? 0 : 1;
  room.phase = 'playing';
  room.turn = newTurnState(firstSeat, 1);
  saveTurnSnapshot(room);
  log(room, `${isRematch ? 'Rematch coin flip' : 'Coin flip'}: Team ${room.startingTeam===0?'A':'B'} goes first in ${room.mode}. The player taking the very first turn does not draw. ${currentPlayer(room).name} starts.`);
  startOfTurn(room, currentPlayer(room));
}

function canPlayCard(room, p, card) {
  if (!canAct(room, p)) return 'It is not your turn.';
  if (!p.hand.includes(card.id)) return 'That card is not in your hand.';
  if (p.buffs.forceSelfPunch) return 'Aura forces your next action to be a punch against yourself.';
  if (p.buffs.mustPunchTurns > 0) return 'This effect forces you to use punches on this turn; you cannot play a card.';
  if (p.buffs.blockCardId === card.id) return 'That card is blocked this turn.';
  if (room.turn.goldenPairRequired && card.name !== room.turn.goldenPairRequired) return `You must play ${room.turn.goldenPairRequired} next.`;
  if (room.turn.noFiveStarExtraCards && room.turn.cardsPlayed >= 0 && card.stars === 5 && room.turn.firstCardWasQuintessential) return 'Quintessential Quintuplets does not allow 5-star follow-up cards.';
  if (room.turn.mainActionUsed && room.turn.extraCardMaxStars != null && card.stars > room.turn.extraCardMaxStars) return `Your extra card play is limited to ${room.turn.extraCardMaxStars}★ or lower.`;
  if (!room.turn.mainActionUsed) return null;
  if (room.turn.mainActionType === 'punch' && room.turn.cardPlayLimit <= 1) return 'You already used your main action to punch this turn.';
  if (room.turn.cardsPlayed < room.turn.cardPlayLimit) return null;
  return 'You have already used your card/action allowance this turn.';
}

function actionHarmfullyTargetsChosen(action) {
  if (!action) return false;
  if (action.type === 'bundle') return actionHarmfullyTargetsChosen(action.main) || (action.after || []).some(harmfulStepTargetsChosen);
  if (action.type === 'sequence') return (action.steps || []).some(harmfulStepTargetsChosen);
  if (action.type === 'coin') return [...(action.heads || []), ...(action.tails || [])].some(harmfulStepTargetsChosen);
  return false;
}

function harmfulStepTargetsChosen(step) {
  if (!step || !['chosen_enemy','chosen_other'].includes(step.target)) return false;
  const harmful = new Set(['damage','discard_random','mark','prevent_heal','delayed_damage','force_self_punch','skip_turn','steal_random','swap_hp']);
  if (harmful.has(step.op)) return true;
  return step.op === 'buff_attack' && Number(step.amount) < 0;
}

function playCard(room, p, card, targetSeat = null) {
  const opp = otherPlayer(room, p, targetSeat);
  const error = canPlayCard(room, p, card);
  if (error) return error;

  const chosen = playerBySeat(room, targetSeat);
  const actionTargetsAnyOther = card.action && (['damage','damage_draw','mark'].includes(card.action.type) || actionHarmfullyTargetsChosen(card.action));
  const targetedPlayer = (actionTargetsAnyOther || FRIENDLY_FIRE_DAMAGE_CARDS.has(card.name.toLowerCase())) && chosen && chosen.hp > 0 && chosen.socketId !== p.socketId
    ? chosen
    : opp;
  if (targetedPlayer?.buffs.untargetableUntilOwnTurn && (actionHarmfullyTargetsChosen(card.action) || /damage|opponent|enemy|target/i.test(card.effect))) {
    return `${targetedPlayer.name} is untargetable right now.`;
  }

  // Random-next-card effect replaces the chosen card.
  if (p.buffs.randomNextCard) {
    p.buffs.randomNextCard = false;
    const playable = p.hand.map(getCard).filter(Boolean);
    if (playable.length) card = playable[Math.floor(Math.random() * playable.length)];
    log(room, `Seeing Stars randomized ${p.name}'s card into ${card.name}.`);
  }

  const wasQuintessential = card.name.toLowerCase() === 'quintessential quintuplets';
  discardCard(p, card.id);
  const firstAction = !room.turn.mainActionUsed;
  room.turn.mainActionUsed = true;
  if (firstAction) room.turn.mainActionType = 'card';
  if (!wasQuintessential) room.turn.cardsPlayed += 1;
  const resolutionStart = room.log.length;
  log(room, `${p.name} played ${card.name} (${card.stars}★).`);

  if (opp?.buffs.heliocentricPunish) {
    opp.buffs.heliocentricPunish = false;
    applyDamage(room, opp, p, 10, { isAttack: false });
  }

  const result = resolveCard(room, p, opp, card, targetSeat);
  const chosenTarget = playerBySeat(room, targetSeat);
  room.lastPlayed = {
    card: { id: card.id, name: card.name, stars: card.stars, effect: card.effect, show: card.show || card.origin || '', cardType: card.cardType || 'card' },
    playerName: p.name,
    playerSeat: p.seat,
    targetName: chosenTarget?.name || null,
    targetSeat: chosenTarget?.seat ?? null,
    resolution: room.log.slice(resolutionStart + 1).map(x => x.text).slice(-8),
    at: Date.now(),
  };
  if (p.hp <= 0 && room.phase === 'playing') {
    saveTurnSnapshot(room);
    advanceTurn(room);
    return null;
  }
  emitState(room);
  scheduleAutoEnd(room, p);
  return null;
}

io.on('connection', socket => {
  socket.on('createRoom', ({ name, mode } = {}) => {
    const code = roomCode();
    mode = mode === '1v1' ? '1v1' : '2v2';
    const requiredPlayers = mode === '1v1' ? 2 : 4;
    const room = { code, mode, requiredPlayers, phase:'waiting', players:[makePlayer(socket,name,0)], turn:newTurnState(0,1), log:[], winner:null, history:[], pending:null, startingTeam:null, environment:null, lastPlayed:null };
    rooms.set(code, room); socket.data.roomCode = code; socket.join(code);
    log(room, `${room.players[0].name} created a ${mode} room ${code}. Choose exactly ${SHOWS_PER_DECK} shows, build your 48-card deck, and ready up.`); emitState(room);
  });

  socket.on('joinRoom', ({ code, name } = {}) => {
    code = String(code || '').trim().toUpperCase(); const room = rooms.get(code);
    if (!room) return socket.emit('errorMessage','Room not found.');
    if (room.players.length >= room.requiredPlayers) return socket.emit('errorMessage','Room is full.');
    const allowedSeats = room.mode === '1v1' ? [0,1] : [0,1,2,3];
    const seat=allowedSeats.find(s=>!room.players.some(x=>x.seat===s)); const p=makePlayer(socket,name,seat);
    room.players.push(p); socket.data.roomCode=code; socket.join(code);
    log(room, `${p.name} joined as Team ${teamOf(p)===0?'A':'B'} Player ${Math.floor(seat/2)+1}.`); emitState(room);
  });

  socket.on('setDeck', ({ shows, cardIds } = {}) => {
    const room=requireRoom(socket); if (!room || room.phase!=='waiting') return;
    const p=playerBySocket(room,socket.id); if (!p) return;
    const deck=buildDeckForSelection(shows, cardIds);
    if (!deck) return socket.emit('errorMessage',`Choose exactly ${SHOWS_PER_DECK} valid shows and exactly 10×3★, 5×4★, and 1×5★ from each show (48 cards total), with at least ${MIN_ENVIRONMENTS_PER_SHOW} Environment cards from each show.`);
    p.selectedShows=[...new Set(shows)]; p.selectedCardIds=[...deck]; p.ready=true;
    log(room, `${p.name} locked a custom 48-card deck (${p.selectedShows.join(' / ')}).`);
    if (room.players.length===room.requiredPlayers && room.players.every(x=>x.ready)) beginMatch(room, false);
    emitState(room);
  });

  socket.on('playCard', ({ cardId, targetSeat } = {}) => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id); if (!p) return;
    const card = getCard(cardId); if (!card) return;
    const error = playCard(room, p, card, targetSeat);
    if (error) socket.emit('errorMessage', error);
  });

  socket.on('punch', ({ targetSeat } = {}) => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id);
    const chosen = playerBySeat(room, targetSeat);
    const target = chosen && chosen.socketId !== p.socketId && chosen.hp > 0 ? chosen : null;
    if (!canAct(room, p)) return socket.emit('errorMessage', 'It is not your turn.');
    if (p.buffs.forceSelfPunch) {
      p.buffs.forceSelfPunch = false;
      room.turn.mainActionUsed = true;
      room.turn.mainActionType = 'punch';
      applyDamage(room, p, p, BASE_PUNCH_DAMAGE, { isPunch: true, isAttack: true });
      log(room, `${p.name} was forced to punch themself.`);
      if (p.hp <= 0 && room.phase === 'playing') { saveTurnSnapshot(room); advanceTurn(room); return; }
      emitState(room); scheduleAutoEnd(room, p); return;
    }
    if (room.turn.mainActionUsed && !room.turn.extraPunchAllowed) return socket.emit('errorMessage', 'You already used your main action this turn.');
    if (!target) return socket.emit('errorMessage', 'Choose a living teammate or enemy to punch.');
    if (target.buffs.untargetableUntilOwnTurn) return socket.emit('errorMessage', `${target.name} is untargetable right now.`);
    const firstAction = !room.turn.mainActionUsed;
    room.turn.mainActionUsed = true;
    if (firstAction) room.turn.mainActionType = 'punch';
    room.turn.extraPunchAllowed = false;
    const base = p.buffs.punchDamageOverrideTurns > 0 ? p.buffs.punchDamageOverride : BASE_PUNCH_DAMAGE;
    applyDamage(room, p, target, base, { isPunch: true, isAttack: true });
    if (p.hp <= 0 && room.phase === 'playing') { saveTurnSnapshot(room); advanceTurn(room); return; }
    emitState(room);
    scheduleAutoEnd(room, p);
  });


  socket.on('endTurn', () => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id);
    if (!canAct(room, p)) return socket.emit('errorMessage', 'It is not your turn.');
    finishTurn(room, p, false);
  });

  socket.on('requestRematch', () => {
    const room = requireRoom(socket); if (!room || room.phase !== 'finished') return;
    const p = playerBySocket(room, socket.id); if (!p) return;
    p.rematchReady = true;
    log(room, `${p.name} is ready for a rematch.`);
    if (room.players.length === room.requiredPlayers && room.players.every(x => x.rematchReady)) {
      beginMatch(room, true);
    }
    emitState(room);
  });

  socket.on('disconnect', () => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id);
    if (p) log(room, `${p.name} disconnected.`);
    if (room.phase === 'waiting') {
      room.players = room.players.filter(x => x.socketId !== socket.id);
      if (!room.players.length) rooms.delete(room.code); else emitState(room);
      return;
    }
    if (p && room.phase === 'playing') {
      room.phase = 'finished';
      room.players.forEach(x => x.rematchReady = false);
      const winningTeam = teamOf(p) === 0 ? 1 : 0;
      const names = room.players.filter(x => teamOf(x) === winningTeam).map(x => x.name).join(' & ');
      room.winner = `Team ${winningTeam === 0 ? 'A' : 'B'} (${names})`;
      log(room, `${room.winner} wins because ${p.name} disconnected.`);
      emitState(room);
      setTimeout(() => rooms.delete(room.code), 60_000);
    }
  });

});

server.listen(PORT, () => console.log(`Fanmade TCG running on http://localhost:${PORT}`));
