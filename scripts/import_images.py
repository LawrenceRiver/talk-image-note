"""Import original PNG/JPEG pages without redrawing their visible text."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from vision_ocr import prepare, recognize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--no-ocr', action='store_true', help='Import images without text recognition')
    parser.add_argument('images', nargs='+')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    pages = root / 'pages'

    inputs = []
    for path in args.images:
        source = Path(path).resolve()
        with Image.open(source) as image:
            suffix = {'PNG': '.png', 'JPEG': '.jpg'}.get(image.format)
            if suffix is None:
                raise ValueError('Use PNG or JPEG source images')
            image.verify()
            inputs.append((source, suffix, image.size))

    pages.mkdir(parents=True, exist_ok=True)
    binary = None if args.no_ocr else prepare(root)
    documents = []
    digest = hashlib.sha256()
    for index, (source, suffix, (width, height)) in enumerate(inputs, start=1):
        original = source.read_bytes()
        digest.update(original)
        name = f'p{index}-en{suffix}'
        destination = pages / name
        destination.write_bytes(original)
        lines = []
        if binary is not None:
            try:
                lines = recognize(binary, destination)['lines']
            except (OSError, subprocess.SubprocessError, ValueError) as exc:
                print(f'Page {index}: OCR unavailable: {exc}', file=sys.stderr)

        doc_id = f'IMG{index:02d}'
        paragraphs = []
        boxes = []
        for row, line in enumerate(lines):
            paragraph_id = f'{doc_id}-P{row + 1:03d}'
            text = line['text']
            x, y, w, h = line['box']
            paragraphs.append({'id': paragraph_id, 'text': text, 'source_shape': None,
                               'source_paragraph': row, 'ocr': True})
            boxes.append({'paragraphId': paragraph_id, 'start': 0,
                          'end': len(text.encode('utf-16-le')) // 2,
                          'text': text, 'x': x, 'y': y, 'w': w, 'h': h})
        documents.append({'id': doc_id, 'title': source.stem, 'page': index,
                          'en': paragraphs, 'source_image': str(source),
                          'images': {'en': {'url': '/pages/' + name, 'width': width,
                                            'height': height, 'boxes': boxes}}})

    payload = {
        'source': {'title': 'Original images', 'url': '',
                   'modified_time': datetime.now(timezone.utc).isoformat(),
                   'sha256': digest.hexdigest(), 'kind': 'image-ocr' if binary else 'image'},
        'documents': documents,
        'original_images': True,
    }
    (root / 'data.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                    encoding='utf-8')
    print(f'Imported {len(documents)} unchanged source images' +
          (' (OCR disabled or unavailable)' if binary is None else ''))


if __name__ == '__main__':
    main()
