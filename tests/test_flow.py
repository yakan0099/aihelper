import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
import app


class Flow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = patch.object(app, 'DB', Path(self.tmp.name) / 'test.db'); self.db.start()
        self.env = patch.dict(os.environ, {'ASSISTANT_API_KEY': ''}); self.env.start()
        self.client = TestClient(app.app)
        self.screen = {'scope': '뉴스 정리', 'window_id': 'tab-1', 'fingerprint': 'a'*64,
                       'image': 'data:image/jpeg;base64,AA==', 'text': '테스트 기사 본문'}

    def tearDown(self):
        self.client.close(); self.env.stop(); self.db.stop(); self.tmp.cleanup()

    def analyze(self, **changes):
        return self.client.post('/api/analyze', json=self.screen | changes).json()

    def test_correction_reused_and_edit_delete(self):
        first = self.analyze()
        self.assertIn('화면 이미지를 해석하지 않았습니다', first['answer'])
        f = self.client.post('/api/runs/'+first['run_id']+'/feedback', json={'correct': False, 'correction': '결론을 먼저 작성'}).json()
        second = self.analyze()
        self.assertIn('결론을 먼저 작성', second['answer'])
        self.assertEqual(len(second['memories']), 1)
        self.assertEqual(self.analyze(scope='다른 업무')['memories'], [])
        mid = f['memory_id']
        self.client.put('/api/memories/'+mid, json={'scope': '뉴스 정리', 'correction': '주의점 포함'})
        self.assertIn('주의점 포함', self.analyze()['answer'])
        self.client.delete('/api/memories/'+mid)
        self.assertEqual(self.analyze()['memories'], [])
        self.client.delete('/api/history')
        self.assertEqual(self.client.get('/api/runs/'+first['run_id']+'/events').status_code, 404)

    def test_guard_window_pixels_and_age(self):
        rid = self.analyze()['run_id']; url = '/api/runs/'+rid+'/guard'
        valid = {k: self.screen[k] for k in ['window_id', 'fingerprint']}
        self.assertTrue(self.client.post(url, json=valid).json()['allowed'])
        self.assertFalse(self.client.post(url, json=valid | {'window_id': 'tab-2'}).json()['allowed'])
        self.assertFalse(self.client.post(url, json=valid | {'fingerprint': 'b'*64}).json()['allowed'])
        with app.connect() as c:
            c.execute('UPDATE runs SET created=0 WHERE id=?', (rid,))
        self.assertFalse(self.client.post(url, json=valid).json()['allowed'])

    def test_provider_failure_does_not_log_secret(self):
        with patch.dict(os.environ, {'ASSISTANT_API_KEY': 'test-secret', 'ASSISTANT_MODEL': 'test'}), patch.object(app, 'provider_post', side_effect=RuntimeError('test-secret')):
            r = self.analyze()
        self.assertIn('error', r)
        events = self.client.get('/api/runs/'+r['run_id']+'/events').json()
        self.assertEqual(events[-1]['status'], 'failed')
        self.assertNotIn('test-secret', str(events))
        self.assertEqual(self.client.post('/api/runs/'+r['run_id']+'/feedback', json={'correct': True}).status_code, 409)

    def test_api_adapter_passes_correction(self):
        rid = self.analyze()['run_id']
        self.client.post('/api/runs/'+rid+'/feedback', json={'correct': False, 'correction': '세 줄 요약'})
        response = httpx.Response(200, json={'choices': [{'message': {'content': '{"observation":"기사 화면","summary":"핵심","next_action":"원문 확인"}'}}]}, request=httpx.Request('POST', 'https://example.com'))
        with patch.dict(os.environ, {'ASSISTANT_API_KEY': 'test', 'ASSISTANT_MODEL': 'vision-test'}), patch.object(app, 'provider_post', return_value=response) as post:
            r = self.analyze()
        self.assertEqual(r['mode'], 'api')
        self.assertIn('원문 확인', r['answer'])
        self.assertIn('세 줄 요약', str(post.call_args.kwargs['json']))

    def test_capture_failure_record(self):
        r = self.client.post('/api/capture-failure', json={'scope': '뉴스', 'error_type': 'NotAllowedError'}).json()
        events = self.client.get('/api/runs/'+r['run_id']+'/events').json()
        self.assertEqual(events[0]['stage'], '화면 수집')
        self.assertEqual(events[0]['status'], 'failed')

    def test_cross_origin_rejected(self):
        self.assertEqual(self.client.post('/api/analyze', json=self.screen, headers={'origin': 'https://evil.example'}).status_code, 403)
        self.assertEqual(self.client.get('/api/status', headers={'host': 'evil.example'}).status_code, 403)


if __name__ == '__main__':
    unittest.main()
