use <sample_lib.scad>;

difference() {
  base_plate(size=[30, 20, 3]);
  translate([10, 10, 0]) cylinder(r=3, h=3);
  translate([20, 10, 0]) cylinder(r=3, h=3);
}
