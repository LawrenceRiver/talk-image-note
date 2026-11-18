import base64
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from bootstrap_workspace import bootstrap
from portable_export import build_portable
from archive_workspace import archive

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=')

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        bootstrap(self.root)
        (self.root / 'pages').mkdir()
        for name in ('p1-en.png', 'p1-zh.png', 'p1-en-export.png', 'p1-zh-export.png'):
            (self.root / 'pages' / name).write_bytes(PNG)
        images = {lang: {'url': '/pages/p1-' + lang + '.png', 'width': 1, 'height': 1, 'boxes': []}
                  for lang in ('en', 'zh')}
        doc = {'id': 'DOC01', 'title': 'Test', 'page': 1, 'en': [{'id': 'P1', 'text': 'Test'}],
               'zh': [{'id': 'P1', 'text': '测试'}], 'images': images}
        self.data = {'source': {'sha256': 'fixture-v1'}, 'documents': [doc]}
        self.draft = {'source': self.data['source'], 'pageIndex': 0,
                      'annotations': [{'id': 'a', 'docId': 'DOC01', 'note': 'Original\n↓\nRevised'}],
                      'deletedAnnotations': [{'annotation': {'docId': 'DOC01', 'id': 'deleted'}}]}
        (self.root / 'annotations').mkdir()
        (self.root / 'data.json').write_text(json.dumps(self.data))
        (self.root / 'annotations/draft.json').write_text(json.dumps(self.draft))

    def test_bootstrap_does_not_replace_user_state_or_custom_ui_without_request(self):
        before = (self.root / 'annotations/draft.json').read_bytes()
        app = self.root / 'app/style.css'
        app.write_text('/* user custom UI */')
        with self.assertRaises(ValueError):
            bootstrap(self.root)
        self.assertEqual(app.read_text(encoding='utf-8'), '/* user custom UI */')
        bootstrap(self.root, refresh=True)
        self.assertEqual((self.root / 'annotations/draft.json').read_bytes(), before)

    def test_portable_embeds_both_source_and_high_res_and_escapes_user_text(self):
        self.draft['annotations'][0]['note'] = '</script><img src=x onerror=alert(1)>'
        before = copy.deepcopy(self.draft)
        html = build_portable(self.root, self.data, self.draft, 'DOC01')
        self.assertNotRegex(html, r'(?:src|href)="/')
        payload = json.loads(re.search(r'<script id="portable-state" type="application/json">(.*?)</script>', html, re.S)[1])
        self.assertEqual(payload['draft']['annotations'][0]['note'], before['annotations'][0]['note'])
        for image in payload['data']['documents'][0]['images'].values():
            for field in ('url', 'exportUrl'):
                self.assertEqual(base64.b64decode(image[field].split(',', 1)[1]), PNG)
        self.assertEqual(self.draft, before)

    def test_archive_is_independent_checksummed_and_does_not_change_live_draft(self):
        before = (self.root / 'annotations/draft.json').read_bytes()
        directory, zipped = archive(self.root)
        self.assertTrue((directory / 'DOC01-editable.html').is_file())
        self.assertEqual((self.root / 'annotations/draft.json').read_bytes(), before)
        state = json.loads((directory / 'annotations.json').read_text(encoding='utf-8'))
        self.assertEqual(len(state['deletedAnnotations']), 1)
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        for name, digest in manifest.items():
            self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), digest)
        with ZipFile(zipped) as package:
            self.assertIsNone(package.testzip())
            self.assertEqual(len(package.namelist()), len(manifest) + 1)
        second, _ = archive(self.root, 'DOC01')
        self.assertNotEqual(second, directory)

    def test_import_without_ocr_and_export_original_jpeg(self):
        original = self.root / 'synthetic.jpg'
        Image.new('RGB', (30, 40), 'orange').save(original)
        importer = Path(__file__).resolve().parents[1] / 'scripts/import_images.py'
        subprocess.run([sys.executable, str(importer), '--root', str(self.root),
                        '--no-ocr', str(original)], check=True, capture_output=True)
        data = json.loads((self.root / 'data.json').read_text(encoding='utf-8'))
        doc, = data['documents']
        image = doc['images']['en']
        self.assertEqual(doc['en'], [])
        self.assertEqual(image['boxes'], [])
        self.assertEqual((image['width'], image['height']), (30, 40))
        self.assertEqual((self.root / image['url'].lstrip('/')).read_bytes(), original.read_bytes())

        html = build_portable(self.root, data, {'annotations': []}, doc['id'])
        payload = json.loads(re.search(r'<script id="portable-state" type="application/json">(.*?)</script>', html, re.S)[1])
        embedded = payload['data']['documents'][0]['images']['en']
        expected = 'data:image/jpeg;base64,' + base64.b64encode(original.read_bytes()).decode('ascii')
        self.assertEqual(embedded['url'], expected)
        self.assertEqual(embedded['exportUrl'], expected)

    def test_stale_source_refuses_archive(self):
        self.draft['source'] = {'sha256': 'older'}
        (self.root / 'annotations/draft.json').write_text(json.dumps(self.draft))
        with self.assertRaises(ValueError):
            archive(self.root)
        self.assertFalse((self.root / 'archives').exists())

if __name__ == '__main__':
    unittest.main()
