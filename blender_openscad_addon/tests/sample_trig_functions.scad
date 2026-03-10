a = 4;
b = 0;

echo("sqrt(4):", sqrt(a));
echo("sin(0):", sin(b));
echo("cos(0):", cos(b));
echo("tan(0):", tan(b));

pi_half = 1.5707963;
echo("sin(pi/2):", sin(pi_half));
echo("cos(pi/2):", cos(pi_half));

values = [1, 4, 9, 16];
roots = [for (v=values) sqrt(v)];
echo("Square roots:", roots);

random_list = rands(0, 10, 3);
echo("Random numbers (0-10):", random_list);

cube(1);
