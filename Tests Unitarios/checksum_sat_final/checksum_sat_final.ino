int ChecksumTransmissio(String dades) {
    char frase[100];

    // Convertimos el String a char[]
    dades.toCharArray(frase, 100);

    int suma = 0;
    int caracteres;

    for (int i = 0; frase[i] != '\0'; i++) {
        caracteres = frase[i];
        suma = suma + caracteres;
    }

    int checksum = suma % 256;
    return checksum;
}
