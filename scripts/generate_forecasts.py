#!/usr/bin/env python3
"""KEIBA NINE: synthetic AI test only. Never overwrites public predictions."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

source_path = Path('keiba-nine-auto-feed.json')
assert source_path.exists(), 'Test feed file is missing'
feed = json.loads(source_path.read_text(encoding='utf-8'))
races = feed.get('forecasts', [])
assert races and all(r.get('recordType') == 'test' for r in races), 'Only synthetic tests are allowed'
key = os.environ.get('OPENAI_API_KEY')
assert key, 'OPENAI_API_KEY secret is not configured'

race = races[0]
prompt = (
    'これは架空の競馬レースのプログラム試験です。実戦予想や投票勧誘ではありません。'
    '提供されたデータだけを使い、事実を創作せず、'
    '日本語でJSONオブジェクトを出力してください。'
    'キーは summary と warning。両方とも短い文字列。'
    '根拠がない評価項目は未検証と明記してください。\n'
    + json.dumps(race, ensure_ascii=False)
)
request_body = {
    'model': 'gpt-4o-mini',
    'input': [{'role': 'user', 'content': prompt}],
    'text': {'format': {'type': 'json_object'}},
    'max_output_tokens': 350,
}
request = Request(
    'https://api.openai.com/v1/responses',
    data=json.dumps(request_body, ensure_ascii=False).encode('utf-8'),
    headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
    method='POST',
)
with urlopen(request, timeout=60) as response:
    result = json.load(response)
parts = [c.get('text', '') for item in result.get('output', [])
         for c in item.get('content', []) if c.get('type') == 'output_text']
assert result.get('status') == 'completed' and parts, 'AI response incomplete'
notes = json.loads(''.join(parts))
assert isinstance(notes.get('summary'), str) and isinstance(notes.get('warning'), str)

# Separate output: public feed and existing records remain untouched.
preview = {
    'testOnly': True,
    'race': {'date': race['date'], 'track': race['track'], 'race': race['race']},
    'summary': notes['summary'],
    'warning': notes['warning'],
}
Path('keiba-nine-ai-test.json').write_text(
    json.dumps(preview, ensure_ascii=False, indent=2), encoding='utf-8')
print('Synthetic AI test OK. Saved keiba-nine-ai-test.json')
