"""Freeze one canvas page as an editable HTML plus a checked source/state ZIP."""
import argparse
import copy
import hashlib
import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from portable_export import build_portable

def archive(root, doc_id=None):
    root = Path(root).expanduser().resolve()
    data = json.loads((root / 'data.json').read_text())
    draft = json.loads((root / 'annotations/draft.json').read_text())
    if data['source']['sha256'] != draft.get('source', {}).get('sha256'):
        raise ValueError('Source version differs; reconcile the draft before archiving.')
    if doc_id is None:
        doc_id = data['documents'][draft.get('pageIndex', 0)]['id']
    if not re.fullmatch(r'[A-Za-z0-9-]+', doc_id):
        raise ValueError('Invalid document ID')
    document = next((d for d in data['documents'] if d['id'] == doc_id), None)
    if document is None:
        raise ValueError('Document ID does not exist')
    html = build_portable(root, data, draft, doc_id)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:5]
    output = root / 'archives' / (doc_id + '-' + stamp)
    output.mkdir(parents=True, exist_ok=False)
    (output / (doc_id + '-editable.html')).write_text(html)
    state = copy.deepcopy(draft)
    state['annotations'] = [n for n in state.get('annotations', []) if n.get('docId') == doc_id]
    state['deletedAnnotations'] = [n for n in state.get('deletedAnnotations', [])
                                   if n.get('annotation', {}).get('docId') == doc_id][:2]
    state['undoStates'] = []
    state['redoStates'] = []
    state['pageIndex'] = 0
    (output / 'annotations.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
    (output / 'source-and-page.json').write_text(json.dumps(
        {'source': data['source'], 'documents': [document]}, ensure_ascii=False, indent=2))
    originals = output / 'originals'
    originals.mkdir()
    for image in document.get('images', {}).values():
        url = image['url']
        if url.startswith('data:'):
            continue
        source = (root / url.lstrip('/')).resolve()
        if not source.is_relative_to(root):
            raise ValueError('Image path leaves workspace')
        shutil.copyfile(source, originals / source.name)
        high_res = source.with_name(source.stem + '-export' + source.suffix)
        if high_res.exists():
            shutil.copyfile(high_res, originals / high_res.name)
    (output / '使用说明.txt').write_text(
        '这是单篇画布的冻结快照。可编辑HTML已内嵌原图与批注。\n'
        '编辑旁批后请再次导出HTML，再分享新文件；浏览器自动保存不会写回旧HTML。\n'
        '原件文字仍是图片。实时工作区未被修改。\n')
    manifest = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in output.rglob('*') if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    zip_path = output.with_suffix('.zip')
    with ZipFile(zip_path, 'x', compression=ZIP_DEFLATED) as target:
        for path in output.rglob('*'):
            if path.is_file():
                target.write(path, path.relative_to(output.parent))
    with ZipFile(zip_path) as target:
        if target.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
    for name, digest in manifest.items():
        if hashlib.sha256((output / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Archive checksum failed: ' + name)
    return output, zip_path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--doc-id')
    args = parser.parse_args()
    directory, zipped = archive(args.root, args.doc_id)
    print(json.dumps({'directory': str(directory), 'zip': str(zipped)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
