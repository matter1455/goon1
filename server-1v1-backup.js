const path = require('path');
const http = require('http');
const express = require('express');
const { Server } = require('socket.io');
const CARDS = require('./data/cards.json');
const SETTINGS = require('./game-settings.json');

// Most balance values live in game-settings.json so you can edit them without
// touching the multiplayer/game-engine code below.
const PORT = process.env.PORT || 3000;
const STARTING_HP = SETTINGS.startingHp;
const BASE_PUNCH_DAMAGE = SETTINGS.basePunchDamage;
const STARTING_THREE_STARS = SETTINGS.startingCards.threeStar;
const STARTING_FOUR_STARS = SETTINGS.startingCards.fourStar;
const STARTING_FIVE_STARS = SETTINGS.startingCards.fiveStar;
const STANDARD_GAMBLE = SETTINGS.gambleOdds.standard;
const BETTER_GAMBLE = SETTINGS.gambleOdds.better;

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });
app.use(express.static(path.join(__dirname, 'public')));
app.get('/api/cards', (_req, res) => res.json(CARDS));
app.get('/api/config', (_req, res) => res.json({ startingHp: STARTING_HP, basePunchDamage: BASE_PUNCH_DAMAGE, standardGamble: STANDARD_GAMBLE, betterGamble: BETTER_GAMBLE }));

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

function makeDecks() {
  return {
    3: shuffle(CARDS.filter(c => c.stars === 3).map(c => c.id)),
    4: shuffle(CARDS.filter(c => c.stars === 4).map(c => c.id)),
    5: shuffle(CARDS.filter(c => c.stars === 5).map(c => c.id)),
  };
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
    reviveAt50: false,
    cannotHealTurns: 0,
    damageCap: null,
    damageCapUntilOwnTurn: false,
    cannotDropBelowOne: false,
    cannotDropBelowOneUntilOwnTurn: false,
    deathNoteTurns: null,
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
  };
}

function makePlayer(socket, name, seat) {
  const p = {
    socketId: socket.id,
    name: String(name || `Player ${seat + 1}`).slice(0, 24),
    seat,
    hp: STARTING_HP,
    armor: 0,
    hand: [],
    discard: [],
    decks: makeDecks(),
    buffs: blankBuffs(),
  };
  for (let i = 0; i < STARTING_THREE_STARS; i++) drawStar(p, 3);
  for (let i = 0; i < STARTING_FOUR_STARS; i++) drawStar(p, 4);
  for (let i = 0; i < STARTING_FIVE_STARS; i++) drawStar(p, 5);
  return p;
}

function getCard(id) { return CARDS.find(c => c.id === Number(id)); }
function otherPlayer(room, p) { return room.players.find(x => x.socketId !== p.socketId); }
function currentPlayer(room) { return room.players[room.turn.seat]; }
function playerBySocket(room, socketId) { return room.players.find(p => p.socketId === socketId); }

function drawStar(player, stars) {
  const deck = player.decks[stars];
  if (!deck.length) {
    const eligible = player.discard.filter(id => getCard(id)?.stars === Number(stars));
    if (eligible.length) {
      player.decks[stars] = shuffle(eligible);
      player.discard = player.discard.filter(id => getCard(id)?.stars !== Number(stars));
    } else return null;
  }
  const id = player.decks[stars].pop();
  if (id) player.hand.push(id);
  return id || null;
}

function weightedStar(odds) {
  const r = Math.random();
  let acc = 0;
  for (const s of [3, 4, 5]) {
    acc += odds[s];
    if (r <= acc) return s;
  }
  return 3;
}

