import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
import app


class Web(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = patch.object(app, 'DB', Path(self.tmp.name)/'web.db'); self.db.start()
        self.env = patch.dict(os.environ, {'ASSISTANT_API_KEY':'', 'ASSISTANT_MODEL':'test', 'ASSISTANT_DAILY_LIMIT':'2', 'ASSISTANT_USER_DAILY_LIMIT':'2'}); self.env.start()
        self.client = TestClient(app.app)
        self.headers = {'Authorization':'Bearer '+'a'*64}
        self.memory = {'id':'11111111-1111-1111-1111-111111111111','scope':'記事','correction':'結論 first','updated':1,'deleted':False}

    def tearDown(self):
        self.client.close(); self.env.stop(); self.db.stop(); self.tmp.cleanup()

    def test_sync_isolated_and_deletion_wins(self):
        url='/api/memories/sync'
        self.assertEqual(self.client.post(url,json={'memories':[self.memory]}).status_code,401)
        self.assertEqual(len(self.client.post(url,headers=self.headers,json={'memories':[self.memory]}).json()),1)
        self.assertEqual(self.client.get('/api/memories',headers={'Authorization':'Bearer '+'b'*64}).json(),[])
        tomb=self.memory|{'deleted':True,'correction':'','updated':2}
        self.client.post(url,headers=self.headers,json={'memories':[tomb]})
        r=self.client.post(url,headers=self.headers,json={'memories':[self.memory]}).json()
        self.assertTrue(r[0]['deleted'])
        self.client.delete('/api/memories',headers=self.headers)
        self.assertEqual(self.client.get('/api/memories',headers=self.headers).json(),[])

    def test_demo_does_not_accept_paid_requests(self):
        r=self.client.post('/api/analyze',headers=self.headers,json={'scope':'test'})
        self.assertEqual(r.status_code,503)
        self.assertEqual(self.client.get('/api/status').json()['mode'],'demo')

    def test_provider_memory_payload_quota_and_no_screen_storage(self):
        response=httpx.Response(200,json={'choices':[{'message':{'content':'{"observation":"article","summary":"summary","next_action":"review"}'}}]},request=httpx.Request('POST','https://example.com'))
        data={'scope':'test','image':'data:image/jpeg;base64,SECRETSCREEN','text':'PRIVATEBODY','corrections':['conclusion first']}
        with patch.dict(os.environ,{'ASSISTANT_API_KEY':'SECRETKEY'}), patch.object(app,'provider_post',return_value=response) as post:
            for _ in range(2):
                self.assertEqual(self.client.post('/api/analyze',headers=self.headers,json=data).status_code,200)
            self.assertIn('conclusion first',str(post.call_args.kwargs['json']))
            self.assertEqual(self.client.post('/api/analyze',headers=self.headers,json=data).status_code,429)
            self.assertEqual(self.client.post('/api/analyze',headers={'Authorization':'Bearer '+'b'*64},json=data).status_code,429)
        contents=app.DB.read_bytes()
        for secret in (b'SECRETSCREEN',b'PRIVATEBODY',b'SECRETKEY',b'conclusion first'):
            self.assertNotIn(secret,contents)

    def test_errors_do_not_leak_provider_secrets(self):
        with patch.dict(os.environ,{'ASSISTANT_API_KEY':'KEY'}),patch.object(app,'provider_post',side_effect=RuntimeError('KEY SECRET')):
            r=self.client.post('/api/analyze',headers=self.headers,json={'scope':'test','image':'data:image/jpeg;base64,AA=='})
        self.assertEqual(r.status_code,502)
        self.assertNotIn('KEY',r.text)
        self.assertIn('RuntimeError',r.text)

    def test_host_origin_and_size_protection(self):
        self.assertEqual(self.client.get('/api/status',headers={'host':'evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/memories/sync',headers=self.headers|{'origin':'https://evil.example'},json={'memories':[]}).status_code,403)
        self.assertEqual(self.client.post('/api/analyze',headers=self.headers,content=b'x'*4500001).status_code,413)
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/app.js').status_code,200)


if __name__=='__main__':
    unittest.main()
