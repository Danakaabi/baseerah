import hashlib
from pathlib import Path
from html.parser import HTMLParser
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
FRONT = Path(__file__).resolve().parents[1] / 'Frontend ' / 'baseerah-separated'

def test_all_ui_pages_are_served():
    for page in FRONT.rglob('*.html'):
        response = client.get('/ui/' + page.relative_to(FRONT).as_posix())
        assert response.status_code == 200
        assert 'Readex+Pro' in response.text
        assert 'statusbar' not in response.text
    assert client.get('/').url.path == '/ui/'

def test_sources_match_index():
    response = client.get('/tools/sources')
    assert response.status_code == 200
    assert response.json()['sources']
    assert all(s['chunk_count'] > 0 for s in response.json()['sources'])

def test_fingerprint_is_real_and_duplicate_is_stable(tmp_path, monkeypatch):
    monkeypatch.setenv('BASEERAH_REGISTRY_DB', str(tmp_path / 'registry.sqlite3'))
    def send(title):
        return client.post('/tools/fingerprint', data={'title': title}, files={'audio': ('clip.wav', b'original-bytes', 'audio/wav')})
    first = send('Original'); second = send('Copy')
    assert first.status_code == 200
    assert first.json()['sha256'] == hashlib.sha256(b'original-bytes').hexdigest()
    assert first.json() == second.json()
    assert first.json()['identity_verified'] is False

def test_fingerprint_rejects_empty_and_invalid(tmp_path, monkeypatch):
    monkeypatch.setenv('BASEERAH_REGISTRY_DB', str(tmp_path / 'registry.sqlite3'))
    for name, data, status in [('clip.wav', b'', 400), ('script.html', b'x', 415)]:
        assert client.post('/tools/fingerprint', data={'title': 'Title'}, files={'audio': (name, data)}).status_code == status
    assert client.post('/tools/fingerprint', data={'title': '   '}, files={'audio': ('clip.wav', b'x')}).status_code == 422

def test_local_links_resolve():
    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for key, val in attrs:
                if key in {'href', 'src'} and val and not val.startswith(('https:', '#')):
                    assert (self.page.parent / val).is_file(), (self.page, val)
    for page in FRONT.rglob('*.html'):
        parser = Links(); parser.page = page; parser.feed(page.read_text())


def test_fingerprint_check_uses_original_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv('BASEERAH_REGISTRY_DB', str(tmp_path / 'registry.sqlite3'))
    upload = {'audio': ('clip.wav', b'original-bytes', 'audio/wav')}
    assert client.post('/tools/fingerprint/check', files=upload).json()['match_found'] is False
    client.post('/tools/fingerprint', data={'title': 'Title'}, files=upload)
    assert client.post('/tools/fingerprint/check', files=upload).json()['match_found'] is True
    assert client.post('/tools/fingerprint/check', files={'audio': ('clip.wav', b'changed', 'audio/wav')}).json()['match_found'] is False
