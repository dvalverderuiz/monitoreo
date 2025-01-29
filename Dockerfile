# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de la aplicación
COPY ./app /app

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Instalar herramientas de red (arp-scan y nmap)
RUN apt-get update && apt-get install -y \
    arp-scan \
    nmap \
    && rm -rf /var/lib/apt/lists/*

# Exponer el puerto 5000 para la versión web
EXPOSE 5000

# Comando por defecto (versión CLI)
CMD ["python", "cli/tmd_cli.py"]
