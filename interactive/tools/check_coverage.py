"""Small, strict course/catalog consistency gate; never infer coverage from a badge."""
import ast
import csv
import json
import re
from pathlib import Path
from inventory import inventory,ROOT

catalog=json.loads((ROOT/'interactive/catalog.json').read_text())
coverage=json.loads((ROOT/'interactive/coverage.json').read_text())
saved=json.loads((ROOT/'interactive/inventory.json').read_text())
current=inventory()
assert current==saved,'Course prose changed: review new methods, then refresh inventory.json and coverage.json.'
metadata=json.loads((ROOT/'interactive/data/metadata.json').read_text())
scope=json.loads((ROOT/'interactive/scope.json').read_text())
ids={e['id'] for e in catalog['experiments']}
assert len(ids)==len(catalog['experiments']),'Duplicate experiment id'
assert set(current)=={e['chapter'] for e in catalog['experiments']},'A course chapter has no live experiment'
assert coverage['chapter_headings']=={k:v['headings'] for k,v in current.items()},'Chapter headings need coverage review'
assert {i for unit in coverage['method_units'] for i in unit['experiments']}==ids,'Unmapped experiment or stale coverage record'
bib=(ROOT/'references.bib').read_text()
for experiment in catalog['experiments']:
    assert experiment['terms'] and experiment['diagnostics'] and experiment['description'],experiment['id']
    assert re.search(r'@\w+\{'+re.escape(experiment['reference'])+r',',bib),experiment['reference']
    assert (ROOT/experiment['implementation'].split(':')[0]).exists(),experiment['id']
    keys=[c['key'] for c in experiment['controls']]
    assert len(keys)==len(set(keys)),experiment['id']
    assert set(keys)<=set(experiment['defaults']),experiment['id']
    for control in experiment['controls']:
        if control.get('when'):assert set(control['when'])<=set(keys),control
        if control['type']=='number':
            assert control['min']<=control['default']<=control['max'],control
            grid=(control['default']-control['min'])/control['step']
            assert abs(grid-round(grid))<1e-7,('Default violates HTML step grid',control)
    for dataset in experiment['datasets']:
        record=metadata[dataset]
        assert (ROOT/record['path']).is_file(),record['path']
        assert record['series'] and record['provenance'] and record['license'] and record['vintage'],dataset
        if record.get('join'):assert (ROOT/record['join']).is_file()
        with (ROOT/record['path']).open() as handle:columns=set(next(csv.reader(handle)))
        if record.get('join'):
            with (ROOT/record['join']).open() as handle:columns.update(next(csv.reader(handle)))
        for control in experiment['controls']:
            if control['key']=='variables':
                for choice in control['options']:
                    assert set(choice.split(','))<=columns,(experiment['id'],dataset,choice)
for qualification in scope:
    assert set(qualification['browser'])<=ids,qualification['id']
    assert (ROOT/qualification['implementation'].split(':')[0]).is_file()
for path in (ROOT/'interactive/python').glob('*.py'):ast.parse(path.read_text())
print(f'Coverage reviewed: {len(current)} chapters, {len(ids)} live experiments, {len(scope)} explicit qualifications.')
