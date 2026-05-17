#!/usr/bin/env python3
"""Build palette texture + UV-mapped OBJ with one color per polygon (no MTL)."""
import argparse, math
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
    vals = [tuple(raw[i:i+3]) for i in range(0, min(len(raw), 256*3), 3)]
    if len(vals) < 256:
        vals += [(0,0,0)] * (256-len(vals))
    return vals[:256]


def save_ppm(path: Path, pixels, w, h):
    with path.open('wb') as f:
        f.write(f'P6\n{w} {h}\n255\n'.encode())
        for r,g,b in pixels:
            f.write(bytes((r,g,b)))


def build(obj, pal, out_obj, out_tex):
    verts, faces = read_obj(Path(obj))
    palette = load_palette(Path(pal))
    n = len(faces)
    side = max(1, math.ceil(math.sqrt(n)))
    pixels = [(0,0,0)] * (side * side)
    vts = []
    out_faces = []
    for i, (a,b,c) in enumerate(faces):
        color = palette[i % 256]
        pixels[i] = color
        x = i % side
        y = i // side
        u = (x + 0.5) / side
        v = 1.0 - (y + 0.5) / side
        vt_idx = len(vts) + 1
        vts.append((u, v))
        out_faces.append((a,b,c,vt_idx))
    save_ppm(Path(out_tex), pixels, side, side)
    with Path(out_obj).open('w', encoding='utf-8') as f:
        f.write('# one-color-per-polygon obj\n')
        for x,y,z in verts: f.write(f'v {x} {y} {z}\n')
        for u,v in vts: f.write(f'vt {u:.8f} {v:.8f}\n')
        for a,b,c,t in out_faces: f.write(f'f {a}/{t} {b}/{t} {c}/{t}\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('obj')
    ap.add_argument('--pal', default='Bridge.pal')
    ap.add_argument('--out-obj', default='out_uv.obj')
    ap.add_argument('--out-tex', default='out_palette.ppm')
    args = ap.parse_args()
    build(args.obj, args.pal, args.out_obj, args.out_tex)
    print(f'Saved {args.out_obj} and {args.out_tex}')

if __name__ == '__main__':
    main()
