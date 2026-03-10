use <sample_lib.scad>;

function pick_h(i) = i % 2 == 0 ? 8 : 5;
pts = [[4,4], [12,4], [20,4], [8,12], [16,12]];

union() {
  base_plate(size=[24, 16, 2]);
  for (i = [0:4]) {
    translate([pts[i][0], pts[i][1], 2])
      peg(r=1 + i * 0.1, h=pick_h(i));
  }
}
