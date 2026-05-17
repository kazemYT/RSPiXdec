#!/usr/bin/env python3
"""SAK archive reader/editor for POSTAL RSPiX resources."""
import argparse, io, json, struct
from pathlib import Path

SAK_MAGIC = 0x204B4153
SAK_VERSION = 1

class SakArchive:
    def __init__(self, entries=None):
        self.entries = entries or {}

    @classmethod
    def load(cls, path: Path):
        data = path.read_bytes()
        bio = io.BytesIO(data)
        magic, version = struct.unpack('<II', bio.read(8))
        if magic != SAK_MAGIC or version != SAK_VERSION:
            raise ValueError('Not a SAK v1 archive')
        count = struct.unpack('<H', bio.read(2))[0]
        names, offs = [], []
        for _ in range(count):
            name = bytearray()
            while True:
                b = bio.read(1)
                if b in (b'', b'\0'):
                    break
                name.extend(b)
            names.append(name.decode('utf-8', errors='replace'))
            offs.append(struct.unpack('<I', bio.read(4))[0])
        entries = {}
        for i, n in enumerate(names):
            start = offs[i]
            end = offs[i+1] if i+1 < len(offs) else len(data)
            entries[n] = data[start:end]
        return cls(entries)

    def save(self, path: Path):
        items = list(self.entries.items())
        index_size = sum(len(n.encode()) + 1 + 4 for n, _ in items)
        pos = 10 + index_size
        out = io.BytesIO()
        out.write(struct.pack('<IIH', SAK_MAGIC, SAK_VERSION, len(items)))
        for name, blob in items:
            out.write(name.encode() + b'\0')
            out.write(struct.pack('<I', pos))
            pos += len(blob)
        for _, blob in items:
            out.write(blob)
        path.write_bytes(out.getvalue())


def main():
    p = argparse.ArgumentParser(description='Read/edit .sak archives')
    sub = p.add_subparsers(dest='cmd', required=True)
    l = sub.add_parser('list'); l.add_argument('sak')
    x = sub.add_parser('extract'); x.add_argument('sak'); x.add_argument('outdir')
    b = sub.add_parser('build'); b.add_argument('indir'); b.add_argument('sak')
    j = sub.add_parser('dump-json'); j.add_argument('sak'); j.add_argument('json')
    a = p.parse_args()

    if a.cmd == 'list':
        s = SakArchive.load(Path(a.sak))
        for n, d in s.entries.items():
            print(f'{n}\t{len(d)}')
    elif a.cmd == 'extract':
        s = SakArchive.load(Path(a.sak)); out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
        for n, d in s.entries.items():
            fp = out / n
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(d)
            print(fp)
    elif a.cmd == 'build':
        base = Path(a.indir)
        entries = {}
        for f in base.rglob('*'):
            if f.is_file():
                entries[str(f.relative_to(base)).replace('\\','/')] = f.read_bytes()
        SakArchive(entries).save(Path(a.sak))
        print(f'Wrote {a.sak} ({len(entries)} files)')
    elif a.cmd == 'dump-json':
        s = SakArchive.load(Path(a.sak))
        Path(a.json).write_text(json.dumps({k: len(v) for k,v in s.entries.items()}, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
