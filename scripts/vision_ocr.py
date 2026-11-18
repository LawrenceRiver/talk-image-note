"""Optional macOS Vision backend shared by import and handwriting."""

import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def prepare(root):
    if sys.platform != 'darwin':
        return None

    source = Path(__file__).with_name('ocr.swift')
    runtime = root / '.runtime'
    binary = runtime / 'ink-ocr'
    temporary = runtime / ('ink-ocr-' + uuid4().hex)
    try:
        runtime.mkdir(exist_ok=True)
        if not binary.is_file() or binary.stat().st_mtime < source.stat().st_mtime:
            subprocess.run(['swiftc', str(source), '-O', '-o', str(temporary)],
                           check=True, timeout=90, capture_output=True)
            temporary.replace(binary)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f'Vision OCR unavailable: {exc}', file=sys.stderr)
        return None
    finally:
        temporary.unlink(missing_ok=True)
    return binary


def recognize(binary, image):
    result = subprocess.run([str(binary), str(image)], check=True, timeout=30,
                            capture_output=True, encoding='utf-8')
    return json.loads(result.stdout)
