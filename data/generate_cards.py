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
        'hinokami kagura': ('Deal 35 damage to both opponents.', {'type':'split_enemies','amount':35}),
        'one punch': ('Deal 60 damage to one other player.', {'type':'damage','amount':60,'target':'other'}),
        'equivalent exchange': ('Discard one 3★ card, then draw 2 cards.', {'type':'discard_star_draw','stars':3,'draw':2}),
        'excalibur': ('Deal 100 damage to one other player.', {'type':'damage','amount':100,'target':'other'}),
        'how cute': ('Deal 35 damage to both opponents.', {'type':'split_enemies','amount':35}),
    }
    if k in simple:
        c['effect'], c['action'] = simple[k]

    replacements = {
      'i mustn’t run away':'For your next 2 turns, you cannot play a card; your punch deals 45 damage instead of 20.',
      'apology':'Lose 20 HP, heal your teammate 35 HP, then draw 1 card.',
      'star eye':'The next time you draw at the start of your turn, draw 1 additional card.',
      'agnes tachyon':'Return one 3★ card from your discard pile to your hand, then draw 1 card.',
      'boredom':'Choose an opponent. They draw their top card; if it is 3★, they give it to you. Otherwise they keep it.',
      'unlimited blade works':'The next time you draw at the start of your turn, draw 1 additional card.',
      'the place above the grey fog':'Draw 5 cards, then you may play one additional card this turn.'
    }
    if k in replacements: c['effect'] = replacements[k]
    return c

def st(op, target=None, **kwargs):
    d={'op':op}
    if target is not None: d['target']=target
    d.update(kwargs)
    return d

