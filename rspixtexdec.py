#!/usr/bin/env python3
"""Build palette texture + UV-mapped OBJ with one color per polygon (no MTL)."""
import argparse
import math
import struct
import zlib
from pathlib import Path


def read_obj(path: Path):
    verts, faces = [], []
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.startswith('v '):
            _, x, y, z = line.split()[:4]
            verts.append((float(x), float(y), float(z)))
        elif line.startswith('f '):
            ids = []
            for part in line.split()[1:]:
                ids.append(int(part.split('/')[0]))
            if len(ids) == 3:
                faces.append(tuple(ids))
    return verts, faces


def load_palette(path: Path):
    raw = path.read_bytes()
    vals = [tuple(raw[i:i + 3]) for i in range(0, min(len(raw), 256 * 3), 3)]
    if len(vals) < 256:
        vals += [(0, 0, 0)] * (256 - len(vals))
    return vals[:256]


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack('>I', len(data))
        + tag
        + data
        + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def save_png(path: Path, pixels, w, h):
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0
        row = pixels[y * w:(y + 1) * w]
        for r, g, b in row:
            raw.extend((r, g, b))
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=9)
    sig = b'\x89PNG\r\n\x1a\n'
    png = sig + _png_chunk(b'IHDR', ihdr) + _png_chunk(b'IDAT', idat) + _png_chunk(b'IEND', b'')
    path.write_bytes(png)


def build(obj, pal, out_obj, out_tex):
    verts, faces = read_obj(Path(obj))
    palette = load_palette(Path(pal))
    n = len(faces)
    side = max(1, math.ceil(math.sqrt(n)))
    pixels = [(0, 0, 0)] * (side * side)
    vts = []
    out_faces = []
    for i, (a, b, c) in enumerate(faces):
        color = palette[i % 256]
        pixels[i] = color
        x = i % side
        y = i // side
        u = (x + 0.5) / side
        v = 1.0 - (y + 0.5) / side
        vt_idx = len(vts) + 1
        vts.append((u, v))
        out_faces.append((a, b, c, vt_idx))
    save_png(Path(out_tex), pixels, side, side)
    with Path(out_obj).open('w', encoding='utf-8') as f:
        f.write('# one-color-per-polygon obj\n')
        for x, y, z in verts:
            f.write(f'v {x} {y} {z}\n')
        for u, v in vts:
            f.write(f'vt {u:.8f} {v:.8f}\n')
        for a, b, c, t in out_faces:
            f.write(f'f {a}/{t} {b}/{t} {c}/{t}\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('obj')
    ap.add_argument('--pal', default='Bridge.pal')
    ap.add_argument('--out-obj', default='out_uv.obj')
    ap.add_argument('--out-tex', default='out_palette.png')
    args = ap.parse_args()
    build(args.obj, args.pal, args.out_obj, args.out_tex)
    print(f'Saved {args.out_obj} and {args.out_tex}')


if __name__ == '__main__':
    main()
