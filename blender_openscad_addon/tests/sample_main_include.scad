include "sample_lib.scad";

union() {
  base_plate(size=[24, 24, 2]);
  translate([6, 6, 2]) peg(r=1.5, h=8);
  translate([18, 6, 2]) peg(r=1.5, h=8);
  translate([6, 18, 2]) peg(r=1.5, h=8);
  translate([18, 18, 2]) peg(r=1.5, h=8);
}
