import pytest
pytest.importorskip('flask')
from app import app

@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_home_and_health(client):
    response=client.get('/')
    assert response.status_code==200
    assert b'DH RoboLab' in response.data
    assert client.get('/api/health').json['joint_types']==['R','P']


def test_presets_and_fk(client):
    presets=client.get('/api/defaults').json['presets']
    assert {'rrr','rrp','rpp','ppp'}.issubset(presets)
    for kind in ('rrr','rrp','rpp','ppp'):
        result=client.post('/api/fk',json={'rows':presets[kind]})
        assert result.status_code==200
        assert result.json['configuration']==kind.upper()
    assert client.post('/api/fk',json={'rows':[]}).status_code==400


def test_experiment_and_download(client,tmp_path,monkeypatch):
    import src.experiments as e
    import app as a
    monkeypatch.setattr(e,'BASE_OUTPUT',tmp_path)
    monkeypatch.setattr(a,'BASE_OUTPUT',tmp_path)
    preset=client.get('/api/defaults').json['presets']['ppp']
    r=client.post('/api/experiments',json={'rows':preset,'joint':2,'start':0,'end':1,'samples':6})
    assert r.status_code==200,r.json
    assert r.json['varied_parameter']=='d'
    assert r.json['configuration']=='PPP'
    download=client.get(r.json['download_url'])
    assert download.status_code==200
    assert download.data[:2]==b'PK'
    assert client.get('/api/results/../app.py').status_code in (404,308)


def test_interface_language_switch(client):
    html = client.get('/').data.decode('utf-8')
    assert 'id="langPt"' in html
    assert 'id="langEn"' in html
    assert 'js/i18n.js' in html
    assert client.get('/api/health').json['languages'] == ['pt', 'en']


def test_english_experiment_via_api(client,tmp_path,monkeypatch):
    import src.experiments as e
    import app as a
    monkeypatch.setattr(e,'BASE_OUTPUT',tmp_path)
    monkeypatch.setattr(a,'BASE_OUTPUT',tmp_path)
    preset=client.get('/api/defaults').json['presets']['rrp']
    response=client.post('/api/experiments',json={'rows':preset,'joint':3,
                                                    'start':0,'end':.3,'samples':5,'lang':'en'})
    assert response.status_code == 200
    assert response.json['language'] == 'en'
    assert client.get(response.json['download_url']).status_code == 200
