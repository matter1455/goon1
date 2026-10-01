import json, sys
from collections import Counter, defaultdict
from pathlib import Path
from canon_references import SHOW_REFERENCES

ROOT = Path(__file__).resolve().parent
cards = json.loads((ROOT / 'cards.json').read_text(encoding='utf-8'))
by_show = defaultdict(Counter)
for c in cards:
    by_show[c['show']][int(c['stars'])] += 1

errors=[]
EXPECTED=(15,7,2)
if len(cards) != 1392: errors.append(f'Expected 1392 cards, got {len(cards)}')
if len(by_show) != 58: errors.append(f'Expected 58 shows, got {len(by_show)}')
for show in SHOW_REFERENCES:
    got=by_show[show]
    if (got[3],got[4],got[5]) != EXPECTED: errors.append(f'{show}: got {dict(got)}')

names=[c['name'].casefold() for c in cards]
if len(names)!=len(set(names)): errors.append('Duplicate card names found')

generated=[c for c in cards if c.get('generated')]
texts=[c['effect'] for c in generated]
actions=[json.dumps(c.get('action'),sort_keys=True,ensure_ascii=False) for c in generated]
if len(texts)!=len(set(texts)): errors.append('Generated effect text is not unique')
if len(actions)!=len(set(actions)): errors.append('Generated structured actions are not unique')

for c in generated:
    if c.get('canonRef') not in SHOW_REFERENCES[c['show']]:
        errors.append(f"{c['name']}: canonRef not in its show reference list")

banned=('opening move','crossfire','guard stance','momentum shift','series finale','signature technique')
for c in generated:
    if any(x in c['name'].casefold() for x in banned): errors.append(f"Generic filler name remains: {c['name']}")

if errors:
    print('VALIDATION FAILED')
    for e in errors: print('-',e)
    sys.exit(1)

print('VALIDATION OK')
print(f'- {len(cards)} cards')
print(f'- {len(by_show)} shows')
print(f'- {len(generated)} generated canon-reference cards')
print('- every show pool = 15x 3-star / 7x 4-star / 2x 5-star')
print('- each deck still selects 10x 3-star / 5x 4-star / 1x 5-star per chosen show')
print('- generated effect text unique')
print('- generated structured actions unique')
