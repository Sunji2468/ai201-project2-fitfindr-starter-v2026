"""Capture Unit 4 failure/trace evidence without changing the saved API key."""
import json
import os
from pathlib import Path
import subprocess
import sys

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def main():
    env_file = ROOT / '.env'
    original = env_file.read_bytes()
    key = dotenv_values(env_file).get('GEMINI_API_KEY', '').strip()
    if not key:
        raise RuntimeError('Add GEMINI_API_KEY to .env before running this check.')
    bad_key = key[:-1] + ('A' if key[-1] != 'A' else 'B')
    cases = [
        ('happy', 'vintage graphic tee under $30', []),
        ('empty_search', 'designer ballgown size XXS under $5', []),
        ('empty_wardrobe', 'vintage graphic tee under $30', ['--empty-wardrobe']),
        ('model_unavailable', 'rust corduroy wide-leg pants size W28 under $37.42', []),
    ]
    records = []
    for name, query, flags in cases:
        env = os.environ.copy()
        env['GEMINI_API_KEY'] = bad_key if name == 'model_unavailable' else key
        # Force a real request for the bad-key test, even on subsequent reruns.
        if name == 'model_unavailable':
            env['AI201_CACHE'] = '0'
        args = ['app.py', 'ask', query, *flags, '--trace']
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=180)
        output = result.stdout + result.stderr
        for secret in (key, bad_key):
            output = output.replace(secret, '[REDACTED]')
        assert result.returncode == 0, f'{name} exited unsuccessfully'
        assert 'Traceback (most recent call last)' not in output, name
        if name == 'model_unavailable':
            assert 'The model request failed during suggest_outfit.' in output
            assert 'served from cache' not in output
            assert '1 model calls this session' in output
        elif name == 'empty_search':
            assert 'No matching listings.' in output
            assert '] suggest_outfit' not in output
        else:
            assert 'Fit card:' in output
        records.append({'case': name, 'args': args, 'output': output,
                        'cache_disabled': name == 'model_unavailable',
                        'returncode': result.returncode})
        print(name + ':\n' + output, flush=True)
    assert env_file.read_bytes() == original, '.env changed during the check'
    target = ROOT / 'results' / 'unit4_failure_checks.json'
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    print('All cases recorded; saved .env unchanged.')


if __name__ == '__main__':
    main()
