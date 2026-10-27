import csv
import json
import zipfile
import pytest
from src.experiments import generate, validate_run_id
from src.kinematics import PRESETS

@pytest.mark.parametrize('preset,joint,parameter,unit,start,end', [
    ('rrr', 2, 'theta','graus',-45,45),
    ('rrp', 3, 'd','m',0,.8),
    ('rpp', 2, 'd','m',0,1),
    ('ppp', 1, 'd','m',.1,1.1),
])
def test_experiment_for_each_joint_type(tmp_path,preset,joint,parameter,unit,start,end):
    result=generate(PRESETS[preset], joint=joint,start=start,end=end,samples=9,output_root=tmp_path)
    folder=tmp_path/result['id']
    assert validate_run_id(result['id'])
    assert result['varied_parameter']==parameter
    assert result['parameter_unit']==unit
    assert result['joint_type']==PRESETS[preset][joint-1]['type']
    assert len(result['figures'])==4
    assert all((folder/f).stat().st_size>10000 for f in result['figures'])
    with (folder/'dados_cinematica.csv').open(encoding='utf-8-sig',newline='') as f:
        entries=list(csv.DictReader(f,delimiter=';'))
    assert len(entries)==9
    assert entries[0]['parametro_variado']==parameter
    assert float(entries[0]['valor_variavel'])==pytest.approx(start)
    assert float(entries[-1]['valor_variavel'])==pytest.approx(end)
    assert json.loads((folder/'metadados.json').read_text(encoding='utf-8'))['configuration']==preset.upper()
    with zipfile.ZipFile(folder/'resultados.zip') as z:
        assert len(z.namelist())==6
        assert z.testzip() is None


def test_prismatic_straight_trajectory(tmp_path):
    result=generate(PRESETS['ppp'],joint=1,start=0,end=1,samples=11,output_root=tmp_path)
    assert result['travel_distance_m']==pytest.approx(1,abs=1e-12)


def test_input_errors(tmp_path):
    for kwargs in ({'joint':4},{'samples':2},{'start':.5,'end':.2},
                   {'rows':PRESETS['ppp'],'joint':1,'start':0,'end':6}):
        with pytest.raises(ValueError):generate(output_root=tmp_path,**kwargs)
    assert not validate_run_id('../../etc')

@pytest.mark.parametrize('lang', ['pt', 'en'])
def test_export_language_and_charts(tmp_path, lang):
    result = generate(PRESETS['rrr'], joint=2, start=-30, end=30,
                      samples=7, output_root=tmp_path, lang=lang)
    metadata = json.loads((tmp_path/result['id']/'metadados.json').read_text(encoding='utf-8'))
    assert metadata['language'] == lang
    assert metadata['configuration'] == 'RRR'
    assert all((tmp_path/result['id']/figure).stat().st_size > 1000 for figure in result['figures'])


def test_invalid_language(tmp_path):
    with pytest.raises(ValueError, match='Language'):
        generate(PRESETS['rrr'], output_root=tmp_path, lang='fr')
