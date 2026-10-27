from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def test_translation_keys_present_in_both_languages():
    html=(ROOT/'templates/index.html').read_text(encoding='utf-8')
    js=(ROOT/'static/js/i18n.js').read_text(encoding='utf-8')
    keys=set(re.findall(r'data-i18n="([a-zA-Z]+)"', html))
    assert len(keys)>40
    # The translation tables are built as parallel plain objects: each key occurs in both.
    for key in keys:
        assert len(re.findall(r'\b'+key+r'\s*:', js))==2, key


def test_no_network_translation_service():
    js=(ROOT/'static/js/i18n.js').read_text(encoding='utf-8')
    assert 'fetch(' not in js
