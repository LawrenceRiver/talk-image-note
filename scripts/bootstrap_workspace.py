"""Install the canvas UI without touching document images or annotation state."""
import argparse
import shutil
from pathlib import Path

def bootstrap(root, refresh=False):
    root = Path(root).expanduser().resolve()
    assets = Path(__file__).resolve().parents[1] / 'assets' / 'app'
    destination = root / 'app'
    files = [p for p in assets.iterdir() if p.is_file()]
    conflicts = [p.name for p in files if (destination / p.name).exists()
                 and (destination / p.name).read_bytes() != p.read_bytes()]
    if conflicts and not refresh:
        raise ValueError('Existing UI differs; preserve it or explicitly use --refresh-ui: '
                         + ', '.join(conflicts))
    destination.mkdir(parents=True, exist_ok=True)
    for source in files:
        target = destination / source.name
        if not target.exists() or target.read_bytes() != source.read_bytes():
            shutil.copyfile(source, target)
    return destination

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--refresh-ui', action='store_true')
    args = parser.parse_args()
    print(bootstrap(args.root, args.refresh_ui))

if __name__ == '__main__':
    main()
