APLICACIÓN WEB 

La idea que teniamos sobre alojar una página web en una dirección como tmd.tallerdekirby.com no la vimos factible después de investigar debido a lo siguiente:

- Los comandos de ejecución para redes privadas por ejemplo deberian de hacerse en local de cada usuario, de manera que sacará la información que necesitamos para mostrar desde el navegador web del usuario con phpexec por ejemplo.
  Esto nos limita mucho ya que los navegadores por si solos ya van muy capados.


Por esto creemos que debemos de enfocar el proyecto mas de esta manera que explico adelante:

La aplicación estará ya totalmente creada con docker en un repositorio de github, el usuario (principalmente una empresa que desee monitorear gran volumen de dispositivos) la desplegará en 3 sencillos pasos:

1. git clone (repositorio de la aplicación)
2. docker-compose up -d
3. Entrar a localhost:5000

Nuestro sistema de monitoreo ya estara configurado en el repositorio de github, el usuario solo deberá de clonarlo y levantarlo. Esto levantar 
