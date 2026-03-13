// 1000 Objects Exhaustive Test (10x10x10)
for (x = [0 : 9]) {
    for (y = [0 : 9]) {
        for (z = [0 : 9]) {
            translate([x * 20, y * 20, z * 20]) {
                idx = (x + y + z) % 4;
                if (idx == 0) {
                    // Simple Box
                    color([x/10, y/10, z/10]) cube(size=10, center=true);
                } else if (idx == 1) {
                    // Primitive sphere resolving $fn
                    color([1-x/10, y/10, z/10]) sphere(r=6, $fn=16);
                } else if (idx == 2) {
                    // Difference CSG
                    difference() {
                        cylinder(h=12, r=6, center=true, $fn=12);
                        cylinder(h=14, r=4, center=true, $fn=12);
                    }
                } else {
                    // Rotate Extrude
                    rotate_extrude($fn=12)
                        translate([5, 0, 0])
                            square([4, 4], center=true);
                }
            }
        }
    }
}
