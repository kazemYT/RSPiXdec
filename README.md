# RSPiXdec

simple python tool for converting old rspix/postal model formats (`.sop` + `.mesh`) into `.obj`

## what it does

- reads `.sop` file and extracts vertex data (float4 blocks)
- reads `.mesh` file and extracts triangle faces
- builds valid obj model
- exports `.obj` with vertices, normals (dummy), and faces

## supported format

expects files:

model.sop

model.mesh

run with base name:

model


## requirements

- python 3.10+

no external dependencies

## usage

```bash
python convert.py model

this will:

load model.sop
load model.mesh
detect vertex block automatically
build mesh
export model.obj
output

example:

sop offset: 32
vertices:   1248
faces:      2330
saved:      model.obj
how it works
.sop is scanned for valid float4 (x, y, z, w) blocks
vertices are accepted if values are in sane ranges and w ≈ 1.0
.mesh is scanned for uint16 triangle indices
best valid face block is selected automatically
limitations
heuristic-based parsing (no official spec)
may fail on heavily modified files
normals are dummy (0,1,0)
assumes standard postal/rspix layout
errors
not a chan file → wrong input format
could not locate sop vertex block → no valid float4 region found
could not locate mesh faces → face data not detected
file not found → missing .sop or .mesh
