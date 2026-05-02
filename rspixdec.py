#!/usr/bin/env python3
import struct
import sys
from pathlib import Path
HEADER_SIZE = 20
def read_file(path):
    data = Path(path).read_bytes()
    if data[:4] != b"CHAN":
        raise ValueError(f"{path} is not a CHAN file")
    return data
def find_sop_vertices(data, min_vertices=4):
    # ищем блок float4, где w ≈ 1.0
    for start in range(HEADER_SIZE, min(len(data) - 64, 256), 2):
        good = 0
        for i in range(8):
            off = start + i * 16
            if off + 16 > len(data):
                break
            x, y, z, w = struct.unpack_from("<4f", data, off)
            if (
                -100000 < x < 100000 and
                -100000 < y < 100000 and
                -100000 < z < 100000 and
                0.8 < w < 1.2
            ):
                good += 1
        if good >= 6:
            verts = []
            off = start
            while off + 16 <= len(data):
                x, y, z, w = struct.unpack_from("<4f", data, off)
                if not (
                    -100000 < x < 100000 and
                    -100000 < y < 100000 and
                    -100000 < z < 100000
                ):
                    break
                # w должен быть близок к 1
                if not (0.0 < w < 2.0):
                    break
                verts.append((x, y, z))
                off += 16
            return start, verts
    return None, []
def parse_mesh(data, vertex_count):
    # ищем лучший индексный блок
    best_faces = []
    for start in range(HEADER_SIZE, min(len(data), 128), 2):
        faces = []
        for off in range(start, len(data) - 6, 6):
            a, b, c = struct.unpack_from("<3H", data, off)
            if max(a, b, c) >= vertex_count:
                break
            if a == b or b == c or a == c:
                continue
            faces.append((a + 1, b + 1, c + 1))
        if len(faces) > len(best_faces):
            best_faces = faces
    return best_faces
def save_obj(out_path, vertices, faces, scale=1.0):
    with open(out_path, "w") as f:
        f.write("# RSPiX / POSTAL OBJ Export\n")
        for x, y, z in vertices:
            f.write(f"v {x * scale:.6f} {y * scale:.6f} {z * scale:.6f}\n")
        for _ in vertices:
            f.write("vn 0.0 1.0 0.0\n")
        for a, b, c in faces:
            f.write(f"f {a}//{a} {b}//{b} {c}//{c}\n")
def convert(base_name):
    sop_file = base_name + ".sop"
    mesh_file = base_name + ".mesh"
    if not Path(sop_file).exists():
        raise FileNotFoundError(f"File not found: {sop_file}")
    if not Path(mesh_file).exists():
        raise FileNotFoundError(f"File not found: {mesh_file}")
    sop = read_file(sop_file)
    mesh = read_file(mesh_file)
    sop_offset, vertices = find_sop_vertices(sop)
    if not vertices:
        raise RuntimeError("Could not locate SOP vertex block")
    faces = parse_mesh(mesh, len(vertices))
    if not faces:
        raise RuntimeError("Could not locate mesh faces")
    out = base_name + ".obj"
    save_obj(out, vertices, faces)
    print(f"SOP offset: {sop_offset}")
    print(f"Vertices:   {len(vertices)}")
    print(f"Faces:      {len(faces)}")
    print(f"Saved:      {out}")
def print_usage():
    print("Usage:")
    print("  python rspixdec.py <filename>")
    print("  python rspixdec.py woman1")
    print("\nThis will look for woman1.sop and woman1.mesh files")
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Please provide the base filename (without extension)")
        print_usage()
        sys.exit(1)
    base_name = sys.argv[1]
    try:
        convert(base_name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
