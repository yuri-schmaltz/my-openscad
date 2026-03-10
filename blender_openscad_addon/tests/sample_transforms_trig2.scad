// test mirror, resize, multmatrix, offset, projection and new math functions

// sign, atan, atan2, asin, acos, log, exp, is_num, is_bool, is_string, is_list
echo("sign(-5):", sign(-5));
echo("sign(0):", sign(0));
echo("sign(3):", sign(3));
echo("atan(1):", atan(1));
echo("atan2(1, 1):", atan2(1, 1));
echo("asin(0.5):", asin(0.5));
echo("acos(0.5):", acos(0.5));
echo("log(100):", log(100));
echo("exp(0):", exp(0));
echo("is_num(3.14):", is_num(3.14));
echo("is_bool(true):", is_bool(true));
echo("is_string(\"hello\"):", is_string("hello"));
echo("is_list([1,2]):", is_list([1, 2]));

// mirror
mirror([1, 0, 0]) {
  cube([5, 5, 5]);
}

// resize
resize([10, 10, 10]) {
  sphere(r=5);
}

// offset (2D)
offset(r=2) {
  square([10, 10]);
}

// projection
projection(cut=false) {
  cube([5, 5, 5]);
}
