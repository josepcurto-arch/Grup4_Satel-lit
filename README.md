# Grup4_Satèl·lit
Repositori amb els arxius del projecte del satèl·lit del grup 4, format per Alba Jarrett, Alex Minghao Tong i Josep Curto, per a l'assignatura de Ciències de la Computació.


 <b> Entrega actual publicada:  </b> Versió 3 

 <b> Video Versió 3:  </b> <br> 
 [![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/KC8rA3bHNaE/0.jpg)](https://www.youtube.com/watch?v=Ry7vCwv50jE)


 Funcionalitats disponibles:
 - 
   - El satèl·lit llegeix i envia correctament les dades de Temperatura i Humitat del DHT11 i la Distància del sensor d'ultrasons, que es mou amb l'ajuda del servo.
   - L'estació de terra rep les dades correctament i les mostra a una interficie gràfica juntament amb les mitjanes. Cada valor es mostra en una gràfica adient al que representa.
   - El sàtel·lit calcula la seva posició utilitzant una llibreria personalitzada i l'envia perquè es mostri a un groundtrack a l'estació de terra.
   - A l'interficie, l'usuari pot parar i reanudar la transmissió de dades, així com veure-les amb gràfiques que mostren els últims 30 segons. També pot decidir si les mitjanes es calculen a terra o al sàtel·lit.
   - L'estació de terra dectecta dades errònies de temperatura, humitat, distància o si no s'ha rebut informació durant massa temps. També informa del problema amb un missatge al programa Python i emet un so a l'Arduino receptor per informar de tal situació.
   - L'usuari disposa d'un Menú de Configuració per ajustar els valors màxims i mínims de temperatura i humitat, així com el temps entre cada enviament de dades.
   - El sistema utilitza el checksum per validar les dades rebudes. En cas que no siguin correctes, no es mostren a les gràfiques i s'informa de tal situació.

