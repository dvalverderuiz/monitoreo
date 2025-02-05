<b>APLICACIÓN WEB</b> 

La idea que teniamos sobre alojar una página web en una dirección como tmd.tallerdekirby.com no la vimos factible después de investigar debido a lo siguiente:

- Los comandos de ejecución para redes privadas por ejemplo deberian de hacerse en local de cada usuario, de manera que sacará la información que necesitamos para mostrar desde el navegador web del usuario con phpexec por ejemplo.
  Esto nos limita mucho ya que los navegadores por si solos ya van muy capados.


Por esto creemos que debemos de enfocar el proyecto mas de esta manera que explico adelante:

La aplicación estará ya totalmente creada con docker en un repositorio de github, el usuario (principalmente una empresa que desee monitorear gran volumen de dispositivos) la desplegará en 3 sencillos pasos:
<br>
```
git clone https://github.com/dvalverderuiz/TMD.git
```
```
docker-compose up -d
```
```
localhost:5000
```
Nuestro sistema de monitoreo ya estara configurado en el repositorio de github, el usuario solo deberá de clonarlo y levantarlo. 
<br>
<br>
<br>
<b>DEMO</b>
<br>
<br>
![image](https://github.com/user-attachments/assets/79647d06-6950-4b3c-b9dc-429558ca9d2d)
