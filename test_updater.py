"""Fluxo de download, integridade e abertura da versão atualizada."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import updater


class Response(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(data)
        self.url=url

    def geturl(self):
        return self.url


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config={'version':'1.1.0','manifest_url':'https://example.com/update.json'}
        self.exe=b'MZ-version-1.2.0'
        self.manifest={'schema':1,'version':'1.2.0',
                       'url':'https://example.com/ERP_Papeis_de_Marte.exe',
                       'sha256':hashlib.sha256(self.exe).hexdigest(),'size_bytes':len(self.exe)}

    def open(self,url,timeout):
        payload=json.dumps(self.manifest).encode() if url.endswith('.json') else self.exe
        return Response(payload,url)

    def test_download_and_restart_only_newer_verified_exe(self):
        with patch.object(updater.sys,'frozen',True,create=True):
            self.assertEqual(updater.check_and_stage(self.config,self.tmp.name,opener=self.open),'1.2.0')
            path=updater.cached_update(self.config,self.tmp.name)
            self.assertEqual(path.read_bytes(),self.exe)
            with patch.object(updater.subprocess,'Popen') as spawn:
                self.assertTrue(updater.launch_cached(self.config,self.tmp.name))
                self.assertEqual(spawn.call_args.args[0],[str(path)])
                self.assertEqual(spawn.call_args.kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'],'1')
            self.assertIsNone(updater.check_and_stage(self.config,self.tmp.name,opener=self.open))
            path.write_bytes(b'corrompido')
            self.assertIsNone(updater.cached_update(self.config,self.tmp.name))
            self.assertFalse(updater.launch_cached(self.config,self.tmp.name))

    def test_failed_download_preserves_previous_update(self):
        with patch.object(updater.sys,'frozen',True,create=True):
            updater.check_and_stage(self.config,self.tmp.name,opener=self.open)
            self.manifest['version']='1.3.0'
            self.manifest['sha256']='f'*64
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                updater.check_and_stage(self.config,self.tmp.name,opener=self.open)
            self.assertEqual(updater.cached_update(self.config,self.tmp.name).read_bytes(),self.exe)
            self.assertEqual(list((Path(self.tmp.name)/'updates').glob('*.part')),[])

    def test_rejects_insecure_source_and_runs_offline(self):
        with self.assertRaises(ValueError):
            updater.https_url('http://example.com/update.json')
        with patch.object(updater.sys,'frozen',True,create=True):
            self.assertIsNone(updater.check_and_stage({'version':'1.1.0','manifest_url':''},self.tmp.name))
        self.assertFalse(updater.launch_cached(self.config,self.tmp.name))


if __name__=='__main__':
    unittest.main()
