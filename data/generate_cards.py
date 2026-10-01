import json, re
from collections import defaultdict, Counter
from pathlib import Path
from canon_references import SHOW_REFERENCES, PROFILES

ROOT = Path(__file__).resolve().parent
legacy_path = ROOT / 'legacy_cards.json'
legacy = json.loads(legacy_path.read_text(encoding='utf-8'))

ALIASES = {
    '86':'86 Eighty-Six', 'AOT':'Attack on Titan', 'Akame Ga Kill':'Akame ga Kill!',
    'Angel beats':'Angel Beats!', 'Apothecary Diaries':'The Apothecary Diaries',
    'Bocchi the rock':'Bocchi the Rock!', 'Bochi the rock':'Bocchi the Rock!',
    'Bunny girl senpai':'Rascal Does Not Dream of Bunny Girl Senpai',
    'Chainsaw man':'Chainsaw Man', 'Cyberpunk':'Cyberpunk: Edgerunners',
    'Cyberpunk Edgerunners':'Cyberpunk: Edgerunners', 'Dan Da dan':'Dandadan',
    'Demon slayer':'Demon Slayer', 'Devil is a partimer':'The Devil Is a Part-Timer!',
    'Fate':'Fate/stay night', 'Fate Stay Night UBW':'Fate/stay night', 'FMAB':'Fullmetal Alchemist: Brotherhood',
    'Fragrant Flower Blooms with dignity':'The Fragrant Flower Blooms with Dignity',
    'Horimya':'Horimiya', 'JJK':'Jujutsu Kaisen', 'Jojos':"JoJo's Bizarre Adventure",
    'Kaguya sama love is war':'Kaguya-sama: Love Is War', 'kaguya':'Kaguya-sama: Love Is War',
    'Lord of Mysteries':'Lord of Mysteries', 'Madoka':'Puella Magi Madoka Magica',
    'MHA':'My Hero Academia', 'My Hero Academia':'My Hero Academia',
    'Miss Koboyashi’s dragon maid':"Miss Kobayashi's Dragon Maid", 'My Dressup Darling':'My Dress-Up Darling',
    'one punch man':'One-Punch Man', 'Orb on the movements of the earth':'Orb: On the Movements of the Earth',
    'Oshi':'Oshi no Ko', 'Oshi No Ko':'Oshi no Ko', 'oshi':'Oshi no Ko',
    'overlord':'Overlord', 'Pokemon':'Pokémon', 'Rent a Girlfriend':'Rent-a-Girlfriend',
    'Rezero':'Re:Zero', 'SAO':'Sword Art Online', 'Shield hero':'The Rising of the Shield Hero',
    'Solo leveling':'Solo Leveling', 'Spy X Family':'SPY x FAMILY', 'Steins Gate':'Steins;Gate',
    'To Be Hero X':'To Be Hero X', 'Umamusume':'Uma Musume', 'Vivy':'Vivy: Fluorite Eye’s Song',
    'Wistoria':'Wistoria: Wand and Sword', 'You and I are Polar Opposites':'You and I Are Polar Opposites',
    'Yugioh':'Yu-Gi-Oh!', 'birdie wing':'Birdie Wing'
}

def canonical_origin(card):
    n = card['name'].lower().strip()
    if n.startswith('how cute'): return 'Kaguya-sama: Love Is War'
    if n.startswith('quintessential'): return 'The Quintessential Quintuplets'
    if n == 'petting a dog': return 'Chainsaw Man'
    return ALIASES.get(card.get('origin','').strip(), card.get('origin','').strip() or 'Miscellaneous')

def clean_legacy(card):
    c = dict(card)
    c['show'] = canonical_origin(c)
    c['origin'] = c['show']
    c['legacy'] = True
    k = c['name'].lower().strip()

    # Clean a few names that were malformed/typoed in the pasted source while preserving the card identity.
    if k.startswith('how cute'):
        c['name'] = 'How Cute'; k = 'how cute'
    elif k == 'rassengan':
        c['name'] = 'Rasengan'; k = 'rasengan'
    elif k == 'sukunas finger':
        c['name'] = "Sukuna's Finger"; k = "sukuna's finger"
    elif k.startswith('‘mgronalds worker') or k.startswith('mgronalds worker'):
        c['name'] = "MgRonald's Worker"; k = "mgronald's worker"
    elif k == 'perfect warrior':
        c['name'] = 'Perfect Warrior'; k = 'perfect warrior'

    # Rules/balance pass for the 300 HP / 20 punch / deck-draw ruleset.
    if k == 'petting a dog':
        c['name'] = 'Petting Pochita'; c['effect'] = 'Heal yourself 40 HP.'; c['action'] = {'type':'heal','amount':40,'target':'self'}
    simple = {
        'kyubey': ('Deal 20 damage to both opponents.', {'type':'split_enemies','amount':20}),
        'explosion': ('Deal 30 damage to one other player.', {'type':'damage','amount':30,'target':'other'}),
        'wendy': ('Heal yourself or your teammate 40 HP.', {'type':'heal','amount':40,'target':'ally'}),
        'breathing technique': ('Discard 1 card, then draw 2 cards.', {'type':'discard_draw','draw':2}),
        'rage shield': ('Deal 20 damage to both opponents.', {'type':'split_enemies','amount':20}),
        'pizzahut': ('Heal yourself 40 HP.', {'type':'heal','amount':40,'target':'self'}),
        'digivolve': ('Discard 1 card, then draw 2 cards.', {'type':'discard_draw','draw':2}),
        'rasengan': ('Deal 30 damage to one other player.', {'type':'damage','amount':30,'target':'other'}),
        'hit the nape': ('Deal 30 damage to one other player.', {'type':'damage','amount':30,'target':'other'}),
        'titan hardening': ('Give yourself 30 armor. Armor can exceed max HP.', {'type':'armor','amount':30,'target':'self'}),
        'requip': ('Give yourself or your teammate 60 armor.', {'type':'armor','amount':60,'target':'ally'}),
        'thunder spear': ('Deal 60 damage to one other player.', {'type':'damage','amount':60,'target':'other'}),
        'hinokami kagura': ('Deal 40 damage to both opponents.', {'type':'split_enemies','amount':40}),
        'one punch': ('Deal 60 damage to one other player.', {'type':'damage','amount':60,'target':'other'}),
        'equivalent exchange': ('Discard one 3★ card, then draw 2 cards.', {'type':'discard_star_draw','stars':3,'draw':2}),
        'excalibur': ('Deal 100 damage to one other player.', {'type':'damage','amount':100,'target':'other'}),
        'how cute': ('Deal 40 damage to both opponents.', {'type':'split_enemies','amount':40}),
    }
    if k in simple:
        c['effect'], c['action'] = simple[k]

    replacements = {
      'i mustn’t run away':'For your next 2 turns, you cannot play a card; your punch deals 50 damage instead of 20.',
      'apology':'Lose 20 HP, heal your teammate 40 HP, then draw 1 card.',
      'star eye':'The next time you draw at the start of your turn, draw 1 additional card.',
      'agnes tachyon':'Return one 3★ card from your discard pile to your hand, then draw 1 card.',
      'boredom':'Choose an opponent. They draw their top card; if it is 3★, they give it to you. Otherwise they keep it.',
      'unlimited blade works':'The next time you draw at the start of your turn, draw 1 additional card.',
      'the place above the grey fog':'Draw 5 cards, then you may play one additional card this turn.'
    }
    if k in replacements: c['effect'] = replacements[k]
    if k == 'fire dragon roar': c['effect'] = 'Deal 20 damage to one opponent and 10 damage to the other opponent.'
    if k == 'pull the chord': c['effect'] = 'Take 10 damage, then deal 40 damage to one other player.'
    c['effect'], c['action'] = normalize_pair(c.get('effect',''), c.get('action'))
    return c

def st(op, target=None, **kwargs):
    d={'op':op}
    if target is not None: d['target']=target
    d.update(kwargs)
    return d

def seq(*steps): return {'type':'sequence','steps':list(steps)}


