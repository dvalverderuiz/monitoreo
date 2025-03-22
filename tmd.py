import argparse
import subprocess
from rich.console import Console
from rich.table import Table
from pysnmp.hlapi import *

console = Console()

def obtener_info_snmp(ip, oid):
    """Consulta SNMP en un dispositivo para obtener información específica."""
    iterator = getCmd(
        SnmpEngine(),
        CommunityData("public", mpModel=1),  # Comunidad SNMP
        UdpTransportTarget((ip, 161), timeout=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication:
            return "No responde"
        elif errorStatus:
            return "Error SNMP"
        else:
            for varBind in varBinds:
                return str(varBind[1])
    return "Desconocido"

def listar_dispositivos():
    """Escanea la red en busca de dispositivos y obtiene información SNMP."""
    red = "192.168.1.0/24"
    
    # Escaneo de dispositivos activos en la red
    console.print("🔍 Escaneando la red...", style="yellow")
    resultado = subprocess.run(["nmap", "-sn", red], capture_output=True, text=True)
    ips = [line.split()[-1] for line in resultado.stdout.splitlines() if "Nmap scan report for" in line]

    table = Table(title="Dispositivos en la Red")
    table.add_column("IP", style="cyan")
    table.add_column("MAC", style="magenta")
    table.add_column("Sistema Operativo", style="green")
    table.add_column("Dispositivo", style="blue")

    for ip in ips:
        mac = obtener_info_snmp(ip, "1.3.6.1.2.1.2.2.1.6.2")  # OID para la MAC
        so = obtener_info_snmp(ip, "1.3.6.1.2.1.1.1.0")  # OID para OS
        dispositivo = "PC" if "Linux" in so else "Otro"
        table.add_row(ip, mac, so, dispositivo)

    console.print(table)

parser = argparse.ArgumentParser(description="TMD - Herramienta de Monitoreo de Red")
parser.add_argument("comando", help="Comando a ejecutar (LP, LT, SNMP)")

args = parser.parse_args()

if args.comando.upper() == "LP":
    listar_dispositivos()
else:
    console.print("[red]Comando no válido[/red]")
