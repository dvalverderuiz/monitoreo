#!/bin/bash


if [[ $EUID -ne 0 ]]; then
   echo "Este script debe ejecutarse como root" 
   exit 1
fi

# Red a escanear (ajusta según tu red)
RED="192.168.1.0/24"
USUARIO="usuario_remoto"   # usuario SSH
CLAVE="tu_contraseña"

# Escanea la red en busca de dispositivos activos
echo "🔍 Escaneando dispositivos en la red..."
IPS=$(nmap -sn $RED | grep "Nmap scan report for" | awk '{print $5}')

# Recorre cada IP encontrada
for IP in $IPS; do
    echo "⚙️ Configurando SNMP en $IP..."
    
    sshpass -p "$CLAVE" ssh -o StrictHostKeyChecking=no "$USUARIO@$IP" << 'EOF'
    sudo apt update && sudo apt install -y snmpd snmp
    sudo bash -c 'echo "agentAddress udp:161" > /etc/snmp/snmpd.conf'
    sudo bash -c 'echo "rocommunity public 192.168.1.0/24" >> /etc/snmp/snmpd.conf'
    sudo systemctl restart snmpd
    sudo systemctl enable snmpd
EOF

    echo "✅ SNMP configurado en $IP"
done

echo "🚀 Configuración remota de SNMP completada."
