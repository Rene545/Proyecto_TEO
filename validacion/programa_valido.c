int main() {
    int edad = 18;
    int limite = 20;
    int doble = edad * 2;
    if (edad < limite) {
        edad = edad + 1;
    } else {
        edad = edad - 1;
    }
    while (edad < limite) {
        edad = edad + 1;
    }
    return 0;
}
