use <sample_lib.scad>;

function slot_r(n) = let(base = 1 + n * 0.2) base;

plate_w = 18 + 6;

if (plate_w >= 24 && slot_r(2) > 1.3) {
  difference() {
    base_plate(size=[plate_w, 18, 2]);
    translate([8, 9, 0]) cylinder(r=slot_r(2), h=2);
    translate([16, 9, 0]) cylinder(r=slot_r(3), h=2);
  }
} else {
  cube([8, 8, 2]);
}