function gambleDraw(player, odds = STANDARD_GAMBLE, count = 1) {
  const gained = [];
  for (let i = 0; i < count; i++) {
    const stars = weightedStar(odds);
    const id = drawStar(player, stars);
    if (id) gained.push(id);
  }
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
    cardsPlayed: 0,
    cardPlayLimit: 1,
    noFiveStarExtraCards: false,
    extraPunchAllowed: false,
    extraGambleAllowed: false,
    goldenPairRequired: null,
    goldenPairStarted: false,
    firstCardWasQuintessential: false,
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
  if (b.punchesTakeOne) out.push('Punches deal 1');
  if (b.infinityCharges) out.push(`Infinity: ${b.infinityCharges}`);
  if (b.berserkReflect) out.push('Berserk armed');
  if (b.reviveAt50) out.push('Return by Death armed');
  if (b.cannotHealTurns) out.push('Healing blocked');
  if (b.damageCap) out.push(`Damage cap ${b.damageCap}`);
  if (b.cannotDropBelowOne) out.push('Cannot drop below 1');
  if (b.deathNoteTurns != null) out.push(`Death Note: ${b.deathNoteTurns}`);
  if (b.zoltraakTicks) out.push(`Zoltraak: ${b.zoltraakTicks}`);
  if (b.skipTurns) out.push(`Skip turns: ${b.skipTurns}`);
  if (b.forceSelfPunch) out.push('Next action: self-punch');
  if (b.randomNextCard) out.push('Random next card');
  return out;
}