def _round10(value):
    """Round flat combat-point values to clean multiples of 10.

    Counts/turns/multipliers are intentionally NOT passed through this helper.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return value
    sign = -1 if value < 0 else 1
    n = abs(float(value))
    if n == 0:
        return 0
    return sign * max(10, int((n + 5) // 10) * 10)


def _normalize_action_amounts(node):
    """Normalize only flat point `amount` fields; leave count/turn/mult values alone."""
    if isinstance(node, list):
        return [_normalize_action_amounts(x) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k == 'amount' and isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = _round10(v)
        else:
            out[k] = _normalize_action_amounts(v)
    return out


def _normalize_effect_text(text):
    """Keep displayed flat combat values synchronized with the clean-10 action values."""
    def repl(m):
        return str(abs(int(_round10(int(m.group(1))))))

    # Values explicitly written with combat units.
    text = re.sub(r'(?<![\d.])(\d+)(?=\s*(?:HP|hp|armor|damage|dmg)\b)', repl, text)
    # Flat modifiers that are written without repeating the unit immediately after the number.
    text = re.sub(r'(?<=\+)(\d+)(?=\s+on the next damage)', repl, text)
    text = re.sub(r'(?<=increased by )(\d+)(?!\s*%)(?=[\s.,;]|$)', repl, text)
    text = re.sub(r'(\d+)(?=\s+less damage)', repl, text)
    text = re.sub(r'(?<=damage by )(\d+)(?!\s*%)', repl, text)
    text = re.sub(r'(?<=attack by )(\d+)(?!\s*%)', repl, text)
    text = re.sub(r'(?<=gets \+)(\d+)(?=\s+damage)', repl, text)
    text = re.sub(r'(?<=give each \+)(\d+)(?=\s+damage)', repl, text)
    text = re.sub(r'(?<=give your teammate \+)(\d+)(?=\s+damage)', repl, text)
    return text


def normalize_pair(effect, action):
    return _normalize_effect_text(effect), _normalize_action_amounts(action)


# Hand-designed marquee cards. These are intentionally more thematic than the
# general rarity templates and use the PDF's pure-stat numbers as a power budget,
# not a hard rule. A powerful utility effect gives up raw damage/healing/armor.
FIVE_STAR_SPECIALS = {
    '86 Eighty-Six': ('Deal 85 damage to one other player. The next damage they take is increased by 25.', seq(st('damage','chosen_other',amount=85), st('mark','chosen_other',amount=25))),
    'Akame ga Kill!': ('You and your teammate each get +30 damage on your next attack, then draw 1 card.', seq(st('buff_attack','team',amount=30), st('draw','self',count=1))),
    'Angel Beats!': ('Gain 60 armor. The next 2 punches that would damage you deal 0 instead.', seq(st('armor','self',amount=60), st('punch_immunity','self',charges=2))),
    'Attack on Titan': ('Deal 50 damage to both opponents. The next damage each takes is increased by 10.', seq(st('damage','enemies',amount=50), st('mark','enemies',amount=10))),
    'Birdie Wing': ('Your next attack gets +60 damage, then draw 1 card.', seq(st('buff_attack','self',amount=60), st('draw','self',count=1))),
    'Bocchi the Rock!': ('You and your teammate each get +25 damage on your next attack. Draw 2 cards.', seq(st('buff_attack','team',amount=25), st('draw','self',count=2))),
    'Chainsaw Man': ('Deal 65 damage to one other player, then return one non-5★ card from your discard pile to your hand.', seq(st('damage','chosen_other',amount=65), st('return_discard','self',count=1,maxStars=4))),
    'Cyberpunk: Edgerunners': ('Take 30 damage, then deal 130 damage to one other player.', seq(st('damage','self',amount=30,attack=False), st('damage','chosen_other',amount=130))),
    'Dandadan': ('Heal both members of your team 35 HP and give each 15 armor.', seq(st('heal','team',amount=35), st('armor','team',amount=15))),
    'Darling in the Franxx': ('You and your teammate each get +30 damage on your next attack and gain 20 armor.', seq(st('buff_attack','team',amount=30), st('armor','team',amount=20))),
    'Demon Slayer': ('Take 15 damage, then deal 110 damage to one other player.', seq(st('damage','self',amount=15,attack=False), st('damage','chosen_other',amount=110))),
    'Digimon': ('Deal 80 damage to one other player and give yourself or your teammate 30 armor.', seq(st('damage','chosen_other',amount=80), st('armor','ally',amount=30))),
    'Evangelion': ('Until your next turn, no single hit can deal more than 30 damage to you. Your next attack gets +50 damage.', seq(st('damage_cap','self',amount=30), st('buff_attack','self',amount=50))),
    'Fairy Tail': ('Heal both members of your team 40 HP, then draw 1 card.', seq(st('heal','team',amount=40), st('draw','self',count=1))),
    'Frieren': ('Deal 65 damage to one other player, draw 1 card, and reduce the next damage you take by 25.', seq(st('damage','chosen_other',amount=65), st('draw','self',count=1), st('reduce_next','self',amount=25))),
    'Horimiya': ('Heal both members of your team 35 HP. Reduce the next damage your teammate takes by 25.', seq(st('heal','team',amount=35), st('reduce_next','ally',amount=25))),
    'Komi Can’t Communicate': ('Choose an opponent. Their next attack deals 30 less damage and they cannot heal until the start of their next turn. Draw 2 cards.', seq(st('buff_attack','chosen_enemy',amount=-30), st('prevent_heal','chosen_enemy',turns=1), st('draw','self',count=2))),
    "Miss Kobayashi's Dragon Maid": ('Give both members of your team 30 armor and heal each 20 HP.', seq(st('armor','team',amount=30), st('heal','team',amount=20))),
    'My Dress-Up Darling': ('Draw 3 cards. You may play one additional non-5★ card this turn, then discard 1 random card.', seq(st('draw','self',count=3), st('extra_play','self',count=1,maxStars=4), st('discard_random','self',count=1))),
    'My Hero Academia': ('Deal 105 damage to one other player. You and your teammate each get +10 damage on your next attack.', seq(st('damage','chosen_other',amount=105), st('buff_attack','team',amount=10))),
    'Naruto': ('Deal 80 damage to one other player and gain 20 armor.', seq(st('damage','chosen_other',amount=80), st('armor','self',amount=20))),
    'One-Punch Man': ('Deal 120 damage to one other player, then discard 1 random card from your hand.', seq(st('damage','chosen_other',amount=120), st('discard_random','self',count=1))),
    'Orb: On the Movements of the Earth': ('Draw 2 cards, then you may play one additional non-5★ card this turn. Afterward, your next attack deals 10 less damage.', seq(st('draw','self',count=2), st('extra_play','self',count=1,maxStars=4), st('buff_attack','self',amount=-10))),
    'Overlord': ('Deal 85 damage to one other player and gain 30 armor.', seq(st('damage','chosen_other',amount=85), st('armor','self',amount=30))),
    'Planetarian': ('Heal both members of your team 30 HP and give each 20 armor.', seq(st('heal','team',amount=30), st('armor','team',amount=20))),
    'Pokémon': ('Draw 3 cards and steal 1 random card from an opponent, then discard 1 random card from your hand.', seq(st('draw','self',count=3), st('steal_random','chosen_enemy',count=1), st('discard_random','self',count=1))),
    'Puella Magi Madoka Magica': ('Heal both members of your team 50 HP.', seq(st('heal','team',amount=50))),
    'Rascal Does Not Dream of Bunny Girl Senpai': ('Choose an opponent. They skip their next turn. Take 20 damage.', seq(st('skip_turn','chosen_enemy',count=1), st('damage','self',amount=20,attack=False))),
    'Rent-a-Girlfriend': ('Heal yourself or your teammate 85 HP, then draw 1 card.', seq(st('heal','ally',amount=85), st('draw','self',count=1))),
    'SPY x FAMILY': ('Heal both members of your team 20 HP, give each +20 damage on their next attack, then draw 1 card.', seq(st('heal','team',amount=20), st('buff_attack','team',amount=20), st('draw','self',count=1))),
    'Solo Leveling': ('Return up to 3 non-5★ cards from your discard pile to your hand and play one additional non-5★ card this turn. Take 20 damage.', seq(st('return_discard','self',count=3,maxStars=4), st('extra_play','self',count=1,maxStars=4), st('damage','self',amount=20,attack=False))),
    'Sword Art Online': ('Deal 80 damage to one other player, then you may punch once this turn.', seq(st('damage','chosen_other',amount=80), st('extra_punch','self'))),
    'The Apothecary Diaries': ('Heal yourself or your teammate 60 HP, then draw 2 cards.', seq(st('heal','ally',amount=60), st('draw','self',count=2))),
    'The Devil Is a Part-Timer!': ('Heal both members of your team 30 HP, give each +15 damage on their next attack, then draw 1 card.', seq(st('heal','team',amount=30), st('buff_attack','team',amount=15), st('draw','self',count=1))),
    'The Fragrant Flower Blooms with Dignity': ('Heal both members of your team 35 HP, give each 10 armor, then draw 1 card.', seq(st('heal','team',amount=35), st('armor','team',amount=10), st('draw','self',count=1))),
    'The Quintessential Quintuplets': ('Draw 2 cards. You may play one additional non-5★ card this turn, then heal yourself or your teammate 25 HP.', seq(st('draw','self',count=2), st('extra_play','self',count=1,maxStars=4), st('heal','ally',amount=25))),
    'The Rising of the Shield Hero': ('Give both members of your team 40 armor. Reduce the next damage your teammate takes by 20.', seq(st('armor','team',amount=40), st('reduce_next','ally',amount=20))),
    'Tokyo Ghoul': ('Take 25 damage, then deal 130 damage to one other player.', seq(st('damage','self',amount=25,attack=False), st('damage','chosen_other',amount=130))),
    'Vinland Saga': ('The next punch that would damage either member of your team deals 0 instead. Heal both members of your team 20 HP.', seq(st('punch_immunity','team',charges=1), st('heal','team',amount=20))),
    'Violet Evergarden': ('Heal both members of your team 35 HP, then return one non-5★ card from your discard pile to your hand.', seq(st('heal','team',amount=35), st('return_discard','self',count=1,maxStars=4))),
    'Wistoria: Wand and Sword': ('Deal 90 damage to one other player and gain 20 armor.', seq(st('damage','chosen_other',amount=90), st('armor','self',amount=20))),
    'You and I Are Polar Opposites': ('Heal both members of your team 30 HP. You and your teammate each get +15 damage on your next attack.', seq(st('heal','team',amount=30), st('buff_attack','team',amount=15))),
    'Yu-Gi-Oh!': ('Draw 2 cards. You may play one additional non-5★ card this turn, then discard 1 random card.', seq(st('draw','self',count=2), st('extra_play','self',count=1,maxStars=4), st('discard_random','self',count=1))),
}

SHOW_NAMES_BY_INDEX = sorted(SHOW_REFERENCES)

# Reference-level roles keep recognizable powers/items from receiving obviously wrong effects
# (for example, Charizard should not become a pure healer). Exact overrides cover iconic
# characters/abilities; keyword rules handle the rest while the show's profile is the fallback.
ROLE_OVERRIDES = {
    ('Pokémon','Pikachu'):'assault', ('Pokémon','Charizard'):'assault', ('Pokémon','Bulbasaur'):'team',
    ('Pokémon','Squirtle'):'team', ('Pokémon','Misty'):'team', ('Pokémon','Brock'):'team',
    ('Pokémon','Meowth'):'tempo', ('Pokémon','Poké Ball'):'control', ('Pokémon','Pokédex'):'tempo',
    ('Pokémon','Thunderbolt'):'assault', ('Pokémon','Ash Ketchum'):'team', ('Pokémon','Mewtwo'):'control',
    ('Pokémon','Legendary Pokémon'):'assault', ('Pokémon','Master Ball'):'control', ('Pokémon','Pokémon League'):'sport',
    ('Jujutsu Kaisen','Yuji Itadori'):'assault', ('Jujutsu Kaisen','Megumi Fushiguro'):'mystic',
    ('Jujutsu Kaisen','Nobara Kugisaki'):'assault', ('Jujutsu Kaisen','Kento Nanami'):'assault',
    ('Jujutsu Kaisen','Maki Zenin'):'assault', ('Jujutsu Kaisen','Toge Inumaki'):'control',
    ('Jujutsu Kaisen','Panda'):'team', ('Jujutsu Kaisen','Yuta Okkotsu'):'mystic',
    ('Jujutsu Kaisen','Cursed Speech'):'control', ('Jujutsu Kaisen','Satoru Gojo'):'control',
    ('Jujutsu Kaisen','Mahito'):'control', ('Jujutsu Kaisen','Suguru Geto'):'control',
    ('86 Eighty-Six','Shin Nouzen'):'assault', ('86 Eighty-Six','Vladilena Milizé'):'team',
    ('86 Eighty-Six','Raiden Shuga'):'team', ('86 Eighty-Six','Anju Emma'):'assault',
    ('86 Eighty-Six','Theoto Rikka'):'assault', ('86 Eighty-Six','Kurena Kukumila'):'assault',
    ('86 Eighty-Six','Fido'):'team', ('86 Eighty-Six','Frederica Rosenfort'):'control',
    ('86 Eighty-Six','Juggernaut'):'tactical', ('86 Eighty-Six','Spearhead Squadron'):'team',
    ('86 Eighty-Six','Reginleif'):'assault', ('86 Eighty-Six','Legion'):'assault',
    ('86 Eighty-Six','Morpho'):'assault', ('86 Eighty-Six','San Magnolia'):'control',
    ('86 Eighty-Six','Giad Federacy'):'team',
    ('Attack on Titan','Armin Arlert'):'control', ('Attack on Titan','Hange Zoë'):'tactical',
    ('Attack on Titan','Erwin Smith'):'team', ('Attack on Titan','Reiner Braun'):'tactical',
    ('Attack on Titan','Annie Leonhart'):'assault', ('Attack on Titan','ODM Gear'):'tempo',
    ('Attack on Titan','Levi Ackerman'):'assault',
    ('Chainsaw Man','Denji'):'risk', ('Chainsaw Man','Power'):'risk', ('Chainsaw Man','Aki Hayakawa'):'tactical',
    ('Chainsaw Man','Himeno'):'risk', ('Chainsaw Man','Kobeni Higashiyama'):'tempo', ('Chainsaw Man','Kishibe'):'tactical',
    ('Demon Slayer','Shinobu Kocho'):'control', ('Demon Slayer','Kanao Tsuyuri'):'tactical',
    ('Demon Slayer','Mitsuri Kanroji'):'team', ('Demon Slayer','Tengen Uzui'):'tempo',
    ('Naruto','Sakura Haruno'):'team', ('Naruto','Kakashi Hatake'):'tactical', ('Naruto','Tsunade'):'team',
    ('Naruto','Gaara'):'tactical', ('Naruto','Shadow Clone Jutsu'):'tempo', ('Naruto','Chidori'):'assault',
    ('My Hero Academia','Ochaco Uraraka'):'control', ('My Hero Academia','Shota Aizawa'):'control',
    ('My Hero Academia','Hawks'):'tempo', ('My Hero Academia','Class 1-A'):'team',
    ('One-Punch Man','King'):'control', ('One-Punch Man','Mumen Rider'):'team',
    ('One-Punch Man','Hero Association'):'team', ('One-Punch Man','Monster Association'):'risk',
    ('Fullmetal Alchemist: Brotherhood','Winry Rockbell'):'team', ('Fullmetal Alchemist: Brotherhood','Riza Hawkeye'):'assault',
    ('Fullmetal Alchemist: Brotherhood','Ling Yao'):'tempo', ('Fullmetal Alchemist: Brotherhood','Greed'):'tactical',
    ('Fullmetal Alchemist: Brotherhood','Scar'):'assault', ('Fullmetal Alchemist: Brotherhood','Lust'):'assault',
    ('Fullmetal Alchemist: Brotherhood','Envy'):'control',
    ('SPY x FAMILY','Loid Forger'):'tactical', ('SPY x FAMILY','Yor Forger'):'assault',
    ('SPY x FAMILY','Anya Forger'):'control', ('SPY x FAMILY','Becky Blackbell'):'social',
    ('SPY x FAMILY','Damian Desmond'):'social', ('SPY x FAMILY','Fiona Frost'):'tactical',
    ('Solo Leveling','Yoo Jinho'):'team', ('Solo Leveling','Cha Hae-In'):'assault', ('Solo Leveling','Go Gunhee'):'team',
    ('Solo Leveling','The System'):'tempo', ('Solo Leveling','Igris'):'assault', ('Solo Leveling','Iron'):'tactical',
    ('The Apothecary Diaries','Maomao'):'tactical', ('The Apothecary Diaries','Jinshi'):'control',
    ('The Apothecary Diaries','Gaoshun'):'team', ('The Apothecary Diaries','Gyokuyou'):'team',
    ('The Apothecary Diaries','Luomen'):'team', ('The Apothecary Diaries','Poisoned Face Powder'):'control',
    ('Yu-Gi-Oh!','Yugi Muto'):'control', ('Yu-Gi-Oh!','Seto Kaiba'):'assault', ('Yu-Gi-Oh!','Joey Wheeler'):'risk',
    ('Yu-Gi-Oh!','Téa Gardner'):'team', ('Yu-Gi-Oh!','Dark Magician'):'mystic', ('Yu-Gi-Oh!','Blue-Eyes White Dragon'):'assault',
    ('Yu-Gi-Oh!','Red-Eyes Black Dragon'):'assault', ('Yu-Gi-Oh!','Duel Disk'):'tempo',
}

ROLE_OVERRIDES.update({
    # Fairy Tail
    ('Fairy Tail','Natsu Dragneel'):'assault', ('Fairy Tail','Lucy Heartfilia'):'mystic',
    ('Fairy Tail','Gray Fullbuster'):'assault', ('Fairy Tail','Happy'):'tempo',
    ('Fairy Tail','Gajeel Redfox'):'assault', ('Fairy Tail','Laxus Dreyar'):'assault',
    ('Fairy Tail','Mirajane Strauss'):'assault', ('Fairy Tail','Jellal Fernandes'):'mystic',
    ('Fairy Tail','Makarov Dreyar'):'team', ('Fairy Tail','Aquarius'):'assault',
    ('Fairy Tail','Dragon Force'):'assault', ('Fairy Tail','Fairy Law'):'control',
    ('Fairy Tail','Urano Metria'):'assault', ('Fairy Tail','Grand Chariot'):'assault', ('Fairy Tail','Fairy Glitter'):'assault',
    # My Hero Academia
    ('My Hero Academia','Izuku Midoriya'):'assault', ('My Hero Academia','Katsuki Bakugo'):'assault',
    ('My Hero Academia','Shoto Todoroki'):'assault', ('My Hero Academia','Tenya Iida'):'tempo',
    ('My Hero Academia','Endeavor'):'assault', ('My Hero Academia','Mirko'):'assault',
    ('My Hero Academia','One For All'):'assault', ('My Hero Academia','All For One'):'control',
    ('My Hero Academia','Tomura Shigaraki'):'risk', ('My Hero Academia','Dabi'):'risk', ('My Hero Academia','United States of Smash'):'assault',
    # Digimon Adventure
    ('Digimon','Tai and Agumon'):'assault', ('Digimon','Matt and Gabumon'):'assault',
    ('Digimon','Sora and Biyomon'):'team', ('Digimon','Izzy and Tentomon'):'tactical',
    ('Digimon','Mimi and Palmon'):'team', ('Digimon','Joe and Gomamon'):'team',
    ('Digimon','T.K. and Patamon'):'team', ('Digimon','Kari and Gatomon'):'team',
    ('Digimon','Crest of Courage'):'assault', ('Digimon','DigiDestined'):'team',
    ('Digimon','Myotismon'):'control', ('Digimon','WarGreymon'):'assault',
    # Darling in the Franxx
    ('Darling in the Franxx','Hiro'):'team', ('Darling in the Franxx','Zero Two'):'assault',
    ('Darling in the Franxx','Ichigo'):'team', ('Darling in the Franxx','Goro'):'team',
    ('Darling in the Franxx','Delphinium'):'assault', ('Darling in the Franxx','Genista'):'assault',
    ('Darling in the Franxx','Argentea'):'assault', ('Darling in the Franxx','Queen Pike'):'assault',
    ('Darling in the Franxx','Klaxosaur Princess'):'mystic',
    # Shield Hero
    ('The Rising of the Shield Hero','Naofumi Iwatani'):'tactical', ('The Rising of the Shield Hero','Raphtalia'):'assault',
    ('The Rising of the Shield Hero','Filo'):'assault', ('The Rising of the Shield Hero','Melty Q Melromarc'):'team',
    ('The Rising of the Shield Hero','Rishia Ivyred'):'team', ('The Rising of the Shield Hero','Motoyasu Kitamura'):'assault',
    ('The Rising of the Shield Hero','Ren Amaki'):'assault', ('The Rising of the Shield Hero','Itsuki Kawasumi'):'assault',
    ('The Rising of the Shield Hero','Air Strike Shield'):'tactical', ('The Rising of the Shield Hero','Shield Prison'):'control',
    ('The Rising of the Shield Hero','Iron Maiden'):'assault', ('The Rising of the Shield Hero','Blood Sacrifice'):'risk',
    ('The Rising of the Shield Hero','Curse Series'):'risk', ('The Rising of the Shield Hero','Glass'):'assault', ('The Rising of the Shield Hero',"L'Arc Berg"):'assault',
    # Frieren
    ('Frieren','Fern'):'assault', ('Frieren','Stark'):'assault', ('Frieren','Himmel'):'team',
    ('Frieren','Heiter'):'team', ('Frieren','Eisen'):'tactical', ('Frieren','Flamme'):'mystic',
    ('Frieren','Denken'):'tactical', ('Frieren','Übel'):'risk', ('Frieren','Lawine'):'mystic', ('Frieren','Kanne'):'mystic',
    ('Frieren','Mimic Chest'):'risk', ('Frieren','Mana Suppression'):'control', ('Frieren','Serie'):'mystic', ('Frieren','First-Class Mage Exam'):'tempo',
    # Madoka
    ('Puella Magi Madoka Magica','Madoka Kaname'):'team', ('Puella Magi Madoka Magica','Homura Akemi'):'control',
    ('Puella Magi Madoka Magica','Sayaka Miki'):'assault', ('Puella Magi Madoka Magica','Mami Tomoe'):'assault',
    ('Puella Magi Madoka Magica','Kyoko Sakura'):'assault', ('Puella Magi Madoka Magica','Soul Gem'):'risk',
    ('Puella Magi Madoka Magica','Grief Seed'):'risk', ('Puella Magi Madoka Magica',"Homura's Shield"):'control',
    ('Puella Magi Madoka Magica',"Sayaka's Swords"):'assault', ('Puella Magi Madoka Magica',"Kyoko's Spear"):'assault',
    ('Puella Magi Madoka Magica','Tiro Finale'):'assault', ('Puella Magi Madoka Magica','The Contract'):'risk',
    # Sword Art Online
    ('Sword Art Online','Kirito'):'assault', ('Sword Art Online','Asuna'):'assault', ('Sword Art Online','Klein'):'team',
    ('Sword Art Online','Agil'):'team', ('Sword Art Online','Silica'):'team', ('Sword Art Online','Lisbeth'):'team',
    ('Sword Art Online','Yui'):'control', ('Sword Art Online','Leafa'):'assault', ('Sword Art Online','Sinon'):'assault',
    ('Sword Art Online','Elucidator'):'assault', ('Sword Art Online','Dual Blades'):'assault', ('Sword Art Online','Starburst Stream'):'assault',
    ('Sword Art Online',"Mother's Rosario"):'assault', ('Sword Art Online','Aincrad'):'tactical', ('Sword Art Online','Heathcliff'):'tactical',
    # Overlord
    ('Overlord','Ainz Ooal Gown'):'control', ('Overlord','Albedo'):'tactical', ('Overlord','Shalltear Bloodfallen'):'risk',
    ('Overlord','Demiurge'):'control', ('Overlord','Cocytus'):'assault', ('Overlord','Aura Bella Fiora'):'team',
    ('Overlord','Mare Bello Fiore'):'mystic', ('Overlord','Sebas Tian'):'assault', ('Overlord',"Pandora's Actor"):'control',
    ('Overlord','Great Tomb of Nazarick'):'tactical', ('Overlord','Grasp Heart'):'control', ('Overlord','Fallen Down'):'assault',
    ('Overlord','The Goal of All Life Is Death'):'control', ('Overlord','Super-Tier Magic'):'mystic', ('Overlord','Momon'):'assault',
    # JoJo
    ("JoJo's Bizarre Adventure",'Jonathan Joestar'):'assault', ("JoJo's Bizarre Adventure",'Joseph Joestar'):'tactical',
    ("JoJo's Bizarre Adventure",'Jotaro Kujo'):'assault', ("JoJo's Bizarre Adventure",'Josuke Higashikata'):'team',
    ("JoJo's Bizarre Adventure",'Giorno Giovanna'):'mystic', ("JoJo's Bizarre Adventure",'Jolyne Cujoh'):'assault',
    ("JoJo's Bizarre Adventure",'Hamon'):'assault', ("JoJo's Bizarre Adventure",'Hermit Purple'):'control',
    ("JoJo's Bizarre Adventure",'Crazy Diamond'):'team', ("JoJo's Bizarre Adventure",'Stone Free'):'assault',
    ("JoJo's Bizarre Adventure",'Star Platinum'):'assault', ("JoJo's Bizarre Adventure",'Killer Queen'):'risk',
    ("JoJo's Bizarre Adventure",'Gold Experience Requiem'):'control', ("JoJo's Bizarre Adventure",'King Crimson'):'control',
    ("JoJo's Bizarre Adventure",'Made in Heaven'):'tempo',
    # Fate
    ('Fate/stay night','Shirou Emiya'):'assault', ('Fate/stay night','Rin Tohsaka'):'mystic', ('Fate/stay night','Archer'):'assault',
    ('Fate/stay night','Sakura Matou'):'mystic', ('Fate/stay night','Rider'):'tempo', ('Fate/stay night','Lancer'):'assault',
    ('Fate/stay night','Illyasviel von Einzbern'):'mystic', ('Fate/stay night','Kirei Kotomine'):'control',
    ('Fate/stay night','Command Spell'):'control', ('Fate/stay night','Rho Aias'):'tactical', ('Fate/stay night','Gáe Bolg'):'assault',
    ('Fate/stay night','Gate of Babylon'):'assault', ('Fate/stay night','Avalon'):'tactical', ('Fate/stay night','Berserker'):'risk', ('Fate/stay night','Gilgamesh'):'assault',
    # Tokyo Ghoul
    ('Tokyo Ghoul','Ken Kaneki'):'risk', ('Tokyo Ghoul','Touka Kirishima'):'assault', ('Tokyo Ghoul','Hideyoshi Nagachika'):'team',
    ('Tokyo Ghoul','Hinami Fueguchi'):'team', ('Tokyo Ghoul','Nishiki Nishio'):'assault', ('Tokyo Ghoul','Shuu Tsukiyama'):'risk',
    ('Tokyo Ghoul','Koutarou Amon'):'assault', ('Tokyo Ghoul','Juuzou Suzuya'):'assault', ('Tokyo Ghoul','Anteiku'):'team',
    ('Tokyo Ghoul','Quinque'):'assault', ('Tokyo Ghoul','Kakuja'):'risk', ('Tokyo Ghoul','Kishou Arima'):'assault',
    ('Tokyo Ghoul','Eto Yoshimura'):'risk', ('Tokyo Ghoul','One-Eyed Owl'):'risk', ('Tokyo Ghoul','Centipede'):'risk',
    # Wistoria
    ('Wistoria: Wand and Sword','Will Serfort'):'assault', ('Wistoria: Wand and Sword','Elfaria Albis Serfort'):'mystic',
    ('Wistoria: Wand and Sword','Colette Loire'):'team', ('Wistoria: Wand and Sword','Sion Ulster'):'assault',
    ('Wistoria: Wand and Sword','Julius Reinberg'):'mystic', ('Wistoria: Wand and Sword','Wignall Lindorr'):'mystic',
    ('Wistoria: Wand and Sword','Lihanna Owenzaus'):'assault', ('Wistoria: Wand and Sword','Rosty Naumann'):'team',
    ('Wistoria: Wand and Sword','Workner Norgram'):'team', ('Wistoria: Wand and Sword','Kiki'):'team',
    ('Wistoria: Wand and Sword','Dungeon'):'risk', ('Wistoria: Wand and Sword','Magia Vander'):'mystic', ('Wistoria: Wand and Sword','Ice Faction'):'mystic',
    # Dragon Maid
    ("Miss Kobayashi's Dragon Maid",'Kobayashi'):'social', ("Miss Kobayashi's Dragon Maid",'Tohru'):'assault',
    ("Miss Kobayashi's Dragon Maid",'Kanna Kamui'):'assault', ("Miss Kobayashi's Dragon Maid",'Elma'):'assault',
    ("Miss Kobayashi's Dragon Maid",'Lucoa'):'mystic', ("Miss Kobayashi's Dragon Maid",'Fafnir'):'risk',
    ("Miss Kobayashi's Dragon Maid",'Ilulu'):'assault', ("Miss Kobayashi's Dragon Maid",'Riko Saikawa'):'social',
    ("Miss Kobayashi's Dragon Maid",'Makoto Takiya'):'social', ("Miss Kobayashi's Dragon Maid",'Shouta Magatsuchi'):'mystic',
    ("Miss Kobayashi's Dragon Maid",'Dragon Transformation'):'assault', ("Miss Kobayashi's Dragon Maid",'Chaos Faction'):'risk',
    ("Miss Kobayashi's Dragon Maid",'Harmony Faction'):'team', ("Miss Kobayashi's Dragon Maid","Kanna's Lightning"):'assault',
    # Angel Beats
    ('Angel Beats!','Yuzuru Otonashi'):'team', ('Angel Beats!','Yuri Nakamura'):'tactical', ('Angel Beats!','Hinata Hideki'):'team',
    ('Angel Beats!','Yui'):'tempo', ('Angel Beats!','Iwasawa Masami'):'tempo', ('Angel Beats!','Ayato Naoi'):'control',
    ('Angel Beats!','TK'):'tempo', ('Angel Beats!','Noda'):'assault', ('Angel Beats!','Shiina'):'assault',
    ('Angel Beats!','Girls Dead Monster'):'tempo', ('Angel Beats!','Hand Sonic'):'assault', ('Angel Beats!','Distortion'):'tactical',
    ('Angel Beats!','Harmonics'):'tempo', ('Angel Beats!','Operation Tornado'):'tactical', ('Angel Beats!','SSS Battlefront'):'team',
    # Bocchi the Rock!
    ('Bocchi the Rock!','Hitori Gotoh'):'tempo', ('Bocchi the Rock!','Nijika Ijichi'):'team', ('Bocchi the Rock!','Ryo Yamada'):'tempo',
    ('Bocchi the Rock!','Ikuyo Kita'):'tempo', ('Bocchi the Rock!','Seika Ijichi'):'tactical', ('Bocchi the Rock!','PA-san'):'tactical',
    ('Bocchi the Rock!','Kikuri Hiroi'):'risk', ('Bocchi the Rock!','Eliza Shimizu'):'tempo', ('Bocchi the Rock!','guitarhero'):'tempo',
    ('Bocchi the Rock!','STARRY'):'team', ('Bocchi the Rock!','Kessoku Band'):'team', ('Bocchi the Rock!',"Bocchi's Bottle Slide"):'assault',
    ('Bocchi the Rock!','Guitar, Loneliness and the Blue Planet'):'tempo', ('Bocchi the Rock!','If I Could Be a Constellation'):'tempo',
    ('Bocchi the Rock!','School Festival Live'):'tempo', ('Bocchi the Rock!','That Band'):'tempo',
    # Planetarian
    ('Planetarian','Yumemi Hoshino'):'social', ('Planetarian','The Junker'):'tactical', ('Planetarian','Miss Jena'):'tempo',
    ('Planetarian','Flowercrest Department Store'):'tactical', ('Planetarian','The Planetarium'):'social', ('Planetarian','Star Projection'):'tempo',
    ('Planetarian','Constant Rain'):'tactical', ('Planetarian','Automated War Machine'):'assault', ('Planetarian',"Scavenger's Pack"):'tactical',
    ('Planetarian','Projector Repair'):'tactical', ('Planetarian','2,500,000th Customer'):'social', ('Planetarian','Heaven for Robots'):'social',
    ('Planetarian','Emergency Battery'):'tactical', ('Planetarian','Memory Card'):'tactical', ('Planetarian','Final Escort'):'team',
    # Vivy
    ('Vivy: Fluorite Eye’s Song','Vivy'):'tempo', ('Vivy: Fluorite Eye’s Song','Matsumoto'):'control', ('Vivy: Fluorite Eye’s Song','Estella'):'team',
    ('Vivy: Fluorite Eye’s Song','Elizabeth'):'assault', ('Vivy: Fluorite Eye’s Song','Grace'):'team', ('Vivy: Fluorite Eye’s Song','Ophelia'):'tempo',
    ('Vivy: Fluorite Eye’s Song','Antonio'):'control', ('Vivy: Fluorite Eye’s Song','Yugo Kakitani'):'assault', ('Vivy: Fluorite Eye’s Song','Momoka Kirishima'):'social',
    ('Vivy: Fluorite Eye’s Song','Sunrise'):'tactical', ('Vivy: Fluorite Eye’s Song','Metal Float'):'risk', ('Vivy: Fluorite Eye’s Song','Singularity Project'):'control',
    ('Vivy: Fluorite Eye’s Song','The Archive'):'control', ('Vivy: Fluorite Eye’s Song','Toak'):'assault', ('Vivy: Fluorite Eye’s Song','Diva'):'tempo',
    # To Be Hero X
    ('To Be Hero X','Lin Ling / The Commoner'):'team', ('To Be Hero X','Nice'):'assault', ('To Be Hero X','E-Soul'):'assault',
    ('To Be Hero X','Lucky Cyan'):'tempo', ('To Be Hero X','Loli'):'tactical', ('To Be Hero X','Ghostblade'):'assault',
    ('To Be Hero X','The Johnnies'):'team', ('To Be Hero X','Dragon Boy'):'assault', ('To Be Hero X','Ahu'):'team', ('To Be Hero X','Moon'):'social',
    ('To Be Hero X','Trust Value'):'control', ('To Be Hero X','Fear'):'control', ('To Be Hero X','Smile'):'control',
    ('To Be Hero X','Hero Affairs Commission'):'control', ('To Be Hero X','Heroes Tournament'):'tempo',
})

KEYWORD_ROLES = [
    ('control', ('geass','death note','eyes','command','domain','speech','tarot','seer','trust value','time loop','body swap','invisible','contract','rule','world line','reading steiner','divergence','notebook','profiling','hacking','system','master ball','poké ball','prison','labyrinth')),
    ('tactical', ('shield','armor','hardening','a.t. field','barrier','fortress','juggernaut','reginleif','quinque','pendant','brooch','medicine','repair','rune','wis')),
    ('assault', ('spear','sword','blade','gun','punch','thunder','lightning','fire','flame','explosion','chainsaw','black flash','roar','smash','chariot','bolg','incursio','pumpkin','morpho','titan','dragon','devil','demon','attack','kagune','kakuja','centipede','mech','eva unit','greymon','garurumon','angemon')),
    ('risk', ('curse','psychosis','impact','walpurgisnacht','berserker','blood sacrifice','monster','witch','forbidden','one-eyed owl','future devil','ghost devil','eternity devil','gun devil')),
    ('tempo', ('song','music','band','live','idol','photoshoot','festival','race','winning','projection','typewriter','letters','phonewave','d-mail','gear','speed','sewing','makeup','costume','study session','exam')),
    ('social', ('cake','bakery','house','date','confession','kiss','love','wedding','sisters','friends','maid','flower','family','bouquet','aquarium','grandmother')),
    ('team', ('squadron','guild','class','team','battlefront','club','academy','league','council','federacy','alliance','digiDestined'.lower(),'operation strix','wise','garden')),
]

def reference_profile(show, ref, fallback):
    exact = ROLE_OVERRIDES.get((show, ref))
    if exact: return exact
    key = ref.casefold()
    for role, words in KEYWORD_ROLES:
        if any(w in key for w in words): return role
    return fallback

SLOT_OVERRIDES = {
    ('The Rising of the Shield Hero','Naofumi Iwatani',3): 6,
    ('The Rising of the Shield Hero','Air Strike Shield',3): 6,
    ('My Hero Academia','Dabi',4): 0,
    ('Jujutsu Kaisen','Yuji Itadori',3): 0,
    ('Fairy Tail','Natsu Dragneel',3): 0,
    ('Pokémon','Pikachu',3): 1,
    ('Pokémon','Charizard',3): 2,
    ('Pokémon','Squirtle',3): 8,
    ('86 Eighty-Six','Shin Nouzen',3): 0,
    ('86 Eighty-Six','Vladilena Milizé',3): 1,
    ('Frieren','Fern',3): 0,
    ('Frieren','Stark',3): 3,
    ('Sword Art Online','Kirito',3): 0,
    ('One-Punch Man','Genos',3): 3,
    ('Naruto','Naruto Uzumaki',3): 1,
    ('Naruto','Sasuke Uchiha',3): 4,
    ('Demon Slayer','Tanjiro Kamado',3): 1,
    ('Demon Slayer','Zenitsu Agatsuma',3): 8,
}

def themed_slot_for(show, ref, stars, profile):
    """Choose from effect slots that make sense for the reference role.
    Offensive/risk references avoid support-only or backwards-feeling templates.
    """
    import hashlib
    exact_slot = SLOT_OVERRIDES.get((show, ref, stars))
    if exact_slot is not None:
        return exact_slot
    pools = {
        ('assault',3): [0,1,2,3,4,5,6,8],
        ('assault',4): [0,1,2,3,4],
        ('risk',3): [0,1,2,3,4,5,7,8,9],
        ('risk',4): [0,1,2,3],
        ('team',3): list(range(10)), ('team',4): list(range(5)),
        ('control',3): list(range(10)), ('control',4): list(range(5)),
        ('social',3): list(range(10)), ('social',4): list(range(5)),
        ('tempo',3): list(range(10)), ('tempo',4): list(range(5)),
        ('sport',3): list(range(10)), ('sport',4): list(range(5)),
        ('mystic',3): list(range(10)), ('mystic',4): list(range(5)),
        ('tactical',3): list(range(10)), ('tactical',4): list(range(5)),
    }
    pool = pools.get((profile,stars), [0])
    h = int(hashlib.sha256(f'{show}|{ref}|{stars}|slot'.encode()).hexdigest()[:8], 16)
    return pool[h % len(pool)]

# Effects are balanced around the PDF baselines as budgets, not hard caps.
# Card advantage, denial, delayed damage, targeting limits, self-damage, and setup all trade against raw stats.
def generated_effect(profile, stars, slot, show_index):
    # Tiny amount variation prevents every show from feeling numerically identical without leaving the rarity budget.
    j = show_index % 3
    dmg30 = 28 + j  # 28-30
    dmg60 = 56 + j*2  # 56-60

    if stars == 3:
        if profile == 'assault':
            table = [
                (f'Deal {dmg30} damage to one other player.', seq(st('damage','chosen_other',amount=dmg30))),
                ('Deal 20 damage to one other player. Your next attack gets +10 damage.', seq(st('damage','chosen_other',amount=20),st('buff_attack','self',amount=10))),
                ('Deal 15 damage to both opponents.', seq(st('damage','enemies',amount=15))),
                ('Take 10 damage, then deal 40 damage to one other player.', seq(st('damage','self',amount=10,attack=False),st('damage','chosen_other',amount=40))),
                ('Deal 20 damage to one other player. The next damage they take is increased by 10.', seq(st('damage','chosen_other',amount=20),st('mark','chosen_other',amount=10))),
                ('Deal 20 damage to one other player, then draw 1 card.', seq(st('damage','chosen_other',amount=20),st('draw','self',count=1))),
                ('Deal 18 damage to one other player and gain 12 armor.', seq(st('damage','chosen_other',amount=18),st('armor','self',amount=12))),
                ('Choose an opponent. Their next attack deals 15 less damage.', seq(st('buff_attack','chosen_enemy',amount=-15))),
                ('Choose one other player. At the start of their next turn, deal 35 damage to them.', seq(st('delayed_damage','chosen_other',amount=35,turns=1))),
                ('Give your teammate +20 damage on their next attack.', seq(st('buff_attack','ally',amount=20))),
            ]
        elif profile == 'team':
            table = [
                ('Deal 20 damage to one other player and give your teammate 10 armor.', seq(st('damage','chosen_other',amount=20),st('armor','ally',amount=10))),
                ('Heal yourself or your teammate 40 HP.', seq(st('heal','ally',amount=40))),
                ('Give yourself or your teammate 30 armor.', seq(st('armor','ally',amount=30))),
                ('Heal your teammate 25 HP and give them 15 armor.', seq(st('heal','ally',amount=25),st('armor','ally',amount=15))),
                ('Draw 1 card and give your teammate 15 armor.', seq(st('draw','self',count=1),st('armor','ally',amount=15))),
                ('Heal both members of your team 20 HP.', seq(st('heal','team',amount=20))),
                ('Give both members of your team 15 armor.', seq(st('armor','team',amount=15))),
                ('Deal 20 damage to one other player; your teammate heals 15 HP.', seq(st('damage','chosen_other',amount=20),st('heal','ally',amount=15))),
                ('Your teammate ignores the next punch that would damage them.', seq(st('punch_immunity','ally',charges=1))),
                ('Reduce the next damage your teammate takes by 25.', seq(st('reduce_next','ally',amount=25))),
            ]
        elif profile == 'control':
            table = [
                ('Deal 15 damage to an opponent and they discard 1 random card.', seq(st('damage','chosen_enemy',amount=15),st('discard_random','chosen_enemy',count=1))),
                ('Deal 20 damage to an opponent. They cannot heal until the start of their next turn.', seq(st('damage','chosen_enemy',amount=20),st('prevent_heal','chosen_enemy',turns=1))),
                ('Choose an opponent. Their next attack deals 20 less damage.', seq(st('buff_attack','chosen_enemy',amount=-20))),
                ('Mark one other player. The next damage they take is increased by 20.', seq(st('mark','chosen_other',amount=20))),
                ('Draw 2 cards, then discard 1 random card from your hand.', seq(st('draw','self',count=2),st('discard_random','self',count=1))),
                ('Choose an opponent. At the start of their next turn, deal 30 damage to them.', seq(st('delayed_damage','chosen_enemy',amount=30,turns=1))),
                ('Choose an opponent. Their next action is a punch against themself.', seq(st('force_self_punch','chosen_enemy'))),
                ('Choose an opponent. They discard 1 random card; then you draw 1 card.', seq(st('discard_random','chosen_enemy',count=1),st('draw','self',count=1))),
                ('Until your next turn, you cannot be targeted by attacks.', seq(st('untargetable','self'))),
                ('Deal 15 damage to an opponent and reduce the next damage you take by 15.', seq(st('damage','chosen_enemy',amount=15),st('reduce_next','self',amount=15))),
            ]
        elif profile == 'social':
            table = [
                ('Heal yourself or your teammate 35 HP, then draw 1 card.', seq(st('heal','ally',amount=35),st('draw','self',count=1))),
                ('Draw 2 cards, then discard 1 random card from your hand.', seq(st('draw','self',count=2),st('discard_random','self',count=1))),
                ('Heal your teammate 25 HP and give them 10 armor.', seq(st('heal','ally',amount=25),st('armor','ally',amount=10))),
                ('Give yourself or your teammate 25 armor, then draw 1 card.', seq(st('armor','ally',amount=25),st('draw','self',count=1))),
                ('Lose 15 HP, heal your teammate 35 HP, then draw 1 card.', seq(st('damage','self',amount=15,attack=False),st('heal','ally',amount=35),st('draw','self',count=1))),
                ('Heal both members of your team 20 HP.', seq(st('heal','team',amount=20))),
                ('Until your next turn, you cannot be targeted by attacks.', seq(st('untargetable','self'))),
                ('Heal your teammate 20 HP and reduce the next damage they take by 15.', seq(st('heal','ally',amount=20),st('reduce_next','ally',amount=15))),
                ('Return one 3★ card from your discard pile to your hand.', seq(st('return_discard','self',count=1,stars=3))),
                ('Heal your teammate 15 HP and give them +15 damage on their next attack.', seq(st('heal','ally',amount=15),st('buff_attack','ally',amount=15))),
            ]
        elif profile == 'tempo':
            table = [
                ('Deal 20 damage to one other player, then draw 1 card.', seq(st('damage','chosen_other',amount=20),st('draw','self',count=1))),
                ('Draw 2 cards, then discard 1 random card from your hand.', seq(st('draw','self',count=2),st('discard_random','self',count=1))),
                ('Draw 1 card. Your next attack gets +10 damage.', seq(st('draw','self',count=1),st('buff_attack','self',amount=10))),
                ('Return one 3★ card from your discard pile to your hand, then discard 1 random card.', seq(st('return_discard','self',count=1,stars=3),st('discard_random','self',count=1))),
                ('Heal yourself 20 HP, then draw 1 card.', seq(st('heal','self',amount=20),st('draw','self',count=1))),
                ('Gain 20 armor, then draw 1 card.', seq(st('armor','self',amount=20),st('draw','self',count=1))),
                ('You may punch once after playing this card.', seq(st('extra_punch','self'))),
                ('You may play one additional 3★ card this turn.', seq(st('extra_play','self',count=1,maxStars=3))),
                ('Choose an opponent. They discard 1 random card; then you draw 1 card.', seq(st('discard_random','chosen_enemy',count=1),st('draw','self',count=1))),
                ('You and your teammate each get +10 damage on your next attack.', seq(st('buff_attack','team',amount=10))),
            ]
        elif profile == 'sport':
            table = [
                ('Deal 20 damage to one other player. Your next attack gets +10 damage.', seq(st('damage','chosen_other',amount=20),st('buff_attack','self',amount=10))),
                ('Give your teammate +20 damage on their next attack.', seq(st('buff_attack','ally',amount=20))),
                ('Draw 1 card and gain 15 armor.', seq(st('draw','self',count=1),st('armor','self',amount=15))),
                ('Your next attack deals ×1.25 damage.', seq(st('attack_multiplier','self',mult=1.25))),
                ('Deal 15 damage to both opponents.', seq(st('damage','enemies',amount=15))),
                ('Heal yourself or your teammate 30 HP and give them +10 on their next attack.', seq(st('heal','ally',amount=30),st('buff_attack','ally',amount=10))),
                ('Draw 2 cards, then discard 1 random card.', seq(st('draw','self',count=2),st('discard_random','self',count=1))),
                ('Reduce the next damage you take by 25.', seq(st('reduce_next','self',amount=25))),
                ('Your teammate may ignore the next punch that would damage them.', seq(st('punch_immunity','ally',charges=1))),
                ('You and your teammate each gain 15 armor.', seq(st('armor','team',amount=15))),
            ]
        elif profile == 'risk':
            table = [
                ('Take 10 damage, then deal 40 damage to one other player.', seq(st('damage','self',amount=10,attack=False),st('damage','chosen_other',amount=40))),
                ('Flip a coin: heads, your next attack deals ×1.5 damage; tails, take 25 damage.', {'type':'coin','heads':[st('attack_multiplier','self',mult=1.5)],'tails':[st('damage','self',amount=25,attack=False)]}),
                ('Deal 20 damage to every other living player.', seq(st('damage','all_others',amount=20))),
                ('Draw 3 cards, then discard 2 random cards from your hand.', seq(st('draw','self',count=3),st('discard_random','self',count=2))),
                ('Take 15 damage. Your next attack gets +35 damage.', seq(st('damage','self',amount=15,attack=False),st('buff_attack','self',amount=35))),
                ('Choose one other player. At the start of their next turn, deal 40 damage to them.', seq(st('delayed_damage','chosen_other',amount=40,turns=1))),
                ('Heal yourself 50 HP, then take 20 damage at the start of your next turn.', seq(st('heal','self',amount=50),st('delayed_damage','self',amount=20,turns=1,attack=False))),
                ('Deal 25 damage to one other player. Reduce the next damage you take by 10.', seq(st('damage','chosen_other',amount=25),st('reduce_next','self',amount=10))),
                ('Deal 30 damage to one other player. You discard 1 random card.', seq(st('damage','chosen_other',amount=30),st('discard_random','self',count=1))),
                ('Your next attack deals ×1.4 damage, but the next damage you take is increased by ×1.25.', seq(st('attack_multiplier','self',mult=1.4),st('next_damage_multiplier','self',mult=1.25))),
            ]
        elif profile == 'mystic':
            table = [
                ('Deal 25 damage to one other player and mark them for +10 on the next damage they take.', seq(st('damage','chosen_other',amount=25),st('mark','chosen_other',amount=10))),
                ('Reduce the next damage you or your teammate takes by 25.', seq(st('reduce_next','ally',amount=25))),
                ('Draw 2 cards, then discard 1 random card.', seq(st('draw','self',count=2),st('discard_random','self',count=1))),
                ('Choose one other player. At the start of their next turn, deal 35 damage to them.', seq(st('delayed_damage','chosen_other',amount=35,turns=1))),
                ('Your next attack deals ×1.25 damage and you gain 10 armor.', seq(st('attack_multiplier','self',mult=1.25),st('armor','self',amount=10))),
                ('Choose an opponent. They cannot heal until the start of their next turn.', seq(st('prevent_heal','chosen_enemy',turns=1))),
                ('Deal 15 damage to both opponents and draw 1 card.', seq(st('damage','enemies',amount=15),st('draw','self',count=1))),
                ('Until your next turn, you cannot be targeted by attacks.', seq(st('untargetable','self'))),
                ('Return one 3★ card from your discard pile to your hand.', seq(st('return_discard','self',count=1,stars=3))),
                ('Choose an opponent. Their next attack deals 15 less damage; your next attack gets +10.', seq(st('buff_attack','chosen_enemy',amount=-15),st('buff_attack','self',amount=10))),
            ]
        else: # tactical
            table = [
                ('Deal 25 damage to one other player and reduce the next damage you take by 10.', seq(st('damage','chosen_other',amount=25),st('reduce_next','self',amount=10))),
                ('Draw 1 card and give yourself or your teammate 15 armor.', seq(st('draw','self',count=1),st('armor','ally',amount=15))),
                ('Mark one other player. The next damage they take is increased by 20.', seq(st('mark','chosen_other',amount=20))),
                ('Choose an opponent. Their next attack deals 20 less damage.', seq(st('buff_attack','chosen_enemy',amount=-20))),
                ('Deal 20 damage to one other player, then draw 1 card.', seq(st('damage','chosen_other',amount=20),st('draw','self',count=1))),
                ('Heal yourself or your teammate 25 HP and give them 10 armor.', seq(st('heal','ally',amount=25),st('armor','ally',amount=10))),
                ('Reduce the next damage you or your teammate takes by 25.', seq(st('reduce_next','ally',amount=25))),
                ('Choose an opponent. They discard 1 random card.', seq(st('discard_random','chosen_enemy',count=1))),
                ('Choose one other player. At the start of their next turn, deal 30 damage to them.', seq(st('delayed_damage','chosen_other',amount=30,turns=1))),
                ('You and your teammate each get +10 damage on your next attack.', seq(st('buff_attack','team',amount=10))),
            ]
        return table[slot]

    if stars == 4:
        if profile == 'assault':
            table=[
                (f'Deal {dmg60} damage to one other player.', seq(st('damage','chosen_other',amount=dmg60))),
                ('Deal 35 damage to both opponents.', seq(st('damage','enemies',amount=35))),
                ('Deal 45 damage to one other player, then draw 1 card.', seq(st('damage','chosen_other',amount=45),st('draw','self',count=1))),
                ('Deal 40 damage to one other player. The next damage they take is increased by 20.', seq(st('damage','chosen_other',amount=40),st('mark','chosen_other',amount=20))),
                ('Take 15 damage, then deal 75 damage to one other player.', seq(st('damage','self',amount=15,attack=False),st('damage','chosen_other',amount=75))),
            ]
        elif profile == 'team':
            table=[
                ('Heal both members of your team 35 HP.', seq(st('heal','team',amount=35))),
                ('Give both members of your team 30 armor.', seq(st('armor','team',amount=30))),
                ('Heal yourself or your teammate 45 HP and give them 20 armor.', seq(st('heal','ally',amount=45),st('armor','ally',amount=20))),
                ('Give your teammate +35 damage on their next attack, then draw 1 card.', seq(st('buff_attack','ally',amount=35),st('draw','self',count=1))),
                ('You may play one additional non-5★ card this turn.', seq(st('extra_play','self',count=1,maxStars=4))),
            ]
        elif profile == 'control':
            table=[
                ('Choose an opponent. They skip their next turn.', seq(st('skip_turn','chosen_enemy',count=1))),
                ('Steal 1 random card from an opponent.', seq(st('steal_random','chosen_enemy',count=1))),
                ('Choose an opponent. They discard 2 random cards.', seq(st('discard_random','chosen_enemy',count=2))),
                ('Deal 45 damage to an opponent; they cannot heal until the start of their next turn.', seq(st('damage','chosen_enemy',amount=45),st('prevent_heal','chosen_enemy',turns=1))),
                ('Draw 2 cards, then you may play one additional non-5★ card this turn.', seq(st('draw','self',count=2),st('extra_play','self',count=1,maxStars=4))),
            ]
        elif profile == 'social':
            table=[
                ('Heal yourself or your teammate 70 HP.', seq(st('heal','ally',amount=70))),
                ('Heal both members of your team 35 HP.', seq(st('heal','team',amount=35))),
                ('Return up to 2 non-5★ cards from your discard pile to your hand.', seq(st('return_discard','self',count=2,maxStars=4))),
                ('You may play one additional non-5★ card this turn.', seq(st('extra_play','self',count=1,maxStars=4))),
                ('Heal yourself or your teammate 40 HP and give them 30 armor.', seq(st('heal','ally',amount=40),st('armor','ally',amount=30))),
            ]
        elif profile == 'tempo':
            table=[
                ('Draw 3 cards, then discard 1 random card. Your next attack gets +20 damage.', seq(st('draw','self',count=3),st('discard_random','self',count=1),st('buff_attack','self',amount=20))),
                ('Deal 45 damage to one other player, then draw 1 card.', seq(st('damage','chosen_other',amount=45),st('draw','self',count=1))),
                ('You may play one additional non-5★ card this turn, then draw 1 card.', seq(st('extra_play','self',count=1,maxStars=4),st('draw','self',count=1))),
                ('You and your teammate each get +25 damage on your next attack.', seq(st('buff_attack','team',amount=25))),
                ('Deal 30 damage to one other player, then you may punch once this turn.', seq(st('damage','chosen_other',amount=30),st('extra_punch','self'))),
            ]
        elif profile == 'sport':
            table=[
                ('Your next attack deals ×1.5 damage. Draw 1 card.', seq(st('attack_multiplier','self',mult=1.5),st('draw','self',count=1))),
                ('You and your teammate each get +30 damage on your next attack.', seq(st('buff_attack','team',amount=30))),
                ('Heal both members of your team 25 HP and give each 15 armor.', seq(st('heal','team',amount=25),st('armor','team',amount=15))),
                ('Deal 40 damage to one other player, then you may punch once this turn.', seq(st('damage','chosen_other',amount=40),st('extra_punch','self'))),
                ('Draw 2 cards and give your teammate +25 damage on their next attack.', seq(st('draw','self',count=2),st('buff_attack','ally',amount=25))),
            ]
        elif profile == 'risk':
            table=[
                ('Take 20 damage, then deal 80 damage to one other player.', seq(st('damage','self',amount=20,attack=False),st('damage','chosen_other',amount=80))),
                ('Flip a coin: heads, deal 75 damage to one other player; tails, take 35 damage and draw 2 cards.', {'type':'coin','heads':[st('damage','chosen_other',amount=75)],'tails':[st('damage','self',amount=35,attack=False),st('draw','self',count=2)]}),
                ('Deal 30 damage to every other living player.', seq(st('damage','all_others',amount=30))),
                ('Your next attack deals ×1.75 damage, but the next damage you take is increased by ×1.5.', seq(st('attack_multiplier','self',mult=1.75),st('next_damage_multiplier','self',mult=1.5))),
                ('Heal yourself 90 HP, then take 30 damage at the start of your next turn.', seq(st('heal','self',amount=90),st('delayed_damage','self',amount=30,turns=1,attack=False))),
            ]
        elif profile == 'mystic':
            table=[
                ('Deal 50 damage to one other player and mark them for +15 on the next damage they take.', seq(st('damage','chosen_other',amount=50),st('mark','chosen_other',amount=15))),
                ('Until your next turn, cap any single damage instance you take at 30.', seq(st('damage_cap','self',amount=30))),
                ('Choose an opponent. They skip their next turn.', seq(st('skip_turn','chosen_enemy',count=1))),
                ('Swap your HP with one other living player.', seq(st('swap_hp','chosen_other'))),
                ('Return up to 2 non-5★ cards from your discard pile to your hand.', seq(st('return_discard','self',count=2,maxStars=4))),
            ]
        else: # tactical
            table=[
                ('Deal 45 damage to one other player, then reduce the next damage you take by 20.', seq(st('damage','chosen_other',amount=45),st('reduce_next','self',amount=20))),
                ('Draw 2 cards and give yourself or your teammate 30 armor.', seq(st('draw','self',count=2),st('armor','ally',amount=30))),
                ('Choose an opponent. They discard 1 random card and their next attack deals 20 less damage.', seq(st('discard_random','chosen_enemy',count=1),st('buff_attack','chosen_enemy',amount=-20))),
                ('Heal your teammate 45 HP and give them +25 damage on their next attack.', seq(st('heal','ally',amount=45),st('buff_attack','ally',amount=25))),
                ('Deal 35 damage to both opponents.', seq(st('damage','enemies',amount=35))),
            ]
        return table[slot]

    # 5-star marquee effects. Strong special effects intentionally deviate from pure-stat 100/100/80 baselines.
    if stars == 5 and SHOW_NAMES_BY_INDEX[show_index] in FIVE_STAR_SPECIALS:
        return FIVE_STAR_SPECIALS[SHOW_NAMES_BY_INDEX[show_index]]
    if profile == 'assault':
        return ('Deal 100 damage to one other player. The next damage they take is increased by 20.', seq(st('damage','chosen_other',amount=100),st('mark','chosen_other',amount=20)))
    if profile == 'team':
        return ('Heal both members of your team 35 HP and give each 15 armor, then draw 1 card.', seq(st('heal','team',amount=35),st('armor','team',amount=15),st('draw','self',count=1)))
    if profile == 'control':
        return ('Choose an opponent. They skip their next turn; then draw 2 cards and steal 1 random card from them.', seq(st('skip_turn','chosen_enemy',count=1),st('draw','self',count=2),st('steal_random','chosen_enemy',count=1)))
    if profile == 'social':
        return ('Heal both members of your team 50 HP. Return one non-5★ card from your discard pile to your hand.', seq(st('heal','team',amount=50),st('return_discard','self',count=1,maxStars=4)))
    if profile == 'tempo':
        return ('Draw 3 cards. You may play one additional card this turn, and your next attack gets +25 damage.', seq(st('draw','self',count=3),st('extra_play','self',count=1,maxStars=5),st('buff_attack','self',amount=25)))
    if profile == 'sport':
        return ('You and your teammate each get ×1.5 damage on your next attack and draw 1 card.', seq(st('attack_multiplier','team',mult=1.5),st('draw','self',count=1)))
    if profile == 'risk':
        return ('Take 40 damage, then deal 140 damage to one other player.', seq(st('damage','self',amount=40,attack=False),st('damage','chosen_other',amount=140)))
    if profile == 'mystic':
        return ('Choose one other player and swap HP with them. Then you may play one additional non-5★ card this turn.', seq(st('swap_hp','chosen_other'),st('extra_play','self',count=1,maxStars=4)))
    return ('Deal 70 damage to one other player, draw 2 cards, and reduce the next damage you take by 20.', seq(st('damage','chosen_other',amount=70),st('draw','self',count=2),st('reduce_next','self',amount=20)))



def _action_ops(action):
    if not action: return []
    if action.get('type') == 'sequence': return [x.get('op') for x in action.get('steps',[])]
    if action.get('type') == 'coin':
        return [x.get('op') for x in action.get('heads',[])] + [x.get('op') for x in action.get('tails',[])]
    if action.get('type') == 'bundle': return _action_ops(action.get('main')) + [x.get('op') for x in action.get('after',[])]
    return [action.get('type')]

def signature_is_redundant(base_action, candidate_action):
    if not candidate_action or candidate_action.get('type') != 'bundle':
        return False
    after = candidate_action.get('after') or []
    if not after:
        return False
    added = after[-1].get('op')
    return added in set(_action_ops(base_action))

def add_signature_twist(effect, action, show, ref, stars, profile, attempt=0):
    """Give generated cards a mechanically distinct rider without tiny 3/7/12-point values.

    A small clean-10 bonus is paired with a mild cost on most cards. This preserves
    mechanical uniqueness while keeping the rarity baseline as the main power budget.
    """
    import hashlib
    h = int(hashlib.sha256(f'{show}|{ref}|{stars}|{attempt}|clean10'.encode()).hexdigest()[:16], 16)
    base_ops = set(_action_ops(action))
    high_impact = any(op in {'extra_play','skip_turn','steal_random','swap_hp'} for op in base_ops)

    bonus_amount = 10 if ((h >> 2) & 1) == 0 else 20
    cost_amount = 10 if ((h >> 3) & 1) == 0 else 20

    role_bonus = {
        'assault': [
            ('buff_attack','self', f'Afterward, your next attack gets +{{a}} damage.'),
            ('mark','chosen_other', f'Afterward, mark one other player for +{{a}} on the next damage they take.'),
            ('armor','self', f'Afterward, gain {{a}} armor.'),
            ('reduce_next','self', f'Afterward, reduce the next damage you take by {{a}}.'),
            ('buff_attack','chosen_enemy', f'Afterward, an opponent’s next attack deals {{a}} less damage.'),
            ('buff_attack','ally', f'Afterward, give your teammate +{{a}} damage on their next attack.'),
        ],
        'risk': [
            ('buff_attack','self', f'Afterward, your next attack gets +{{a}} damage.'),
            ('mark','chosen_other', f'Afterward, mark one other player for +{{a}} on the next damage they take.'),
            ('armor','self', f'Afterward, gain {{a}} armor.'),
            ('reduce_next','self', f'Afterward, reduce the next damage you take by {{a}}.'),
        ],
        'team': [
            ('heal','ally', f'Afterward, heal yourself or your teammate {{a}} HP.'),
            ('armor','ally', f'Afterward, give yourself or your teammate {{a}} armor.'),
            ('buff_attack','ally', f'Afterward, give your teammate +{{a}} damage on their next attack.'),
            ('reduce_next','ally', f'Afterward, reduce the next damage your teammate takes by {{a}}.'),
            ('buff_attack','team', f'Afterward, you and your teammate each get +{{a}} damage on your next attack.'),
        ],
        'social': [
            ('heal','ally', f'Afterward, heal yourself or your teammate {{a}} HP.'),
            ('armor','ally', f'Afterward, give yourself or your teammate {{a}} armor.'),
            ('buff_attack','ally', f'Afterward, give your teammate +{{a}} damage on their next attack.'),
            ('reduce_next','ally', f'Afterward, reduce the next damage your teammate takes by {{a}}.'),
        ],
        'tempo': [
            ('buff_attack','self', f'Afterward, your next attack gets +{{a}} damage.'),
            ('armor','self', f'Afterward, gain {{a}} armor.'),
            ('heal','self', f'Afterward, heal yourself {{a}} HP.'),
            ('mark','chosen_other', f'Afterward, mark one other player for +{{a}} on the next damage they take.'),
        ],
        'sport': [
            ('buff_attack','self', f'Afterward, your next attack gets +{{a}} damage.'),
            ('buff_attack','ally', f'Afterward, give your teammate +{{a}} damage on their next attack.'),
            ('armor','self', f'Afterward, gain {{a}} armor.'),
            ('reduce_next','self', f'Afterward, reduce the next damage you take by {{a}}.'),
        ],
        'control': [
            ('buff_attack','chosen_enemy', f'Afterward, an opponent’s next attack deals {{a}} less damage.'),
            ('mark','chosen_other', f'Afterward, mark one other player for +{{a}} on the next damage they take.'),
            ('reduce_next','self', f'Afterward, reduce the next damage you take by {{a}}.'),
            ('armor','self', f'Afterward, gain {{a}} armor.'),
        ],
        'mystic': [
            ('mark','chosen_other', f'Afterward, mark one other player for +{{a}} on the next damage they take.'),
            ('reduce_next','self', f'Afterward, reduce the next damage you take by {{a}}.'),
            ('buff_attack','self', f'Afterward, your next attack gets +{{a}} damage.'),
            ('armor','self', f'Afterward, gain {{a}} armor.'),
        ],
        'tactical': [
            ('armor','self', f'Afterward, gain {{a}} armor.'),
            ('reduce_next','self', f'Afterward, reduce the next damage you take by {{a}}.'),
            ('buff_attack','chosen_enemy', f'Afterward, an opponent’s next attack deals {{a}} less damage.'),
            ('armor','ally', f'Afterward, give yourself or your teammate {{a}} armor.'),
        ],
    }
    pool = role_bonus.get(profile, role_bonus['tactical'])
    # Cycle through role bonuses deterministically and avoid duplicating a main op when possible.
    ordered = [pool[((h // 17) + attempt + i) % len(pool)] for i in range(len(pool))]
    op, target, template = next((x for x in ordered if x[0] not in base_ops), ordered[0])
    bonus_step = st(op, target, amount=(-bonus_amount if op == 'buff_attack' and target == 'chosen_enemy' else bonus_amount))
    bonus_text = template.format(a=bonus_amount)

    costs = [
        (st('damage','self',amount=10,attack=False), 'Take 10 damage.'),
        (st('damage','self',amount=20,attack=False), 'Take 20 damage.'),
        (st('damage','self',amount=30,attack=False), 'Take 30 damage.'),
        (st('buff_attack','self',amount=-10), 'Your next attack deals 10 less damage.'),
        (st('buff_attack','self',amount=-20), 'Your next attack deals 20 less damage.'),
        (st('discard_random','self',count=1), 'Discard 1 random card from your hand.'),
        (st('discard_random','self',count=2), 'Discard 2 random cards from your hand.'),
        (st('heal','chosen_enemy',amount=10), 'Heal the chosen opponent 10 HP.'),
        (st('heal','chosen_enemy',amount=20), 'Heal the chosen opponent 20 HP.'),
        (st('armor','chosen_enemy',amount=10), 'Give the chosen opponent 10 armor.'),
        (st('armor','chosen_enemy',amount=20), 'Give the chosen opponent 20 armor.'),
        (st('buff_attack','chosen_enemy',amount=10), 'Give the chosen opponent +10 damage on their next attack.'),
        (st('buff_attack','chosen_enemy',amount=20), 'Give the chosen opponent +20 damage on their next attack.'),
    ]
    ci=((h // 97) + attempt) % len(costs)
    cj=((h // 193) + attempt*3 + 1) % len(costs)
    if cj == ci: cj=(cj+1) % len(costs)
    cost_step, cost_text = costs[ci]
    cost2_step, cost2_text = costs[cj]

    # High-impact action-economy/control effects pay two clean drawbacks. Normal cards get
    # one role-consistent bonus and one drawback so uniqueness does not come from tiny numbers.
    after = [cost_step, cost2_step] if high_impact else [bonus_step, cost_step]
    text = f'Then {cost_text[0].lower()+cost_text[1:]} Then {cost2_text[0].lower()+cost2_text[1:]}' if high_impact else f'{bonus_text} Then {cost_text[0].lower()+cost_text[1:]}'
    return effect.rstrip('.') + '. ' + text, {'type':'bundle','main':action,'after':after}


VARIANT_TITLES = {
    'assault': ['Pressure', 'Follow-Through', 'Breakthrough', 'Counteroffensive', 'Overdrive', 'Finisher', 'Decisive Strike', 'Final Push'],
    'team': ['Cover', 'Rally', 'Coordination', 'Backup Plan', 'Formation', 'Rescue', 'United Front', 'Last Stand'],
    'control': ['Read the Field', 'Calculated Trap', 'Lockdown', 'Counterplay', 'Checkmate', 'Interference', 'No Escape', 'Master Plan'],
    'social': ['Heart-to-Heart', 'Helping Hand', 'Promise', 'Trust', 'Reassurance', 'Together', 'Shared Resolve', 'Unbreakable Bond'],
    'tempo': ['Momentum', 'Encore', 'Second Beat', 'Quick Shift', 'Set the Pace', 'Acceleration', 'Showstopper', 'Finale'],
    'sport': ['Perfect Form', 'Second Wind', 'Closing Sprint', 'Training Payoff', 'Clutch Play', 'Peak Condition', 'Photo Finish', 'Champion Form'],
    'risk': ['Over the Limit', 'No Turning Back', 'Danger Zone', 'All In', 'Burnout', 'Desperation', 'Point of No Return', 'Last Gamble'],
    'mystic': ['Hidden Art', 'Arcane Turn', 'Forbidden Pattern', 'Resonance', 'Unseen Hand', 'Mystic Shift', 'Grand Invocation', 'Transcendence'],
    'tactical': ['Positioning', 'Prepared Response', 'Measured Strike', 'Contingency', 'Field Plan', 'Countermeasure', 'Perfect Setup', 'Grand Strategy'],
}


def alternate_five_effect(profile, show_index):
    """Second marquee option for each show using clean 10-point combat values."""
    if profile == 'assault':
        return ('Deal 60 damage to both opponents. Your next attack gets +20 damage.',
                seq(st('damage','enemies',amount=60), st('buff_attack','self',amount=20)))
    if profile == 'team':
        return ('Heal both members of your team 40 HP and give each 20 armor.',
                seq(st('heal','team',amount=40), st('armor','team',amount=20)))
    if profile == 'control':
        return ('Choose an opponent. They skip their next turn. Draw 1 card, then their next attack deals 20 less damage.',
                seq(st('skip_turn','chosen_enemy',count=1), st('draw','self',count=1), st('buff_attack','chosen_enemy',amount=-20)))
    if profile == 'social':
        return ('Heal yourself or your teammate 80 HP, give them 20 armor, then draw 1 card.',
                seq(st('heal','ally',amount=80), st('armor','ally',amount=20), st('draw','self',count=1)))
    if profile == 'tempo':
        return ('Draw 3 cards. You may play one additional non-5★ card this turn, then discard 1 random card.',
                seq(st('draw','self',count=3), st('extra_play','self',count=1,maxStars=4), st('discard_random','self',count=1)))
    if profile == 'sport':
        return ('You and your teammate each get ×1.4 damage on your next attack and 20 armor.',
                seq(st('attack_multiplier','team',mult=1.4), st('armor','team',amount=20)))
    if profile == 'risk':
        return ('Take 30 damage, then deal 120 damage to one other player. The next damage you take is increased by 25%.',
                seq(st('damage','self',amount=30,attack=False), st('damage','chosen_other',amount=120), st('next_damage_multiplier','self',mult=1.25)))
    if profile == 'mystic':
        return ('Deal 70 damage to one other player. Until your next turn, no single hit can deal more than 40 damage to you.',
                seq(st('damage','chosen_other',amount=70), st('damage_cap','self',amount=40)))
    return ('Deal 60 damage to one other player, give yourself or your teammate 40 armor, and reduce the next damage you take by 20.',
            seq(st('damage','chosen_other',amount=60), st('armor','ally',amount=40), st('reduce_next','self',amount=20)))


def add_variant_signature(effect, action, serial):
    """Clean-10 mechanically distinct rider for alternate pool cards."""
    bonus_ops = [
        ('armor','self'), ('heal','self'), ('reduce_next','self'), ('buff_attack','self'),
        ('mark','chosen_other'), ('armor','ally'), ('buff_attack','ally'), ('buff_attack','chosen_enemy'),
    ]
    def make_bonus(op,target,amount):
        actual=-amount if op=='buff_attack' and target=='chosen_enemy' else amount
        step=st(op,target,amount=actual)
        if op=='armor' and target=='self': text=f'gain {amount} armor'
        elif op=='heal': text=f'heal yourself {amount} HP'
        elif op=='reduce_next': text=f'reduce the next damage you take by {amount}'
        elif op=='buff_attack' and target=='self': text=f'your next attack gets +{amount} damage'
        elif op=='mark': text=f'mark one other player for +{amount} on the next damage they take'
        elif op=='armor' and target=='ally': text=f'give yourself or your teammate {amount} armor'
        elif op=='buff_attack' and target=='ally': text=f'give your teammate +{amount} damage on their next attack'
        else: text=f'an opponent’s next attack deals {amount} less damage'
        return step,text

    i=serial % len(bonus_ops)
    j=(serial // len(bonus_ops) + i + 1) % len(bonus_ops)
    if j==i: j=(j+1)%len(bonus_ops)
    amount1=10 if ((serial // 64) % 2 == 0) else 20
    amount2=10 if ((serial // 128) % 2 == 0) else 20
    b1,t1=make_bonus(*bonus_ops[i],amount1)
    b2,t2=make_bonus(*bonus_ops[j],amount2)

    cost_mode=(serial // 7) % 5
    if cost_mode==0:
        cost=st('damage','self',amount=10,attack=False); cost_text='take 10 damage'
    elif cost_mode==1:
        cost=st('damage','self',amount=20,attack=False); cost_text='take 20 damage'
    elif cost_mode==2:
        cost=st('buff_attack','self',amount=-10); cost_text='your next attack deals 10 less damage'
    elif cost_mode==3:
        cost=st('discard_random','self',count=1); cost_text='discard 1 random card from your hand'
    else:
        cost=st('heal','chosen_enemy',amount=10); cost_text='heal the chosen opponent 10 HP'
    return effect.rstrip('.') + f'. Afterward, {t1}; then {t2}; then {cost_text}.', {'type':'bundle','main':action,'after':[b1,b2,cost]}


legacy_clean = [clean_legacy(c) for c in legacy]
by_show = defaultdict(lambda: defaultdict(list))
for c in legacy_clean:
    by_show[c['show']][int(c['stars'])].append(c)

# Every show must exist even if the original 90-card list had no card for it (currently all do).
for show in SHOW_REFERENCES:
    _ = by_show[show]

out=[]; next_id=1
seen_generated_effects=set()
seen_generated_actions=set()
used_names=set()
show_names=sorted(SHOW_REFERENCES)
for show_index, show in enumerate(show_names):
    refs=SHOW_REFERENCES[show]
    profile=PROFILES[show]
    for star, target, candidates, base_slot in [
        (3,10,refs[:10],0), (4,5,refs[10:15],0), (5,1,refs[15:],0)
    ]:
        existing=by_show[show][star][:target]
        for c in existing:
            c=dict(c); c['id']=next_id; next_id+=1; out.append(c); used_names.add(c['name'].casefold())
        need=target-len(existing)
        added=0
        for local_slot, ref in enumerate(candidates):
            if added>=need: break
            name=ref
            # Avoid global collisions without losing the canon reference.
            if name.casefold() in used_names:
                name=f'{ref} — {show}'
            card_profile = reference_profile(show, ref, profile)
            # Pick a deterministic slot from the canon reference itself so cards within the same
            # show/profile do not all inherit the same positional template.
            themed_slot = themed_slot_for(show, ref, star, card_profile)
            effect, action=generated_effect(card_profile,star,themed_slot,show_index)
            effect, action=normalize_pair(effect, action)
            # 3★/4★ generated cards receive a small mechanically real signature twist so
            # no two generated cards are cloned templates. 5★ cards use hand-designed
            # show-specific marquee effects above.
            if star == 5 and show in FIVE_STAR_SPECIALS:
                peffect, paction = effect, action
                action_key = json.dumps(paction, sort_keys=True, ensure_ascii=False)
                # Keep the hand-designed marquee effect intact unless another generated card
                # happens to have the exact same executable action. In that rare case add one
                # small show-specific signature twist rather than allowing cloned abilities.
                attempt=0
                if peffect in seen_generated_effects or action_key in seen_generated_actions:
                    while True:
                        peffect, paction = add_signature_twist(effect, action, show, ref, star, card_profile, attempt)
                        action_key = json.dumps(paction, sort_keys=True, ensure_ascii=False)
                        if peffect not in seen_generated_effects and action_key not in seen_generated_actions:
                            break
                        attempt += 1
                        if attempt > 200:
                            raise RuntimeError(f'Unable to make unique 5-star twist for {show}: {ref}')
            else:
                attempt=0
                while True:
                    peffect, paction = add_signature_twist(effect, action, show, ref, star, card_profile, attempt)
                    action_key = json.dumps(paction, sort_keys=True, ensure_ascii=False)
                    if peffect not in seen_generated_effects and action_key not in seen_generated_actions: break
                    attempt += 1
                    if attempt > 200:
                        raise RuntimeError(f'Unable to make unique twist for {show}: {ref}; base={effect}')
            action_key = json.dumps(paction, sort_keys=True, ensure_ascii=False)
            if peffect in seen_generated_effects or action_key in seen_generated_actions:
                raise RuntimeError(f'Duplicate generated ability for {show}: {ref}')
            seen_generated_effects.add(peffect)
            seen_generated_actions.add(action_key)
            effect, action = peffect, paction
            out.append({
                'id':next_id,'name':name,'show':show,'origin':show,'stars':star,
                'effect':effect,'action':action,'generated':True,'canonRef':ref,'profile':card_profile,'showProfile':profile
            })
            next_id+=1; added+=1; used_names.add(name.casefold())
        if added != need:
            raise RuntimeError(f'Not enough canon candidates for {show} {star}★: need {need}, added {added}')

# Expand every show's card POOL beyond the 16 cards that actually go into a deck.
# Players still build with 10x 3★, 5x 4★, and 1x 5★ from each selected show, but now
# each show offers 15x 3★, 7x 4★, and 2x 5★ to choose from.
POOL_TARGETS = {3: 15, 4: 7, 5: 2}
for show_index, show in enumerate(show_names):
    refs = SHOW_REFERENCES[show]
    show_profile = PROFILES[show]
    # The extra pool cards lean into techniques/items/plot points instead of
    # just making five more character-name cards. The first 10 3★ slots still
    # give characters room to exist, while the optional slots are mostly show concepts.
    variant_specs = [
        *[(3, refs[10+i], i) for i in range(5)],
        (4, refs[15], 0),
        (4, refs[9], 1),
        (5, refs[14], 0),
    ]
    for star, ref, variant_index in variant_specs:
        card_profile = reference_profile(show, ref, show_profile)
        titles = VARIANT_TITLES.get(card_profile, VARIANT_TITLES['tactical'])
        title_index = (variant_index + (0 if star == 3 else 5 if star == 4 else 7)) % len(titles)
        name = f'{ref} — {titles[title_index]}'
        if name.casefold() in used_names:
            name = f'{name} — {show}'

        if star == 5:
            effect, action = alternate_five_effect(card_profile, show_index)
        else:
            # Hash a variant-only label so the alternate card does not simply reuse the base slot.
            themed_slot = themed_slot_for(show, f'{ref} | alternate {variant_index+1}', star, card_profile)
            effect, action = generated_effect(card_profile, star, themed_slot, show_index)
        effect, action = normalize_pair(effect, action)

        variant_serial = show_index * 8 + (variant_index if star == 3 else 5 + variant_index if star == 4 else 7)
        peffect, paction = add_variant_signature(effect, action, variant_serial)
        action_key = json.dumps(paction, sort_keys=True, ensure_ascii=False)
        if peffect in seen_generated_effects or action_key in seen_generated_actions:
            raise RuntimeError(f'Duplicate alternate ability for {show}: {ref}')

        seen_generated_effects.add(peffect)
        seen_generated_actions.add(action_key)
        out.append({
            'id': next_id, 'name': name, 'show': show, 'origin': show, 'stars': star,
            'effect': peffect, 'action': paction, 'generated': True, 'variant': True,
            'canonRef': ref, 'profile': card_profile, 'showProfile': show_profile,
        })
        next_id += 1
        used_names.add(name.casefold())

# Rarity audit for effects whose utility is much stronger than their raw numbers imply.
# Preserve each show's 15/7/2 pool by pairing every promotion with a tuned demotion.
def _find_card(show, name):
    for card in out:
        if card['show'] == show and card['name'].casefold() == name.casefold():
            return card
    raise RuntimeError(f'Card not found for rebalance: {show} / {name}')

def _set_card(show, name, stars=None, effect=None, action=None):
    c=_find_card(show,name)
    if stars is not None: c['stars']=stars
    if effect is not None: c['effect']=effect
    if action is not None: c['action']=action
    if effect is not None or action is not None:
        c['effect'], c['action'] = normalize_pair(c['effect'], c.get('action'))
    return c

# HP swapping is a 5★-level effect because it can create enormous life swings independent of damage baselines.
_set_card('Jujutsu Kaisen','Boogie woogie',stars=5)
_set_card('Jujutsu Kaisen','Malevolent Shrine — Final Push',stars=4,
          effect='Deal 30 damage to both opponents. Your next attack gets +10 damage.',
          action=seq(st('damage','enemies',amount=30),st('buff_attack','self',amount=10)))

_set_card('Dandadan','Evil Eye',stars=5)
_set_card('Dandadan','Occult Family',stars=4,
          effect='Heal both members of your team 30 HP.', action=seq(st('heal','team',amount=30)))

_set_card('Darling in the Franxx','Klaxosaur Princess',stars=5)
_set_card('Darling in the Franxx','The Beast and the Prince',stars=4,
          effect='You and your teammate each get +20 damage on your next attack and gain 10 armor.',
          action=seq(st('buff_attack','team',amount=20),st('armor','team',amount=10)))

_set_card('Frieren','Serie',stars=5)
_set_card('Frieren',"Himmel's Statue — Grand Strategy",stars=4,
          effect='Deal 40 damage to one other player, give yourself or your teammate 20 armor, and reduce the next damage you take by 10.',
          action=seq(st('damage','chosen_other',amount=40),st('armor','ally',amount=20),st('reduce_next','self',amount=10)))

# Sandevistan combines a full skipped turn with an extra punch, so it is also 5★ utility.
_set_card('Cyberpunk: Edgerunners','Sandevistan',stars=5)
_set_card('Cyberpunk: Edgerunners','Edgerunners',stars=4,
          effect='Take 20 damage, then deal 90 damage to one other player.',
          action=seq(st('damage','self',amount=20,attack=False),st('damage','chosen_other',amount=90)))


# Extra hand-tuned balance changes after playtesting the action economy.
# Quintessential is effectively a 5★ because the card itself is free action economy and
# can turn one turn into two additional non-5★ cards.
_set_card('The Quintessential Quintuplets','Quintessential quintuplets',stars=5,
          effect='This card does not count as your normal card play. You may play 2 additional non-5★ cards this turn.')
for _c in out:
    if (_c['show']=='The Quintessential Quintuplets' and _c.get('generated') and
        _c.get('canonRef')=='Wedding Day' and int(_c['stars'])==5):
        _c['stars']=4
        _c['effect']='Heal yourself or your teammate 60 HP and give that player 20 armor.'
        _c['action']=seq(st('heal','ally',amount=60),st('armor','ally',amount=20))
        break

# Kazuya stays a joke card, but no longer bricks an entire draw.
_set_card('Rent-a-Girlfriend','Kazuya',
          effect='This card does basically nothing. Draw 1 card because the deck feels bad for you.',
          action=seq(st('draw','self',count=1)))

# Two 4★ cards and a same-turn combo should have a payoff worth actually building around.
_set_card('Dandadan','Golden ball 1',effect='Does nothing by itself. Play Golden ball 2 this turn to heal 70 HP to either teammate and gain ×1.5 damage for 2 turns.')
_set_card('Dandadan','Golden ball 2',effect='Does nothing by itself. Play Golden ball 1 this turn to heal 70 HP to either teammate and gain ×1.5 damage for 2 turns.')

# The website cannot currently choose an exact hidden card from an opponent's hand, so Geass
# gets a strong, deterministic-to-resolve version rather than pretending the UI can do that.
_set_card('Code Geass','Geass',
          effect='Steal 2 random cards from one opponent’s hand.',
          action=seq(st('steal_random','chosen_enemy',count=2)))

# --- Broader balance audit -------------------------------------------------
# The original generated pool had some cards whose drawbacks stacked so hard that a 3★
# could be worth almost nothing, and a few 5★ utility cards were far below the 5★ budget.
# This lightweight score is not the game rule; it is only a sanity check used while building
# the pool. It values multi-target effects more in 2v2, and values card/turn economy separately.
def _target_factor(target):
    return {
        'self':1.0, 'ally':1.0, 'chosen_other':1.0, 'chosen_enemy':1.0,
        'team':1.6, 'enemies':1.6, 'all_others':2.1,
    }.get(target,1.0)

def _step_power(step):
    op=step.get('op'); target=step.get('target','self'); f=_target_factor(target)
    amount=float(step.get('amount',0) or 0)
    if op=='damage':
        return -amount if target=='self' else amount*f
    if op=='heal':
        return (-0.75*amount if target=='chosen_enemy' else 0.75*amount*f)
    if op=='armor':
        return (-0.70*amount if target=='chosen_enemy' else 0.70*amount*f)
    if op=='reduce_next': return 0.65*amount*f
    if op=='buff_attack':
        value=0.75*amount*f
        return -value if target=='chosen_enemy' else value
    if op=='mark': return 0.75*amount*f
    if op=='draw': return 22*(int(step.get('count',1) or 1))
    if op=='discard_random':
        value=20*(int(step.get('count',1) or 1))*f
        return -value if target=='self' else value
    if op=='discard_star': return -18*(int(step.get('count',1) or 1))
    if op=='delayed_damage': return 0.80*amount*f
    if op=='extra_play': return 45*(int(step.get('count',1) or 1))
    if op=='return_discard': return 18*(int(step.get('count',1) or 1))
    if op=='attack_multiplier': return 45*(float(step.get('mult',1))-1)*f
    if op=='prevent_heal': return 22*f
    if op=='skip_turn': return 65*(int(step.get('count',1) or 1))*f
    if op=='untargetable': return 40*f
    if op=='next_damage_multiplier': return 30*(1-float(step.get('mult',1)))*f
    if op=='extra_punch': return 20
    if op=='steal_random': return 42*(int(step.get('count',1) or 1))*f
    if op=='punch_immunity': return 16*(int(step.get('charges',1) or 1))*f
    if op=='force_self_punch': return 42*f
    if op=='damage_cap': return 42*f
    if op=='swap_hp': return 110
    if op=='bonus_draw': return 22*(int(step.get('count',1) or 1))
    return 0

def _action_power(action):
    if not action: return 0
    if isinstance(action,list): return sum(_action_power(x) for x in action)
    if not isinstance(action,dict): return 0
    typ=action.get('type')
    if typ=='sequence': return sum(_step_power(x) for x in action.get('steps',[]))
    if typ=='bundle': return _action_power(action.get('main')) + sum(_step_power(x) for x in action.get('after',[]))
    if typ=='coin': return 0.5*_action_power(action.get('heads',[])) + 0.5*_action_power(action.get('tails',[]))
    # Old direct action shapes are mostly legacy, but scoring them makes the audit readable.
    if typ=='damage': return float(action.get('amount',0) or 0)
    if typ=='split_enemies': return float(action.get('amount',0) or 0)*1.6
    if typ=='heal': return float(action.get('amount',0) or 0)*0.75
    if typ=='armor': return float(action.get('amount',0) or 0)*0.70
    if typ=='discard_draw': return -18 + 22*int(action.get('draw',2) or 2)
    if typ=='discard_star_draw': return -18 + 22*int(action.get('draw',2) or 2)
    return 0

def _append_step(card, step, sentence):
    action=card.get('action')
    if not action:
        card['action']=seq(step)
    elif action.get('type')=='bundle':
        action.setdefault('after',[]).append(step)
    elif action.get('type')=='sequence':
        action.setdefault('steps',[]).append(step)
    else:
        card['action']={'type':'bundle','main':action,'after':[step]}
    card['effect']=card['effect'].rstrip('.') + '. ' + sentence.rstrip('.') + '.'
    card['balancePatched']=True

# Minimum/maximum sanity bands. These intentionally overlap the PDF baselines instead of
# forcing every card to be a pure-stat clone. Cards with setup/risk can sit near an edge.
_POWER_BANDS={3:(20,55),4:(45,95),5:(80,145)}
for c in out:
    if not c.get('generated') or not c.get('action'): continue
    lo,hi=_POWER_BANDS[int(c['stars'])]
    power=_action_power(c['action'])

    # If a card is genuinely below its rarity floor, add one meaningful rider sized to the
    # actual deficit. This preserves the card's unique core ability without stacking a pile of
    # tiny +10 fixes.
    if power < lo:
        deficit=lo-power
        profile=c.get('profile','tactical')
        if profile in ('assault','risk','sport'):
            amount=max(20,min(100,int(((deficit/0.75)+9)//10*10)))
            _append_step(c,st('buff_attack','self',amount=amount),f'Your next attack also gets +{amount} damage')
        elif profile in ('team','social'):
            amount=max(30,min(100,int(((deficit/0.70)+9)//10*10)))
            _append_step(c,st('armor','ally',amount=amount),f'Also give yourself or your teammate {amount} armor')
        elif profile=='control':
            amount=max(20,min(100,int(((deficit/0.75)+9)//10*10)))
            _append_step(c,st('buff_attack','chosen_enemy',amount=-amount),f'Also make an opponent’s next attack deal {amount} less damage')
        elif profile=='tempo':
            _append_step(c,st('draw','self',count=1),'Also draw 1 card')
            power=_action_power(c['action'])
            if power < lo:
                amount=max(20,min(80,int((((lo-power)/0.70)+9)//10*10)))
                _append_step(c,st('armor','self',amount=amount),f'Also gain {amount} armor')
        elif profile=='mystic':
            amount=max(20,min(100,int(((deficit/0.75)+9)//10*10)))
            _append_step(c,st('mark','chosen_other',amount=amount),f'Also mark one other player for +{amount} on the next damage they take')
        else:
            amount=max(30,min(100,int(((deficit/0.65)+9)//10*10)))
            _append_step(c,st('reduce_next','self',amount=amount),f'Also reduce the next damage you take by {amount}')
        power=_action_power(c['action'])

    # If future generator edits make a generated card cross the ceiling, make the drawback
    # explicit rather than silently shaving numbers off the fun part of the card.
    if power > hi:
        excess=power-hi
        if int(c['stars'])<5:
            amount=max(20,min(60,int((excess+9)//10*10)))
            _append_step(c,st('damage','self',amount=amount,attack=False),f'Then take {amount} damage')
        else:
            _append_step(c,st('discard_random','self',count=1),'Then discard 1 random card from your hand')

# Targeted legacy fixes where the effect itself was mismatched to its rarity or to the 300 HP rules.
_set_card('86 Eighty-Six','Para-RAID',effect='Give yourself or your teammate +30 damage on their next attack.',
          action=seq(st('buff_attack','ally',amount=30)))
_set_card('Akame ga Kill!','Murasame',effect='Mark one other player. The next damage they take is increased by 30.',
          action=seq(st('mark','chosen_other',amount=30)))
_set_card('Fullmetal Alchemist: Brotherhood','Equivalent Exchange',
          effect='Discard one 3★ card from your hand, draw 3 cards, then you may play one additional 3★ card this turn.',
          action=seq(st('discard_star','self',stars=3,count=1),st('draw','self',count=3),st('extra_play','self',count=1,maxStars=3)))
_set_card('Solo Leveling','Arise',effect='Return up to 2 non-5★ cards from your discard pile to your hand.',
          action=seq(st('return_discard','self',count=2,maxStars=4)))
_set_card('Yu-Gi-Oh!','Pot of Greed',stars=4,effect='Draw two 3★ cards from your deck.')
_set_card('Yu-Gi-Oh!','Monster Reborn',stars=3,
          effect='Your next attack deals ×1.75 damage, but the next damage you take is ×1.5. Your next attack also gets +10 damage, and an opponent gets +10 on their next attack.',
          action=seq(st('attack_multiplier','self',mult=1.75),st('next_damage_multiplier','self',mult=1.5),st('buff_attack','self',amount=10),st('buff_attack','chosen_enemy',amount=10)))
_set_card('My Hero Academia','You’re Next',effect='You and your teammate each get +30 damage on your next attack.')
_set_card('Uma Musume','The Gray Monster',effect='You and your teammate each get ×1.25 damage on your next attack. If you are below 30 HP, use ×1.5 instead. This cannot boost a 5★ card.')
_set_card('SPY x FAMILY','Bond Forger',effect='See the abilities of your opponents’ cards for the rest of the game, then draw 2 cards. You still cannot tell your teammate without taking the Tonitrus Bolt penalty.')
_set_card('Overlord','World item',effect='Until your next turn, ignore non-5★ status effects and multipliers targeting you, and gain 20 armor.')
_set_card('Lord of Mysteries','The Place Above the Grey Fog',effect='Draw 3 cards, then you may play one additional non-5★ card this turn.')
_set_card('Fullmetal Alchemist: Brotherhood','The Father',effect='Return up to 2 non-5★ cards from your discard pile to your hand, then you may play one additional non-5★ card this turn.')
_set_card('Re:Zero','Return by Death',effect='The next time you or your teammate dies, revive that player at 80 HP. In 1v1, this protects you.')
_set_card('Jujutsu Kaisen','Infinity',effect='Take no damage from the next 2 standard damage attacks that hit you.')
_set_card("JoJo's Bizarre Adventure",'The World',effect='Both opponents skip their next turn. Then take 40 damage.')
_set_card('Vivy: Fluorite Eye’s Song','Flourite Eye’s Song',effect='Draw 1 card. Your next attack deals ×1.5 damage, and you may play one additional non-5★ card this turn.')
_set_card('Witch Hat Atelier','Piss Dragon',effect='Deal 30 damage to both opponents. Until your next turn, your team cannot take more than 50 damage from any single attack.')

# -----------------------------------------------------------------------------
# Card-name polish + team Field/Terrain system
# -----------------------------------------------------------------------------
# Generated cards should read like actual card titles, not a spreadsheet full of
# character names. Character-based references get a fanmade action/plot-style
# title while techniques, locations, items, and events keep the canon reference
# as the core of the title. canonRef remains untouched for traceability.
TITLE_PHRASES = {
    'assault': ['Full-Force Attack','No Holding Back','Counterattack','Point-Blank','Finishing Blow','Last Rush','Break the Line','All-In Assault'],
    'team': ['Hold the Line','Covering Fire','Rally the Team','Back-to-Back','Rescue Mission','Perfect Assist','Stand Together','Last Stand'],
    'control': ['Trap Is Set','No Escape','Forced Move','Checkmate','Read the Field','False Opening','Cornered','Plan Within a Plan'],
    'social': ['Promise Kept','Heart-to-Heart','Trust Fall','One More Chance','Shared Resolve','Say It Out Loud','Together Again','The Big Moment'],
    'tempo': ['Encore','Quick Shift','Second Beat','Steal the Tempo','Keep It Going','Sudden Turn','One More Move','Finale'],
    'sport': ['Perfect Form','Closing Sprint','Clutch Play','Second Wind','Training Pays Off','Photo Finish','Peak Condition','Championship Point'],
    'risk': ['All In','Over the Limit','No Turning Back','Danger Zone','Burn It All','Desperate Bet','Point of No Return','One Last Shot'],
    'mystic': ['Hidden Art','Forbidden Pattern','Resonance','Grand Invocation','Unseen Hand','Arcane Turn','Reality Break','Transcendence'],
    'tactical': ['Perfect Setup','Countermeasure','Contingency','Read the Situation','Field Plan','Prepared Response','Calculated Risk','Grand Strategy'],
}

def _reference_index(show, ref):
    try: return SHOW_REFERENCES[show].index(ref)
    except ValueError: return 99

CONCEPT_WORDS = (
    'attack','art','battle','ball','blade','castle','club','contract','curse','devil','domain',
    'exam','faction','festival','field','finals','gear','guild','house','island','jutsu','labyrinth',
    'league','live','magic','mode','moon','palace','project','room','school','shrine','spear','sword',
    'system','titan','tournament','tower','warehouse','world','academy','farm','planetarium','float',
    'shield','stone','song','rosario','stream','flash','note','requiem','rumbling','speech','technique','catch','reaper','fool','truth',
    'tail','transformation','memory','machine','festival','family','stryx','strix','star','bolt','garden',
)

def _title_for_generated(card, serial):
    ref=card.get('canonRef') or card['name']
    low=ref.casefold()
    phrases=TITLE_PHRASES.get(card.get('profile'), TITLE_PHRASES['tactical'])
    phrase=phrases[serial % len(phrases)]
    looks_like_concept = any(re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)', low) for word in CONCEPT_WORDS)
    # Plain character/creature references put the move/scene first so the card
    # reads like a TCG card title instead of a character roster entry.
    if not looks_like_concept:
        return f'{phrase} — {ref}'
    # Techniques / items / plot points / places can stand on their own. Alternate
    # versions add a subtitle so each card is still easy to distinguish.
    if card.get('variant'):
        return f'{ref}: {phrase}'
    return ref

# Environments are deliberately common. Each show gets SIX Environment cards in its
# 24-card pool (six 3★), so a legal three-show deck has plenty of
# opportunities to fight over the board. The deck builder requires at least three
# Environments from each selected show (9 total in a 48-card deck), but players may
# include more. Only ONE Environment exists on the board globally; a new one replaces
# the old one, even if the other team played it. Effects are intentionally modest.
FIELD_HINTS = (
    'academy','school','room','house','castle','palace','farm','tomb','island','league',
    'festival','planetarium','float','moon','labyrinth','field','kingdom','village','city',
    'tower','forest','garden','battlefront','underground','nazarick','aincrad','rear palace',
    'ente isla','tracen','vinland','san magnolia','giad federacy','starry','world line',
    'guild','headquarters','warehouse','metal float','tournament','the farm','the moon',
    'shrine','rumbling','requiem','domain','promised day','singularity','zero requiem','culture festival',
)

FIELD_REF_OVERRIDES = {
    'Digimon':['DigiDestined','Digital World'],
    'Fate/stay night':['Gate of Babylon','Unlimited Blade Works'],
    'Frieren':['First-Class Mage Exam','Aureole'],
    'My Hero Academia':['Class 1-A','U.A. High School'],
    'One-Punch Man':['Hero Association','Monster Association'],
    'Oshi no Ko':['Tokyo Blade','B-Komachi'],
    'Re:Zero':['Unseen Hand','Roswaal Mansion'],
    'Rent-a-Girlfriend':['Movie Premiere','Rental Date'],
    'Tokyo Ghoul':['Anteiku','20th Ward'],
    'Violet Evergarden':['Fifty Letters','CH Postal Company'],
    'Yu-Gi-Oh!':['Duel Disk','Shadow Game'],
    "Miss Kobayashi's Dragon Maid":['Chaos Faction','Kobayashi Apartment'],
    'Demon Slayer':['Upper Moons','Infinity Castle'],
    'Darling in the Franxx':['The Beast and the Prince','Plantation 13'],
}
FIELD_TITLE_OVERRIDES = {
    ('You and I Are Polar Opposites','Culture Festival'):'Polar Opposites Culture Festival',
}

def _field_refs(show, count=6):
    refs=[]
    for ref in FIELD_REF_OVERRIDES.get(show,[]):
        if ref in SHOW_REFERENCES[show] and ref not in refs: refs.append(ref)
    scored=[]
    for i,ref in enumerate(SHOW_REFERENCES[show]):
        if ref in refs: continue
        low=ref.casefold()
        score=(7 if any(k in low for k in FIELD_HINTS) else 0) + (3 if i>=10 else 0)
        scored.append((score,i,ref))
    scored.sort(key=lambda x:(x[0],x[1]), reverse=True)
    refs.extend(ref for _,_,ref in scored if ref not in refs)
    return refs[:count]

# Weak persistent effects. They last until either team plays another Environment.

RESERVED_ENV_REFS = {
    ('Frieren','Mimic Chest'), ('Bocchi the Rock!','Kessoku Band'), ('SPY x FAMILY','Operation Strix'),
    ('One-Punch Man','King'), ('Overlord','Grasp Heart'), ('Sword Art Online','Dual Blades'),
    ('Pokémon','Brock'), ('Jujutsu Kaisen','Satoru Gojo'), ('Chainsaw Man','Kobeni Higashiyama'),
    ('Fullmetal Alchemist: Brotherhood','Roy Mustang'), ('Naruto','Naruto Uzumaki'),
    ('Puella Magi Madoka Magica',"Homura's Shield"), ('My Hero Academia','Izuku Midoriya'),
    ("JoJo's Bizarre Adventure",'Star Platinum'), ('Re:Zero','Subaru Natsuki'),
    ('Kaguya-sama: Love Is War','Love Detective Chika'),
}

FIELD_KINDS = [
    ('attack',10,'Your team’s attacks deal +10 damage.'),
    ('guard',10,'Attacks against your team deal 10 less damage.'),
    ('heal',10,'At the start of each allied turn, that player heals 10 HP.'),
    ('armor',10,'At the start of each allied turn, that player gains 10 armor.'),
    ('punch',10,'Your team’s punches deal +10 damage.'),
]

for show_index,show in enumerate(show_names):
    threes=[c for c in out if c['show']==show and c.get('generated') and int(c['stars'])==3]
    # Keep Environments at 3★: their strength comes from persisting until replaced,
    # not from a large one-turn stat swing.
    env_candidates=[c for c in threes if (show,c.get('canonRef')) not in RESERVED_ENV_REFS]
    targets=env_candidates[-6:]
    if len(targets) < 6:
        raise RuntimeError(f'Not enough generated cards to make environments for {show}')
    refs=_field_refs(show,6)
    for j,(env_card,ref) in enumerate(zip(targets,refs)):
        kind,amount,rule=FIELD_KINDS[(show_index+j) % len(FIELD_KINDS)]
        env_card['canonRef']=ref
        env_card['cardType']='environment'
        title=FIELD_TITLE_OVERRIDES.get((show,ref), ref)
        env_card['name']=f'Environment: {title}'
        env_card['effect']=f'Set {title} as the Environment. {rule} Playing another Environment replaces it.'
        env_card['action']={
            'type':'terrain','terrainKind':kind,'amount':amount,
            'terrainKey':f'{show}::{ref}'
        }
        env_card['profile']='tactical'

# Rename the rest of the generated pool after terrain assignment.
used_final=set(c['name'].casefold() for c in out if not c.get('generated'))
for serial,c in enumerate([x for x in out if x.get('generated')]):
    if c.get('cardType') in ('field','environment'):
        proposed=c['name']
    else:
        proposed=_title_for_generated(c,serial)
    attempt=1
    while proposed.casefold() in used_final:
        # Try another action/plot title rather than putting an ugly "2" after the name.
        proposed=_title_for_generated(c,serial + attempt)
        attempt+=1
        if attempt>32:
            proposed=f"{c.get('canonRef', c['name'])}: Another Route {attempt}"
            break
    c['name']=proposed
    used_final.add(proposed.casefold())


# A small number of intentionally meme-y cards. These are still mechanically balanced;
# the joke is in the title/flavor, not in making them unusable or auto-win buttons.
def _generated_ref(show, ref, stars):
    matches=[c for c in out if c.get('generated') and c['show']==show and c.get('canonRef')==ref and int(c['stars'])==stars and c.get('cardType') not in ('field','environment')]
    if not matches:
        raise RuntimeError(f'Meme target not found: {show} / {ref} / {stars}★')
    return matches[-1]

def _meme(show, ref, stars, name, effect, action):
    c=_generated_ref(show,ref,stars)
    c['name']=name; c['effect']=effect; c['action']=action; c['meme']=True

_meme('Frieren','Mimic Chest',3,'99% Chance It Is a Mimic',
      'Flip a coin. Heads: draw 2 cards. Tails: take 20 damage and draw 1 card.',
      {'type':'coin','heads':[st('draw','self',count=2)],'tails':[st('damage','self',amount=20,attack=False),st('draw','self',count=1)]})
_meme('Bocchi the Rock!','Kessoku Band',3,'Bocchi.exe Has Stopped Responding',
      'Until your next turn, you cannot be targeted. Then discard 1 random card.',
      seq(st('untargetable','self'),st('discard_random','self',count=1)))
_meme('SPY x FAMILY','Operation Strix',3,'Heh.',
      'Draw 2 cards, then discard 1 random card.',
      seq(st('draw','self',count=2),st('discard_random','self',count=1)))
_meme('One-Punch Man','King',3,'King Engine (Definitely Real)',
      'Gain 40 armor. Your next attack deals 10 less damage.',
      seq(st('armor','self',amount=40),st('buff_attack','self',amount=-10)))
_meme('Overlord','Grasp Heart',3,'Sasuga Ainz-sama',
      'Give yourself or your teammate +20 damage on their next attack and 20 armor.',
      seq(st('buff_attack','ally',amount=20),st('armor','ally',amount=20)))
_meme('Sword Art Online','Dual Blades',3,'Kirito Is Definitely Not Hacking',
      'Draw 1 card and get +20 damage on your next attack. Then take 10 damage.',
      seq(st('draw','self',count=1),st('buff_attack','self',amount=20),st('damage','self',amount=10,attack=False)))
_meme('Pokémon','Brock',3,'Jelly-Filled Donuts',
      'Heal yourself or your teammate 40 HP.',
      seq(st('heal','ally',amount=40)))
_meme('Jujutsu Kaisen','Satoru Gojo',4,"Nah, I'd Win",
      'Gain 50 armor and +20 damage on your next attack.',
      seq(st('armor','self',amount=50),st('buff_attack','self',amount=20)))
_meme('Chainsaw Man','Kobeni Higashiyama',3,"Kobeni's Car",
      'Deal 40 damage to one other player, then take 20 damage.',
      seq(st('damage','chosen_other',amount=40),st('damage','self',amount=20,attack=False)))
_meme('Fullmetal Alchemist: Brotherhood','Roy Mustang',3,"It's a Terrible Day for Rain",
      'Heal yourself or your teammate 20 HP and reduce their next incoming damage by 20.',
      seq(st('heal','ally',amount=20),st('reduce_next','ally',amount=20)))
_meme('Naruto','Naruto Uzumaki',3,'Talk no Jutsu',
      'Make one opponent’s next attack deal 30 less damage, then draw 1 card.',
      seq(st('buff_attack','chosen_enemy',amount=-30),st('draw','self',count=1)))
_meme('Puella Magi Madoka Magica',"Homura's Shield",3,'Being Meguca Is Suffering',
      'Draw 2 cards, then take 20 damage.',
      seq(st('draw','self',count=2),st('damage','self',amount=20,attack=False)))
_meme('My Hero Academia','Izuku Midoriya',3,'Deku Broke His Arms Again',
      'Take 20 damage, then deal 50 damage to one other player.',
      seq(st('damage','self',amount=20,attack=False),st('damage','chosen_other',amount=50)))
_meme("JoJo's Bizarre Adventure",'Star Platinum',3,'To Be Continued...',
      'Choose one other player. At the start of their next turn, deal 40 damage to them. Gain 10 armor.',
      seq(st('delayed_damage','chosen_other',amount=40,turns=1),st('armor','self',amount=10)))
_meme('Re:Zero','Subaru Natsuki',3,'I Love Emilia',
      'Heal yourself or your teammate 40 HP, draw 1 card, then discard 1 random card.',
      seq(st('heal','ally',amount=40),st('draw','self',count=1),st('discard_random','self',count=1)))
_meme('Kaguya-sama: Love Is War','Love Detective Chika',3,'O Kawaii Koto',
      'Make one opponent’s next attack deal 30 less damage and heal yourself 10 HP.',
      seq(st('buff_attack','chosen_enemy',amount=-30),st('heal','self',amount=10)))


# Simplify generated 3★/4★ abilities. Earlier versions kept every balancing rider used
# during generation, which made some cards read like five unrelated clauses. Keep the
# interesting core and at most two riders, remove "help the opponent" compensation, and
# bring the result back inside the rarity power band.
def _flat_steps(action):
    if not isinstance(action,dict): return []
    if action.get('type')=='sequence': return [dict(x) for x in action.get('steps',[])]
    if action.get('type')=='bundle': return _flat_steps(action.get('main')) + [dict(x) for x in action.get('after',[])]
    return []

def _bad_comp(step):
    op=step.get('op'); target=step.get('target')
    if target=='chosen_enemy' and op in ('heal','armor'): return True
    if target=='chosen_enemy' and op=='buff_attack' and float(step.get('amount',0) or 0)>0: return True
    if target=='self' and op=='buff_attack' and float(step.get('amount',0) or 0)<0: return True
    return False

def _increase_positive(steps, need):
    # Increase one normal flat positive effect in clean 10-point chunks.
    for op in ('damage','heal','armor','reduce_next','buff_attack','mark','delayed_damage'):
        for step in steps:
            if step.get('op')!=op: continue
            if op=='damage' and step.get('target')=='self': continue
            if op=='buff_attack' and float(step.get('amount',0) or 0)<=0: continue
            cur=int(step.get('amount',0) or 0)
            add=max(10,min(50,int(((need+9)//10)*10)))
            step['amount']=cur+add
            return True
    return False

def _rider_for(profile, serial, strength=20):
    amount=max(10,int(round(strength/10))*10)
    options={
      'assault':[st('buff_attack','self',amount=amount),st('mark','chosen_other',amount=amount),st('armor','self',amount=amount)],
      'risk':[st('buff_attack','self',amount=amount),st('damage','self',amount=max(10,amount-10),attack=False),st('mark','chosen_other',amount=amount)],
      'team':[st('armor','ally',amount=amount),st('heal','ally',amount=amount),st('buff_attack','ally',amount=amount)],
      'social':[st('heal','ally',amount=amount),st('armor','ally',amount=amount),st('draw','self',count=1)],
      'control':[st('buff_attack','chosen_enemy',amount=-amount),st('discard_random','chosen_enemy',count=1),st('prevent_heal','chosen_enemy',turns=1)],
      'tempo':[st('draw','self',count=1),st('buff_attack','self',amount=amount),st('armor','self',amount=amount)],
      'sport':[st('buff_attack','self',amount=amount),st('armor','self',amount=amount),st('heal','self',amount=amount)],
      'mystic':[st('mark','chosen_other',amount=amount),st('delayed_damage','chosen_other',amount=amount+10,turns=1),st('reduce_next','self',amount=amount)],
      'tactical':[st('reduce_next','self',amount=amount),st('armor','self',amount=amount),st('buff_attack','chosen_enemy',amount=-amount)],
    }
    opts=options.get(profile,options['tactical'])
    return dict(opts[serial % len(opts)])

def _describe_step(step):
    op=step.get('op'); t=step.get('target','self'); a=int(step.get('amount',0) or 0)
    if op=='damage':
        if t=='self': return f'Take {a} damage'
        if t=='enemies': return f'Deal {a} damage to both opponents'
        if t=='all_others': return f'Deal {a} damage to every other living player'
        if t=='chosen_enemy': return f'Deal {a} damage to one opponent'
        return f'Deal {a} damage to one other player'
    if op=='heal':
        if t=='team': return f'Heal both members of your team {a} HP'
        if t=='self': return f'Heal yourself {a} HP'
        return f'Heal yourself or your teammate {a} HP'
    if op=='armor':
        if t=='team': return f'Give both members of your team {a} armor'
        if t=='self': return f'Gain {a} armor'
        return f'Give yourself or your teammate {a} armor'
    if op=='draw': return f'Draw {int(step.get("count",1) or 1)} card' + ('s' if int(step.get('count',1) or 1)!=1 else '')
    if op=='discard_random':
        n=int(step.get('count',1) or 1)
        who='one opponent' if t=='chosen_enemy' else 'yourself'
        return f'{who.capitalize()} discards {n} random card' + ('s' if n!=1 else '')
    if op=='buff_attack':
        if a<0 and t=='chosen_enemy': return f'One opponent’s next attack deals {abs(a)} less damage'
        if t=='team': return f'Your team gets +{a} damage on their next attack'
        if t=='ally': return f'Give yourself or your teammate +{a} damage on their next attack'
        return f'Your next attack gets +{a} damage'
    if op=='attack_multiplier': return f'Your next attack deals ×{step.get("mult",1)} damage'
    if op=='next_damage_multiplier': return f'Your next damage taken is ×{step.get("mult",1)}'
    if op=='reduce_next':
        if t=='ally': return f'Reduce the next damage you or your teammate takes by {a}'
        return f'Reduce your next incoming damage by {a}'
    if op=='mark': return f'Mark one other player for +{a} damage the next time they take damage'
    if op=='prevent_heal': return 'One opponent cannot heal until the start of their next turn'
    if op=='force_self_punch': return 'Choose an opponent. Their next action is a punch against themself'
    if op=='delayed_damage': return f'Deal {a} delayed damage to one other player at the start of their next turn'
    if op=='untargetable': return 'Until your next turn, you cannot be targeted'
    if op=='return_discard':
        n=int(step.get('count',1) or 1); mx=step.get('maxStars')
        return f'Return up to {n} ' + (f'non-{int(mx)+1}★ ' if mx else '') + 'card' + ('s' if n!=1 else '') + ' from your discard pile'
    if op=='punch_immunity': return f'Ignore the next {int(step.get("charges",1) or 1)} punch' + ('es' if int(step.get('charges',1) or 1)!=1 else '')
    if op=='extra_punch': return 'You may punch once this turn after playing this card'
    if op=='extra_play':
        n=int(step.get('count',1) or 1); mx=step.get('maxStars')
        return f'You may play {n} additional ' + (f'{mx}★ or lower ' if mx else '') + 'card' + ('s' if n!=1 else '') + ' this turn'
    if op=='skip_turn': return 'One opponent skips their next turn'
    if op=='steal_random': return f'Steal {int(step.get("count",1) or 1)} random card' + ('s' if int(step.get('count',1) or 1)!=1 else '') + ' from one opponent'
    if op=='damage_cap': return f'Until your next turn, no single hit can deal you more than {a} damage'
    if op=='swap_hp': return 'Swap your HP with one other living player'
    if op=='bonus_draw': return f'Draw {int(step.get("count",1) or 1)} extra card' + ('s' if int(step.get('count',1) or 1)!=1 else '') + ' at the start of your next turn'
    return None

def _describe_steps(steps):
    parts=[_describe_step(x) for x in steps]
    if any(x is None for x in parts): return None
    return '. '.join(parts)+'.'

_clean_serial=0
for c in out:
    if not c.get('generated') or c.get('meme') or c.get('cardType') in ('field','environment') or int(c['stars']) not in (3,4,5):
        continue
    steps=_flat_steps(c.get('action'))
    if not steps: continue
    steps=[x for x in steps if not _bad_comp(x)]
    if not steps: continue
    # Keep the main idea plus at most two riders.
    steps=steps[:3]
    lo,hi=_POWER_BANDS[int(c['stars'])]
    power=_action_power(seq(*steps))
    if power<lo:
        if len(steps)<3:
            steps.append(_rider_for(c.get('profile','tactical'),_clean_serial,max(10,int((lo-power)//10*10))))
        else:
            _increase_positive(steps,lo-power)
    power=_action_power(seq(*steps))
    if power>hi:
        excess=power-hi
        if len(steps)<3:
            steps.append(st('damage','self',amount=max(10,min(50,int(((excess+9)//10)*10))),attack=False))
        else:
            # Reduce the largest ordinary positive amount instead of adding a fourth clause.
            candidates=[x for x in steps if x.get('op') in ('damage','heal','armor','buff_attack','mark','reduce_next') and not (x.get('op')=='damage' and x.get('target')=='self') and float(x.get('amount',0) or 0)>10]
            if candidates:
                big=max(candidates,key=lambda x:float(x.get('amount',0) or 0))
                big['amount']=max(10,int(big.get('amount',0))-max(10,min(40,int(((excess+9)//10)*10))))
    text=_describe_steps(steps)
    if text:
        c['action']=seq(*steps); c['effect']=text; c['simplified']=True
    _clean_serial+=1

# If simplification happened to make two generated action sets identical, replace only the
# final rider with a small, useful signature rider. This keeps abilities mechanically distinct
# without returning to five-clause cards.
_used_actions={}
for serial,c in enumerate([x for x in out if x.get('generated') and x.get('action') and x.get('cardType') not in ('field','environment')]):
    key=json.dumps(c['action'],sort_keys=True,ensure_ascii=False)
    if key not in _used_actions:
        _used_actions[key]=c['id']; continue
    if c.get('meme'): continue
    steps=_flat_steps(c['action'])
    base=steps[:2]
    fixed=False
    for attempt in range(60):
        strength=10 + 10*((attempt//9)%4)
        rider=_rider_for(c.get('profile','tactical'),serial+attempt,strength)
        candidate=seq(*(base+[rider]))
        k=json.dumps(candidate,sort_keys=True,ensure_ascii=False)
        if k not in _used_actions:
            c['action']=candidate
            desc=_describe_steps(base+[rider])
            if desc: c['effect']=desc
            _used_actions[k]=c['id']; fixed=True; break
    if not fixed:
        # Extremely unlikely fallback: preserve gameplay and vary delayed timing/amount.
        rider=st('delayed_damage','chosen_other',amount=20+10*(serial%5),turns=1+(serial%2))
        candidate=seq(*(base+[rider])); c['action']=candidate
        desc=_describe_steps(base+[rider])
        if desc: c['effect']=desc
        _used_actions[json.dumps(candidate,sort_keys=True,ensure_ascii=False)]=c['id']

# Re-run global name de-duplication after meme overrides.
_seen_names={}
for c in out:
    key=c['name'].casefold()
    if key in _seen_names:
        c['name']=f"{c['name']} — {c['show']}"
    _seen_names[c['name'].casefold()]=c['id']

# Final clean-10 pass catches every generated/legacy flat point value after targeted rebalances.
for c in out:
    c['effect'], c['action'] = normalize_pair(c.get('effect',''), c.get('action'))


# Normalization can collapse two near-identical numeric variants into the same clean-10
# action. Do one last uniqueness repair on the normalized data.
_final_actions=set(); _final_effects=set()
for serial,c in enumerate([x for x in out if x.get('generated')]):
    akey=json.dumps(c.get('action'),sort_keys=True,ensure_ascii=False)
    ekey=c.get('effect','')
    if akey not in _final_actions and ekey not in _final_effects:
        _final_actions.add(akey); _final_effects.add(ekey); continue
    if c.get('cardType') in ('field','environment'):
        # Field keys are already unique by show/reference; duplicate text is okay to repair
        # with the field name without changing the mechanic.
        c['effect']=c['effect'].rstrip('.')+f' ({c["name"]}).'
        ekey=c['effect']; _final_actions.add(akey); _final_effects.add(ekey); continue
    steps=_flat_steps(c.get('action'))
    if not steps:
        # Coin/direct fallback: a small armor rider is easy to understand and stays balanced.
        steps=[st('armor','self',amount=10+10*(serial%4))]
    base=steps[:2]
    fixed=False
    for attempt in range(120):
        amount=10+10*((serial+attempt)%5)
        mode=(serial+attempt)%8
        if mode==0: rider=st('armor','self',amount=amount)
        elif mode==1: rider=st('heal','self',amount=amount)
        elif mode==2: rider=st('reduce_next','self',amount=amount)
        elif mode==3: rider=st('buff_attack','self',amount=amount)
        elif mode==4: rider=st('mark','chosen_other',amount=amount)
        elif mode==5: rider=st('delayed_damage','chosen_other',amount=amount+10,turns=1+(attempt%2))
        elif mode==6: rider=st('buff_attack','chosen_enemy',amount=-amount)
        else: rider=st('discard_random','chosen_enemy',count=1)
        candidate=seq(*(base+[rider]))
        desc=_describe_steps(base+[rider])
        if not desc: continue
        desc,candidate=normalize_pair(desc,candidate)
        k=json.dumps(candidate,sort_keys=True,ensure_ascii=False)
        if k not in _final_actions and desc not in _final_effects:
            c['action']=candidate; c['effect']=desc; akey=k; ekey=desc; fixed=True; break
    if not fixed:
        # Keep the mechanic and make the text unique as a last resort. This should be rare.
        c['effect']=c.get('effect','').rstrip('.')+f' [{c.get("canonRef",c["name"])}].'
        ekey=c['effect']
    _final_actions.add(akey); _final_effects.add(ekey)

counts=defaultdict(Counter)
for c in out: counts[c['show']][c['stars']]+=1
assert len(counts)==58
assert all(v[3]==POOL_TARGETS[3] and v[4]==POOL_TARGETS[4] and v[5]==POOL_TARGETS[5] for v in counts.values())
assert len(out)==58 * sum(POOL_TARGETS.values())
assert len({c['name'].casefold() for c in out})==len(out)

# Ensure generated cards do not use the old generic filler labels from the earliest prototype.
banned=('opening move','crossfire','guard stance','momentum shift','series finale','signature technique')
assert not any(c.get('generated') and any(x in c['name'].lower() for x in banned) for c in out)

(ROOT/'cards.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT/'shows.json').write_text(json.dumps(show_names, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Generated {len(out)} cards across {len(counts)} shows; pool per show = 15x3★ / 7x4★ / 2x5★.')
print(f'{sum(c.get("generated",False) for c in out)} generated canon-reference cards; deck requirement is 10/5/1 plus at least 3 Environments per selected show.')

