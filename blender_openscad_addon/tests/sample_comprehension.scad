use <sample_lib.scad>;

pts = [for (i=[0:4]) [4 + i * 4, 4 + (i % 2) * 6]];
heights = [for (i=[0:4]) i < 2 ? 5 : 8];

union() {
  base_plate(size=[24, 16, 2]);
  for (i = [0:4]) {
    translate([pts[i][0], pts[i][1], 2])
      peg(r=1.2, h=heights[i]);
  }
}
