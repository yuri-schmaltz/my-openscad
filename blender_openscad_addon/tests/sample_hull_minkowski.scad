union() {
  hull() {
    translate([0, 0, 0]) sphere(r=1);
    translate([4, 0, 0]) sphere(r=1);
  }
  minkowski() {
    translate([10, 0, 0]) cube([2, 2, 2]);
    sphere(r=0.5);
  }
}
