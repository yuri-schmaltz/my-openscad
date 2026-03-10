x = 3.7;
y = -2.5;
z = 2;
w = 3;

echo("round(3.7):", round(x));
echo("floor(-2.5):", floor(y));
echo("ceil(-2.5):", ceil(y));
echo("pow(2, 3):", pow(z, w));

values = [1.1, 2.9, 3.4, 4.6, 5.1];
rounded = [for (v=values) round(v)];
echo("Rounded list:", rounded);

cube(round(x));