def seq(*steps): return {'type':'sequence','steps':list(steps)}


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
    """Add a small role-consistent secondary effect so every generated card is mechanically unique.

    The twist is intentionally modest: the rarity baseline remains the main power budget. The role
    filter avoids flavor failures such as an obvious attacker randomly becoming a healer.
    """
    import hashlib
    h = int(hashlib.sha256(f'{show}|{ref}|{stars}|{attempt}'.encode()).hexdigest()[:12], 16)
    base_ops = set(_action_ops(action))
    high_impact = any(op in {'extra_play','skip_turn','steal_random','swap_hp'} for op in base_ops)
    base = 3 + (h % 10)

    if high_impact:
        # High-action-economy/control cards pay a small cost instead of gaining more value.
        costs = [
            (st('damage','self',amount=base+2,attack=False), f'Afterward, take {base+2} damage.'),
            (st('discard_random','self',count=1), 'Afterward, discard 1 random card from your hand.'),
            (st('buff_attack','self',amount=-(base+1)), f'Afterward, your next attack deals {base+1} less damage.'),
        ]
        step, text = costs[(h // 17) % len(costs)]
    else:
        choices = {
            'assault': [
                (st('buff_attack','self',amount=base), f'Afterward, your next attack gets +{base} damage.'),
                (st('mark','chosen_other',amount=base), f'Afterward, mark one other player for +{base} on the next damage they take.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('reduce_next','self',amount=base+2), f'Afterward, reduce the next damage you take by {base+2}.'),
                (st('buff_attack','chosen_enemy',amount=-base), f'Afterward, an opponent’s next attack deals {base} less damage.'),
                (st('buff_attack','ally',amount=base), f'Afterward, give your teammate +{base} damage on their next attack.'),
                (st('armor','ally',amount=base), f'Afterward, give yourself or your teammate {base} armor.'),
                (st('damage','self',amount=base,attack=False), f'Afterward, take {base} damage.'),
            ],
            'risk': [
                (st('buff_attack','self',amount=base+2), f'Afterward, your next attack gets +{base+2} damage.'),
                (st('mark','chosen_other',amount=base+1), f'Afterward, mark one other player for +{base+1} on the next damage they take.'),
                (st('damage','self',amount=base,attack=False), f'Afterward, take {base} damage.'),
                (st('next_damage_multiplier','self',mult=1.1 + (base % 3)*0.05), f'Afterward, the next damage you take is increased by {int(((1.1 + (base % 3)*0.05)-1)*100)}%.'),
                (st('buff_attack','chosen_enemy',amount=-base), f'Afterward, an opponent’s next attack deals {base} less damage.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('buff_attack','ally',amount=base), f'Afterward, give your teammate +{base} damage on their next attack.'),
                (st('reduce_next','self',amount=base+2), f'Afterward, reduce the next damage you take by {base+2}.'),
            ],
            'team': [
                (st('heal','ally',amount=base+3), f'Afterward, heal yourself or your teammate {base+3} HP.'),
                (st('armor','ally',amount=base+1), f'Afterward, give yourself or your teammate {base+1} armor.'),
                (st('buff_attack','team',amount=max(3,base//2)), f'Afterward, you and your teammate each get +{max(3,base//2)} damage on your next attack.'),
                (st('reduce_next','ally',amount=base+3), f'Afterward, reduce the next damage your teammate takes by {base+3}.'),
                (st('heal','self',amount=base+2), f'Afterward, heal yourself {base+2} HP.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('buff_attack','ally',amount=base+1), f'Afterward, give your teammate +{base+1} damage on their next attack.'),
                (st('reduce_next','self',amount=base+2), f'Afterward, reduce the next damage you take by {base+2}.'),
            ],
            'social': [
                (st('heal','ally',amount=base+4), f'Afterward, heal yourself or your teammate {base+4} HP.'),
                (st('armor','ally',amount=base), f'Afterward, give yourself or your teammate {base} armor.'),
                (st('buff_attack','ally',amount=base), f'Afterward, give your teammate +{base} damage on their next attack.'),
                (st('reduce_next','ally',amount=base+2), f'Afterward, reduce the next damage your teammate takes by {base+2}.'),
                (st('heal','self',amount=base+3), f'Afterward, heal yourself {base+3} HP.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('buff_attack','team',amount=max(3,base//2)), f'Afterward, you and your teammate each get +{max(3,base//2)} damage on your next attack.'),
                (st('reduce_next','self',amount=base+2), f'Afterward, reduce the next damage you take by {base+2}.'),
            ],
            'tempo': [
                (st('buff_attack','self',amount=base), f'Afterward, your next attack gets +{base} damage.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('buff_attack','team',amount=max(3,base//2)), f'Afterward, you and your teammate each get +{max(3,base//2)} damage on your next attack.'),
                (st('reduce_next','self',amount=base+1), f'Afterward, reduce the next damage you take by {base+1}.'),
                (st('heal','self',amount=base+2), f'Afterward, heal yourself {base+2} HP.'),
                (st('heal','ally',amount=base+2), f'Afterward, heal yourself or your teammate {base+2} HP.'),
                (st('buff_attack','chosen_enemy',amount=-base), f'Afterward, an opponent’s next attack deals {base} less damage.'),
                (st('mark','chosen_other',amount=base), f'Afterward, mark one other player for +{base} on the next damage they take.'),
            ],
            'sport': [
                (st('buff_attack','self',amount=base+1), f'Afterward, your next attack gets +{base+1} damage.'),
                (st('buff_attack','ally',amount=base), f'Afterward, give your teammate +{base} damage on their next attack.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('heal','self',amount=base+2), f'Afterward, heal yourself {base+2} HP.'),
                (st('reduce_next','self',amount=base+2), f'Afterward, reduce the next damage you take by {base+2}.'),
                (st('armor','ally',amount=base), f'Afterward, give yourself or your teammate {base} armor.'),
                (st('buff_attack','team',amount=max(3,base//2)), f'Afterward, you and your teammate each get +{max(3,base//2)} damage on your next attack.'),
                (st('mark','chosen_other',amount=base), f'Afterward, mark one other player for +{base} on the next damage they take.'),
            ],
            'control': [
                (st('buff_attack','chosen_enemy',amount=-base), f'Afterward, an opponent’s next attack deals {base} less damage.'),
                (st('mark','chosen_other',amount=base), f'Afterward, mark one other player for +{base} on the next damage they take.'),
                (st('reduce_next','self',amount=base+2), f'Afterward, reduce the next damage you take by {base+2}.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('buff_attack','ally',amount=base), f'Afterward, give your teammate +{base} damage on their next attack.'),
                (st('armor','ally',amount=base), f'Afterward, give yourself or your teammate {base} armor.'),
                (st('heal','self',amount=base+2), f'Afterward, heal yourself {base+2} HP.'),
                (st('buff_attack','self',amount=base), f'Afterward, your next attack gets +{base} damage.'),
            ],
            'mystic': [
                (st('mark','chosen_other',amount=base), f'Afterward, mark one other player for +{base} on the next damage they take.'),
                (st('reduce_next','self',amount=base+2), f'Afterward, reduce the next damage you take by {base+2}.'),
                (st('buff_attack','self',amount=base), f'Afterward, your next attack gets +{base} damage.'),
                (st('armor','self',amount=base), f'Afterward, gain {base} armor.'),
                (st('buff_attack','chosen_enemy',amount=-base), f'Afterward, an opponent’s next attack deals {base} less damage.'),
                (st('armor','ally',amount=base), f'Afterward, give yourself or your teammate {base} armor.'),
                (st('heal','self',amount=base+2), f'Afterward, heal yourself {base+2} HP.'),
                (st('buff_attack','ally',amount=base), f'Afterward, give your teammate +{base} damage on their next attack.'),
            ],
            'tactical': [
                (st('armor','self',amount=base+1), f'Afterward, gain {base+1} armor.'),
                (st('reduce_next','self',amount=base+3), f'Afterward, reduce the next damage you take by {base+3}.'),
                (st('buff_attack','chosen_enemy',amount=-base), f'Afterward, an opponent’s next attack deals {base} less damage.'),
                (st('armor','ally',amount=base), f'Afterward, give yourself or your teammate {base} armor.'),
                (st('heal','self',amount=base+2), f'Afterward, heal yourself {base+2} HP.'),
                (st('heal','ally',amount=base+2), f'Afterward, heal yourself or your teammate {base+2} HP.'),
                (st('buff_attack','self',amount=base), f'Afterward, your next attack gets +{base} damage.'),
                (st('mark','chosen_other',amount=base), f'Afterward, mark one other player for +{base} on the next damage they take.'),
            ],
        }
        pool = choices.get(profile, choices['tactical'])
        # Prefer a secondary mechanic not already in the card's main sequence.
        ordered = [pool[(h // 17 + i) % len(pool)] for i in range(len(pool))]
        pick = next((x for x in ordered if x[0].get('op') not in base_ops), ordered[0])
        step, text = pick
    return effect.rstrip('.') + '. ' + text, {'type':'bundle','main':action,'after':[step]}

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

counts=defaultdict(Counter)
for c in out: counts[c['show']][c['stars']]+=1
assert len(counts)==58
assert all(v[3]==10 and v[4]==5 and v[5]==1 for v in counts.values())
assert len(out)==928
assert len({c['name'].casefold() for c in out})==len(out)

# Ensure generated cards do not use the old generic filler labels.
banned=('opening move','crossfire','second wind','guard stance','momentum shift','series finale','signature technique')
assert not any(c.get('generated') and any(x in c['name'].lower() for x in banned) for c in out)

(ROOT/'cards.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT/'shows.json').write_text(json.dumps(show_names, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Generated {len(out)} cards across {len(counts)} shows; {sum(c.get("generated",False) for c in out)} canon-based new cards.')
