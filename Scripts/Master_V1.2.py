
import Rhino.Geometry as rg
import math
import os
import csv

# ==========================================
# POW 01 - PARAMETRIC TOWER
# MASTER SCRIPT V1.2
# RHINO 8 + GRASSHOPPER + PYTHON 3
# LIVE PARAMETRIC SYNCHRONIZATION
# ==========================================

# 01. INPUT VALIDATION

if x is None:
    raise ValueError("Connect footprint to x.")

if y is None:
    raise ValueError("Connect Floor Count to y.")

if h is None:
    raise ValueError("Connect Floor Height to h.")

if r is None:
    raise ValueError("Connect Rotation Angle to r.")

# 02. LIVE DESIGN PARAMETERS

floor_count = int(y)
floor_height = float(h)
rotation_angle = float(r)

if floor_count < 1:
    raise ValueError("Floor Count must be positive.")

if floor_height <= 0:
    raise ValueError("Floor Height must be positive.")

# 03. FIXED DESIGN PARAMETERS

width = 20.0
length = 30.0

slab_thickness = 0.30
column_radius = 0.40
beam_radius = 0.25
roof_thickness = 0.30

core_width = 8.0
core_length = 12.0

export_csv = False

# 04. FOOTPRINT SYNCHRONIZATION

amp = rg.AreaMassProperties.Compute(x)

if amp is None:
    raise ValueError(
        "Invalid footprint. Use a closed planar curve."
    )

center = amp.Centroid

center_x = center.X
center_y = center.Y
base_z = center.Z

height = floor_count * floor_height

# 05. INITIALIZE GEOMETRY

columns = []
beams = []
roof = []
levels = []

column_volume = 0.0
beam_volume = 0.0

# 06. GENERATE ROTATED FLOOR CORNERS

for i in range(floor_count + 1):

    angle = math.radians(i * rotation_angle)
    z = base_z + i * floor_height

    corners = [
        (-width / 2, -length / 2),
        (width / 2, -length / 2),
        (width / 2, length / 2),
        (-width / 2, length / 2)
    ]

    points = []

    for px, py in corners:

        rx = (
            px * math.cos(angle)
            - py * math.sin(angle)
        )

        ry = (
            px * math.sin(angle)
            + py * math.cos(angle)
        )

        points.append(
            rg.Point3d(
                center_x + rx,
                center_y + ry,
                z
            )
        )

    levels.append(points)

# 07. SOLID MEMBER GENERATOR

def create_member(p1, p2, radius):

    direction = p2 - p1
    member_length = direction.Length

    if member_length <= 0.000001:
        return None

    plane = rg.Plane(p1, direction)
    circle = rg.Circle(plane, radius)

    cylinder = rg.Cylinder(
        circle,
        member_length
    )

    return cylinder.ToBrep(True, True)

# 08. STRUCTURAL COLUMNS

for i in range(floor_count):

    for j in range(4):

        p1 = levels[i][j]
        p2 = levels[i + 1][j]

        member = create_member(
            p1,
            p2,
            column_radius
        )

        if member is not None:

            columns.append(member)

            column_volume += (
                math.pi
                * column_radius ** 2
                * p1.DistanceTo(p2)
            )

# 09. PERIMETER BEAMS

for i in range(1, floor_count + 1):

    for j in range(4):

        p1 = levels[i][j]
        p2 = levels[i][(j + 1) % 4]

        member = create_member(
            p1,
            p2,
            beam_radius
        )

        if member is not None:

            beams.append(member)

            beam_volume += (
                math.pi
                * beam_radius ** 2
                * p1.DistanceTo(p2)
            )

# 10. ROOF SLAB

roof_points = list(levels[-1])
roof_points.append(roof_points[0])

roof_curve = rg.PolylineCurve(roof_points)

roof_surface = rg.Surface.CreateExtrusion(
    roof_curve,
    rg.Vector3d(0, 0, -roof_thickness)
)

if roof_surface is not None:

    roof_brep = roof_surface.ToBrep()

    roof_solid = roof_brep.CapPlanarHoles(
        0.001
    )

    if roof_solid is not None:
        roof.append(roof_solid)

# 11. QUANTITY EXTRACTION

floor_area = width * length
gfa = floor_area * floor_count

slab_volume = gfa * slab_thickness

roof_volume = 0.0

for item in roof:

    volume = rg.VolumeMassProperties.Compute(
        item
    )

    if volume is not None:
        roof_volume += abs(volume.Volume)

total_volume = (
    slab_volume
    + column_volume
    + beam_volume
    + roof_volume
)

# 12. DESIGN PERFORMANCE METRICS

total_twist = floor_count * rotation_angle

core_area = core_width * core_length

core_ratio = (
    core_area / floor_area * 100
)

net_area_proxy = (
    gfa - core_area * floor_count
)

total_elements = (
    len(columns)
    + len(beams)
    + len(roof)
)

metrics = [
    ("Building Width", width, "m"),
    ("Building Length", length, "m"),
    ("Building Height", height, "m"),
    ("Floor Count", floor_count, "nos"),
    ("Floor Height", floor_height, "m"),
    ("Rotation Per Floor", rotation_angle, "deg"),
    ("Total Twist", total_twist, "deg"),
    ("Floor Area", floor_area, "m2"),
    ("Gross Floor Area", gfa, "m2"),
    ("Core Area", core_area, "m2"),
    ("Core Area Ratio", core_ratio, "%"),
    ("Area Excluding Core", net_area_proxy, "m2"),
    ("Column Segments", len(columns), "nos"),
    ("Beam Segments", len(beams), "nos"),
    ("Roof Slabs", len(roof), "nos"),
    ("Total Generated Elements", total_elements, "nos"),
    ("Floor Slab Volume", slab_volume, "m3"),
    ("Column Volume", column_volume, "m3"),
    ("Beam Volume", beam_volume, "m3"),
    ("Roof Volume", roof_volume, "m3"),
    ("Gross Member Volume", total_volume, "m3")
]

# 13. CSV DATA EXPORT

export_path = os.path.join(
    os.path.expanduser("~"),
    "PoW01_Quantity_Report.csv"
)

if export_csv:

    with open(
        export_path,
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            ["Parameter", "Value", "Unit"]
        )

        for name, value, unit in metrics:

            writer.writerow(
                [name, round(value, 3), unit]
            )

# 14. LIVE PERFORMANCE REPORT

print("=" * 45)
print("POW 01 - PARAMETRIC TOWER")
print("MASTER SCRIPT V1.2")
print("=" * 45)

print("LIVE PARAMETRIC INPUTS")
print("Floor Count: {}".format(floor_count))
print("Floor Height: {:.2f} m".format(floor_height))
print("Rotation Angle: {:.2f} deg".format(rotation_angle))

print("=" * 45)

print("CENTROID SYNCHRONIZED")
print("Center X: {:.3f}".format(center_x))
print("Center Y: {:.3f}".format(center_y))
print("Base Z: {:.3f}".format(base_z))

print("=" * 45)
print("DESIGN PERFORMANCE REPORT")
print("=" * 45)

for name, value, unit in metrics:

    print(
        "{}: {:.2f} {}".format(
            name,
            value,
            unit
        )
    )

if export_csv:
    print("CSV Export: " + export_path)

print("=" * 45)
print("LIVE PARAMETRIC SYNCHRONIZATION ACTIVE")
print("CONCEPTUAL STRUCTURE GENERATED")
print("=" * 45)

# 15. GRASSHOPPER OUTPUT

a = columns + beams + roof
