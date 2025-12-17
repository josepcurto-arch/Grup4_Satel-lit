# Grup4 Satèl·lit
Repositori amb els arxius del projecte del satèl·lit del grup 4, format per Alba Jarrett, Alex Minghao Tong i Josep Curto, per a l'assignatura de Ciències de la Computació, que inclou les novedoses funcionalitats de l'última versió.

El projecte simula un sistema complet satèl·lit – estació de terra, incloent adquisició de dades de sensors, transmissió, processament, visualització gràfica i càlcul de posició orbital.

 <b> Entrega actual publicada:  </b> Versió 4

 <b> Video Versió 4:  </b> <br> 
 [![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/KC8rA3bHNaE/0.jpg)](https://youtu.be/zalLmHDMvOw)

Foto de grup: <br>
<img src="https://github.com/user-attachments/assets/b6674410-856c-457d-a9b8-a62237ed1c41" alt="IMG_20251216_144434" width="200"/>



 Funcionalitats disponibles:
 - 

| Sàtel·lit | Estació de Terra (Arduino)| Estació de Terra (Python)|
|-----------|---------------------------|--------------------------|
|Lectura de Temperatura, Humitat i Pressió amb un BME280| - | Es mostren les gràfiques dels valors amb les seves mitjanes|
|Lectura de la distància del sensor d'ultrasons, juntament amb el moviment del servo | - | Es mostra una gràfica semi-circular amb les distàncies detectades|
|Es calcula, en funció del voltatge, el percentatge de bateria d'una pila de 9v| - | Es mostra com un `Label`|
|Es calcula una posició simulada del satèl·lit amb una llibreria personalitzada| Es mostra la posició com un groundtrack a una pantalla OLED amb un bitmap per representar la terra | Es mostra la posició com un groundtrack amb una imatge del planeta, en representació Cartogràfica|
|Es coneix la posició real amb un GPS i la llibreria `TinyGPSPlus.h`| Es mostra la posició com un groundtrack a una pantalla OLED amb un bitmap per representar la terra | Es mostra la posició com un groundtrack amb una imatge del planeta, en representació Cartogràfica|
| El sàtel·lit rep commandaments enviats de l'estació de terra i actualitza el seu comportament| Detecta els comandaments i els té en compte abans d'aplicar l'alarma de temps sense rebre informació | Pot enviar comandaments amb els diferents botons i menús incorporats o amb un `Entry` de forma manual|
| El sàtel·lit detecta dades èrronies de les variables i informa a l'estació de terra amb un codi d'error binari i no envia la variable erronia| Detecta el codi d'error i activa l'alarma corresponent | Detecta el codi d'error, actualitza el parseig de dades per no llegir dades innexistents i informa amb el sistema d'alarmes (que es poden filtrar i visualitzar al mateix aplicatiu) i un `Label`|
| Es calcula un checksum en base 256 i s'envia amb la resta de l'String| - | Es torna a calcular el checksum i es compara per asegurar que s'ha rebut l'informació correctament|



Funcionalitats Versió 4:
-
   - S'ha retirat el sensor DHT11, limitat en rang i precisió en les mesures, per un BME280, molt més precís, que ens permet obtenir també la pressió atmosfèrica.
   - GPS integrat per trobar la posició real del sàtel·lit. Es transformen les variables de latitutd i longitiud al sistema ECEF (Earth-Centered Earth-Fixed), el mateix format que s'utilitza per a la posició simulada.
   - Un voltimetre capaç de calcular el percentatge aproximat de bateria restant a una pila de 9v que podria alimentar el sistema.
   - Una pantalla OLED a l'estació de terra que també mostra el groundtrack com un mapa del planeta i un punt representant la posició que s'ha rebut des del satèl·lit.
   - S'ha restructurat des de zero la part gràfica de l'interficie per fer-la més amigable i permetre l'addició de nous botons i gràfiques.
   - S'ha integrat el simulador de posició dins d'una llibreria més fàcil d'integrar i utilitzar al codi, afegint també millores d'eficiència i rendiment.

Estructura del repositori
-
Dins el repositori trobem 3 carpetes que corresponen als Test Unitarios de cada component, el codi d'Arduino del Sàtel·lit, juntament amb la llibreria personalitzada del simulador de posició, i el codi d'Arduino del Receptor. També es troba el codi python de l'estació de terra amb la interficie i l'imatge utilitzada de fons al groundtrack.

Possibles ampliacions
-
   - Actualment la llibreria és limitada en el càlcul d'òrbites amb inclinació i presenta problemes amb simulacions a llarg termini. Es podria optimitzar per millorar aquests punts
   - Tot i que funcional, utilitzar la pantalla OLED juntament amb la comunicació amb el LoRa presenta dificultats degut a les limitacions de la placa Arduino Uno i una de major potència podria permetre afegir més visualitzacions a la pantalla, com era l'idea inicial.
