#!/usr/bin/env python3

from pysnmp.hlapi import *
from tabulate import tabulate
import time
import os
import sys

# Dispositivos a escanear
dispositivos = [
    {"ip": "30.20.10.10"},
    {"ip": "30.20.10.113"},
]

# OIDs relevantes
oid_sysdescr = '1.3.6.1.2.1.1.1.0'
oid_sysname = '1.3.6.1.2.1.1.5.0'
oid_syslocation = '1.3.6.1.2.1.1.6.0'
oid_sysuptime = '1.3.6.1.2.1.1.3.0'
oid_syscontact = '1.3.6.1.2.1.1.4.0'
oid_ifdescr = '1.3.6.1.2.1.2.2.1.2'
oid_ifphysaddr = '1.3.6.1.2.1.2.2.1.6'
oid_ifoperstatus = '1.3.6.1.2.1.2.2.1.8'

# Función SNMP GET
def snmp_get(ip, oid):
    for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
        SnmpEngine(),
        CommunityData('public'),
        UdpTransportTarget((ip, 161), timeout=1, retries=0),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    ):
        if errorIndication or errorStatus:
            return None
        for varBind in varBinds:
            return varBind[1]
    return None

# Función SNMP WALK
def snmp_walk(ip, oid):
    resultados = []
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData('public'),
        UdpTransportTarget((ip, 161), timeout=1, retries=0),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False
    ):
        if errorIndication or errorStatus:
            break
        for varBind in varBinds:
            resultados.append((str(varBind[0]), varBind[1]))
    return resultados

# Mostrar tabla de dispositivos
def mostrar_usuarios():
    tabla = []
    for dispositivo in dispositivos:
        ip = dispositivo["ip"]
        print(f"Probando {ip}...")
        response = os.system(f"ping -c 1 -W 1 {ip} > /dev/null 2>&1")
        if response == 0:
            descripcion = snmp_get(ip, oid_sysdescr) or "N/A"
            nombre = snmp_get(ip, oid_sysname) or "N/A"
            ubicacion = snmp_get(ip, oid_syslocation) or "N/A"
            contacto = snmp_get(ip, oid_syscontact) or "N/A"
            uptime = snmp_get(ip, oid_sysuptime)
            uptime_str = f"({uptime}) {int(uptime) // 8640000} days, {(int(uptime) // 100) % 864}:%02d:%02d" % ((int(uptime) // 100) % 60, int(uptime) % 100) if uptime else "N/A"
            tabla.append([ip, nombre, descripcion, ubicacion, uptime_str, contacto])
    print("\n" + tabulate(tabla, headers=["IP", "Nombre", "Descripción", "Ubicación", "Uptime", "Contacto"], tablefmt="grid"))

# Mostrar tabla de interfaces
def mostrar_interfaces():
    for dispositivo in dispositivos:
        ip = dispositivo["ip"]
        nombre_host = snmp_get(ip, oid_sysname) or "N/A"
        print(f"\nInterfaces de {nombre_host}")
        interfaces = snmp_walk(ip, oid_ifdescr)
        macs = snmp_walk(ip, oid_ifphysaddr)
        estados = snmp_walk(ip, oid_ifoperstatus)

        tabla = []
        for i, (oid, nombre) in enumerate(interfaces):
            mac_val = macs[i][1] if i < len(macs) else None
            estado_val = estados[i][1] if i < len(estados) else "N/A"

            # MAC format
            if isinstance(mac_val, OctetString):
                mac = ':'.join(f'{b:02X}' for b in bytes(mac_val))
            else:
                mac = "N/A"

            # Estado interpretable
            estados_map = {"1": "Up", "2": "Down", "3": "Testing"}
            estado = estados_map.get(str(estado_val), "N/A")

            tabla.append([i+1, str(nombre), mac, estado])
        print(tabulate(tabla, headers=["ID", "Nombre", "MAC", "Estado"], tablefmt="grid"))

# MAIN
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 monitoreo/tmd.py [usuarios|interfaces]")
        sys.exit(1)

    inicio = time.time()

    if sys.argv[1] == "usuarios":
        mostrar_usuarios()
    elif sys.argv[1] == "interfaces":
        mostrar_interfaces()
    else:
        print("Opción no válida. Usa: usuarios o interfaces")
        sys.exit(1)

    fin = time.time()
    print(f"\nTiempo de escaneo: {round(fin - inicio, 2)} segundos")
