// Test special variables, constants, children(), assert, chr/ord/search

// PI constant
echo("PI:", PI);
echo("pi:", pi);

// $fn special variable
$fn = 32;
echo("$fn:", $fn);

// undef
x = undef;
echo("x is undef:", is_undef(x));

// chr/ord
echo("chr(65):", chr(65));
echo("ord(A):", ord("A"));

// search
haystack = [10, 20, 30, 20, 10];
echo("search 20:", search(20, haystack));

// assert (passing)
assert(1 == 1, "1 should equal 1");
echo("assert passed");

// Module with children
module wrap_it() {
  echo("children count:", $children);
  children();
}

wrap_it() {
  cube([5, 5, 5]);
}

// text (parsed, not built in Blender smoke)
// import handled in parser