function stateFor(room, viewer) {
  const opponent = otherPlayer(room, viewer);
  return {
    code: room.code,
    phase: room.phase,
    winner: room.winner,
    turn: { ...room.turn, currentName: room.players[room.turn.seat]?.name || '' },
    you: publicPlayer(viewer, viewer, room),
    opponent: opponent ? publicPlayer(opponent, viewer, room) : null,
    log: room.log,
    config: { startingHp: STARTING_HP, basePunchDamage: BASE_PUNCH_DAMAGE, standardGamble: STANDARD_GAMBLE, betterGamble: BETTER_GAMBLE },
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

  if (isPunch && target.buffs.punchImmunityCharges > 0) {
    target.buffs.punchImmunityCharges -= 1;
    log(room, `${target.name}'s True Warrior blocked the punch.`);
    return 0;
  }
  if (isPunch && target.buffs.punchesTakeOne) amount = 1;
  if (isAttack && target.buffs.infinityCharges > 0) {
    target.buffs.infinityCharges -= 1;
    log(room, `${target.name}'s Infinity blocked the attack.`);
    return 0;
  }

  if (source && isAttack) {
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
  amount *= target.buffs.persistentDamageTakenMultiplier;
  if (target.buffs.overleveledUntilOwnTurn) amount = Math.max(0, amount - 15);
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
  if (p.buffs.reviveAt50) {
    p.buffs.reviveAt50 = false;
    p.hp = 50;
    log(room, `${p.name} activated Return by Death and revived at 50 HP.`);
    return;
  }
  const alive = room.players.filter(x => x.hp > 0);
  if (alive.length === 1) {
    room.phase = 'finished';
    room.winner = alive[0].name;
    log(room, `${alive[0].name} wins the duel!`);
  }
}

function startOfTurn(room, p) {
  // Expire "until your next turn" protections.
  p.buffs.untargetableUntilOwnTurn = false;
  p.buffs.overleveledUntilOwnTurn = false;
  if (p.buffs.damageCapUntilOwnTurn) { p.buffs.damageCap = null; p.buffs.damageCapUntilOwnTurn = false; }
  if (p.buffs.cannotDropBelowOneUntilOwnTurn) {
    p.buffs.cannotDropBelowOne = false;
    p.buffs.cannotDropBelowOneUntilOwnTurn = false;
    const opp = otherPlayer(room, p);
    if (opp) applyDamage(room, p, opp, 30, { isAttack: false });
  }
  if (p.buffs.cannotHealTurns > 0) p.buffs.cannotHealTurns -= 1;
  if (p.buffs.punchDamageOverrideTurns > 0) p.buffs.punchDamageOverrideTurns -= 1;
  if (p.buffs.deathNoteTurns != null) {
    p.buffs.deathNoteTurns -= 1;
    if (p.buffs.deathNoteTurns <= 0) {
      p.hp = 0;
      log(room, `${p.name}'s Death Note timer reached zero.`);
      handleDeath(room, p);
    }
  }
  if (p.buffs.zoltraakTicks > 0) {
    const opp = otherPlayer(room, p);
    // Zoltraak is applied to the affected player and ticks at their turn start.
    applyDamage(room, opp, p, 7, { isAttack: false });
    p.buffs.zoltraakTicks -= 1;
  }
  for (const delayed of p.buffs.delayedTeamRocket) delayed.turns -= 1;
  const due = p.buffs.delayedTeamRocket.filter(x => x.turns <= 0);
  if (due.length) {
    const opp = otherPlayer(room, p);
    for (const _ of due) applyDamage(room, opp, p, 25, { isAttack: false });
    p.buffs.delayedTeamRocket = p.buffs.delayedTeamRocket.filter(x => x.turns > 0);
  }

  if (p.buffs.skipTurns > 0 && room.phase === 'playing') {
    p.buffs.skipTurns -= 1;
    log(room, `${p.name}'s turn was skipped.`);
    setTimeout(() => advanceTurn(room), 250);
    return false;
  }
  return true;
}

function advanceTurn(room) {
  if (room.phase !== 'playing') return;
  const nextSeat = (room.turn.seat + 1) % room.players.length;
  room.turn = newTurnState(nextSeat, room.turn.number + 1);
  const p = currentPlayer(room);
  log(room, `Turn ${room.turn.number}: ${p.name}.`);
  startOfTurn(room, p);
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

function resolveCard(room, p, opp, card) {
  const n = card.name.toLowerCase();
  const damage = (amount, target = opp) => applyDamage(room, p, target, amount, { isAttack: true, fromFiveStar: card.stars === 5 });

  if (n === 'zoltraak') { opp.buffs.zoltraakTicks = Math.max(opp.buffs.zoltraakTicks, 3); }
  else if (n === 'kyubey' || n === 'rage shield') damage(15);
  else if (n === 'team rocket') opp.buffs.delayedTeamRocket.push({ turns: 3 });
  else if (n === 'i mustn’t run away') { p.buffs.punchDamageOverrideTurns = 2; p.buffs.punchDamageOverride = 30; }
  else if (n === 'explosion') damage(25);
  else if (n === 'social anxiety') p.buffs.untargetableUntilOwnTurn = true;
  else if (n === 'murasame') opp.buffs.nextAttackMarkedBonus = 20;
  else if (n === 'magicless') p.buffs.nextDamageMultiplier = 0.75;
  else if (n === 'petting a dog' || n === 'pizzahut') heal(room, p, 25, card.name);
  else if (n === 'sukunas finger') {
    if (Math.random() < 0.5) { p.buffs.nextAttackMultiplier *= 1.5; log(room, `${p.name} flipped tails: next attack ×1.5.`); }
    else { log(room, `${p.name} flipped heads and takes 40.`); applyDamage(room, p, p, 40, { isAttack: false }); }
  }
  else if (n === 'meteor fall') damage(20);
  else if (n === 'crippling depression') { applyDamage(room, p, p, 10, { isAttack: false }); damage(10); }
  else if (n === 'overleveled') p.buffs.overleveledUntilOwnTurn = true;
  else if (n === 'digivolve' || n === 'breathing technique') {
    const candidates = p.hand.filter(id => id !== card.id);
    if (candidates.length) {
      const discardId = candidates[Math.floor(Math.random() * candidates.length)];
      discardCard(p, discardId);
      log(room, `${p.name} discarded ${getCard(discardId).name}.`);
    }
    const gained = gambleDraw(p, STANDARD_GAMBLE, 2);
    log(room, `${p.name} gambled for ${gained.length} cards.`);
  }
  else if (n === 'rassengan' || n === 'hit the nape') damage(25);
  else if (n === 'titan hardening') { p.armor += 20; log(room, `${p.name} gained 20 armor.`); }
  else if (n === 'heliocentrical heresy') { damage(10); opp.buffs.heliocentricPunish = true; }
  else if (n === 'pull the chord') { applyDamage(room, p, p, 10, { isAttack: false }); damage(35); }
  else if (n === 'agnes tachyon') {
    const restored = restoreFromDiscard(p, 1, c => c.stars === 3);
    gambleDraw(p, STANDARD_GAMBLE, 1);
    log(room, `${p.name} restored ${restored.length} three-star card and gambled.`);
  }
  else if (n === 'pot of greed') { drawStar(p, 3); drawStar(p, 3); log(room, `${p.name} drew two 3-star cards.`); }
  else if (n === 'true warrior') p.buffs.punchImmunityCharges += 3;
  else if (n === 'kagune') damage(opp.hp < STARTING_HP / 2 ? 30 : 20);
  else if (n === 'poison detection') opp.buffs.cannotHealTurns = Math.max(opp.buffs.cannotHealTurns, 1);
  else if (n === 'requip') { p.armor += 40; log(room, `${p.name} gained 40 armor.`); }
  else if (n === 'boogie woogie') { const a = p.hp; p.hp = opp.hp; opp.hp = a; log(room, `${p.name} swapped HP with ${opp.name}.`); }
  else if (n === 'i have no enemies') p.buffs.punchesTakeOne = true;
  else if (n === 'how cute') damage(30);
  else if (n === 'sandevistan') { opp.buffs.skipTurns += 1; room.turn.extraPunchAllowed = true; }
  else if (n === 'thunder spear') damage(45);
  else if (n === 'arise') { const r = restoreFromDiscard(p, 3, c => c.stars < 5); log(room, `${p.name} restored ${r.length} cards.`); }
  else if (n === 'you’re next' || n === "you're next") p.buffs.nextAttackMultiplier *= 1.5;
  else if (n === 'berserk') p.buffs.berserkReflect = true;
  else if (n === 'the gray monster') p.buffs.nextAttackMultiplier *= (p.hp < 30 ? 2 : 1.5);
  else if (n === 'hinokami kagura') damage(25);
  else if (n === 'one punch') damage(50);
  else if (n === 'quintessential quintuplets') {
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, 2);
    room.turn.noFiveStarExtraCards = true;
    room.turn.firstCardWasQuintessential = true;
    log(room, `${p.name} may play two additional non-5-star cards this turn.`);
  }
  else if (n === 'seeing stars') { damage(15); opp.buffs.randomNextCard = true; }
  else if (n === 'aura, kill yourself') opp.buffs.forceSelfPunch = true;
  else if (n === 'golden ball 1' || n === 'golden ball 2') {
    const counterpart = n.endsWith('1') ? 'Golden ball 2' : 'Golden ball 1';
    if (!room.turn.goldenPairStarted) {
      room.turn.goldenPairStarted = true;
      room.turn.goldenPairRequired = counterpart;
      room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
      log(room, `${p.name} must play ${counterpart} this turn to activate the pair.`);
    } else {
      heal(room, p, 30, 'Golden Ball pair');
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
  else if (n === 'death note') { opp.buffs.deathNoteTurns = 5; log(room, `${opp.name} will die in 5 of their turns unless the effect is removed.`); }
  else if (n === 'return by death') p.buffs.reviveAt50 = true;
  else if (n === 'excalibur') damage(75);
  else if (n === 'time leap machine') {
    const snap = room.history.length >= 2 ? room.history[room.history.length - 2] : room.history[0];
    if (snap) {
      restoreSnapshot(room, snap);
      log(room, `${p.name} rewound the game two turn-start snapshots.`);
      return 'rewound';
    }
  }
  else if (n === 'flourite eye’s song' || n === "flourite eye's song") {
    p.buffs.nextAttackMultiplier *= 1.5;
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
    room.turn.extraGambleAllowed = true;
    log(room, `${p.name} may play one additional card this turn.`);
  }
  else if (n === 'infinity') p.buffs.infinityCharges += 3;
  else if (n === 'the place above the grey fog') {
    const gained = gambleDraw(p, BETTER_GAMBLE, 5);
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
    log(room, `${p.name} gained ${gained.length} cards from the better wheel and may play another card.`);
  }
  else if (n === 'the overlord of centuries end') { p.buffs.cannotDropBelowOne = true; p.buffs.cannotDropBelowOneUntilOwnTurn = true; }
  else if (n === 'the father') {
    const restored = restoreFromDiscard(p, 3, c => c.stars < 5);
    room.turn.cardPlayLimit = Math.max(room.turn.cardPlayLimit, room.turn.cardsPlayed + 1);
    log(room, `${p.name} restored ${restored.length} cards and may play one extra card.`);
  }
  else if (n === 'piss dragon') { damage(30); p.buffs.damageCap = 30; p.buffs.damageCapUntilOwnTurn = true; }
  else if (n === 'the world') { opp.buffs.skipTurns += 1; }
  else if (n === 'bond forger') { p.buffs.bondForger = true; log(room, `${p.name} can now inspect the opponent's card abilities.`); }
  else if (n === 'world item') { p.buffs.worldItemUntilOwnTurn = true; log(room, `${p.name} is protected from status/multiplier effects until their next turn (manual edge cases may remain).`); }
  else if (n === 'have you ever played golf with your life on the line?') { applyDamage(room, p, p, 15, { isAttack: false }); p.buffs.nextAttackFlatBonus += 30; }
  else if (n === 'perfect warrior') { p.buffs.persistentAttackMultiplier *= 1.25; p.buffs.persistentDamageTakenMultiplier *= 0.75; manual(room, p, card); }
  else manual(room, p, card);
  return 'ok';
}

function snapshotRoom(room) {
  return {
    turn: JSON.parse(JSON.stringify(room.turn)),
    players: room.players.map(p => ({
      hp: p.hp, armor: p.armor, hand: [...p.hand], discard: [...p.discard], decks: JSON.parse(JSON.stringify(p.decks)), buffs: JSON.parse(JSON.stringify(p.buffs))
    }))
  };
}
function restoreSnapshot(room, snap) {
  room.turn = JSON.parse(JSON.stringify(snap.turn));
  room.players.forEach((p, i) => {
    Object.assign(p, JSON.parse(JSON.stringify(snap.players[i])));
  });
}
function saveTurnSnapshot(room) {
  room.history.push(snapshotRoom(room));
  if (room.history.length > 8) room.history.shift();
}

function canPlayCard(room, p, card) {
  if (!canAct(room, p)) return 'It is not your turn.';
  if (!p.hand.includes(card.id)) return 'That card is not in your hand.';
  if (p.buffs.forceSelfPunch) return 'Aura forces your next action to be a punch against yourself.';
  if (p.buffs.blockCardId === card.id) return 'That card is blocked this turn.';
  if (room.turn.goldenPairRequired && card.name !== room.turn.goldenPairRequired) return `You must play ${room.turn.goldenPairRequired} next.`;
  if (room.turn.noFiveStarExtraCards && room.turn.cardsPlayed >= 0 && card.stars === 5 && room.turn.firstCardWasQuintessential) return 'Quintessential Quintuplets does not allow 5-star follow-up cards.';
  if (!room.turn.mainActionUsed) return null;
  if (room.turn.cardsPlayed < room.turn.cardPlayLimit) return null;
  return 'You have already used your card/action allowance this turn.';
}

function playCard(room, p, card) {
  const opp = otherPlayer(room, p);
  const error = canPlayCard(room, p, card);
  if (error) return error;

  if (opp?.buffs.untargetableUntilOwnTurn && /damage|opponent|enemy|target/i.test(card.effect)) {
    return `${opp.name} is untargetable right now.`;
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
  room.turn.mainActionUsed = true;
  if (!wasQuintessential) room.turn.cardsPlayed += 1;
  log(room, `${p.name} played ${card.name} (${card.stars}★).`);

  if (opp?.buffs.heliocentricPunish) {
    opp.buffs.heliocentricPunish = false;
    applyDamage(room, opp, p, 10, { isAttack: false });
  }

  const result = resolveCard(room, p, opp, card);
  if (result !== 'rewound' && room.phase === 'playing') emitState(room);
  else emitState(room);
  return null;
}

io.on('connection', socket => {
  socket.on('createRoom', ({ name } = {}) => {
    const code = roomCode();
    const room = {
      code,
      phase: 'waiting',
      players: [makePlayer(socket, name, 0)],
      turn: newTurnState(0, 1),
      log: [],
      winner: null,
      history: [],
      pending: null,
    };
    rooms.set(code, room);
    socket.data.roomCode = code;
    socket.join(code);
    log(room, `${room.players[0].name} created room ${code}.`);
    emitState(room);
  });

  socket.on('joinRoom', ({ code, name } = {}) => {
    code = String(code || '').trim().toUpperCase();
    const room = rooms.get(code);
    if (!room) return socket.emit('errorMessage', 'Room not found.');
    if (room.players.length >= 2) return socket.emit('errorMessage', 'Room is full.');
    const p = makePlayer(socket, name, 1);
    room.players.push(p);
    room.phase = 'playing';
    socket.data.roomCode = code;
    socket.join(code);
    room.turn = newTurnState(Math.random() < 0.5 ? 0 : 1, 1);
    saveTurnSnapshot(room);
    log(room, `${p.name} joined. ${currentPlayer(room).name} goes first.`);
    emitState(room);
  });

  socket.on('playCard', ({ cardId } = {}) => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id); if (!p) return;
    const card = getCard(cardId); if (!card) return;
    const error = playCard(room, p, card);
    if (error) socket.emit('errorMessage', error);
  });

  socket.on('punch', () => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id); const opp = otherPlayer(room, p);
    if (!canAct(room, p)) return socket.emit('errorMessage', 'It is not your turn.');
    if (p.buffs.forceSelfPunch) {
      p.buffs.forceSelfPunch = false;
      room.turn.mainActionUsed = true;
      applyDamage(room, p, p, BASE_PUNCH_DAMAGE, { isPunch: true, isAttack: true });
      log(room, `${p.name} was forced to punch themself.`);
      emitState(room); return;
    }
    if (room.turn.mainActionUsed && !room.turn.extraPunchAllowed) return socket.emit('errorMessage', 'You already used your main action this turn.');
    if (opp.buffs.untargetableUntilOwnTurn) return socket.emit('errorMessage', `${opp.name} is untargetable right now.`);
    room.turn.mainActionUsed = true;
    room.turn.extraPunchAllowed = false;
    const base = p.buffs.punchDamageOverrideTurns > 0 ? p.buffs.punchDamageOverride : BASE_PUNCH_DAMAGE;
    applyDamage(room, p, opp, base, { isPunch: true, isAttack: true });
    emitState(room);
  });

  socket.on('gamble', () => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id);
    if (!canAct(room, p)) return socket.emit('errorMessage', 'It is not your turn.');
    if (p.buffs.forceSelfPunch) return socket.emit('errorMessage', 'Aura forces your next action to be a self-punch.');
    if (room.turn.mainActionUsed && !room.turn.extraGambleAllowed) return socket.emit('errorMessage', 'You already used your main action this turn.');
    room.turn.mainActionUsed = true;
    room.turn.extraGambleAllowed = false;
    const gained = gambleDraw(p, STANDARD_GAMBLE, 1);
    if (gained.length) log(room, `${p.name} gambled and drew a ${getCard(gained[0]).stars}★ card.`);
    else log(room, `${p.name} gambled, but the deck was empty.`);
    emitState(room);
  });

  socket.on('endTurn', () => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id);
    if (!canAct(room, p)) return socket.emit('errorMessage', 'It is not your turn.');
    if (room.turn.goldenPairRequired) {
      log(room, `${p.name} ended the turn without completing the Golden Ball pair; no pair bonus was gained.`);
    }
    saveTurnSnapshot(room);
    advanceTurn(room);
  });

  socket.on('disconnect', () => {
    const room = requireRoom(socket); if (!room) return;
    const p = playerBySocket(room, socket.id);
    if (p) log(room, `${p.name} disconnected.`);
    if (room.players.length <= 1 || room.phase === 'waiting') rooms.delete(room.code);
    else {
      room.phase = 'finished';
      room.winner = otherPlayer(room, p)?.name || null;
      emitState(room);
      setTimeout(() => rooms.delete(room.code), 60_000);
    }
  });
});

server.listen(PORT, () => console.log(`Fanmade TCG running on http://localhost:${PORT}`));
