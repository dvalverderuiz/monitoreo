import netifaces
import nmap
from pysnmp.hlapi import *
from rich.console import Console
from rich.table import Table
import ipaddress

console = Console()

def get_local_ip():
    for iface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(iface):
            for link in netifaces.ifaddresses(iface)[netifaces.AF_INET]:
                ip = link['addr']
                if ip != '127.0.0.1':
                    return ip, link['netmask']
    return None, None

def scan_network(ip, netmask):
    net = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
    scanner = nmap.PortScanner()
    console.print(f"[bold cyan]Escaneando red: {net} (puerto UDP 161)...[/bold cyan]")
    scanner.scan(hosts=str(net), arguments='-p 161 --open -sU -T4')
    return [host for host in scanner.all_hosts() if scanner[host].has_udp(161)]

def snmp_get(ip, oid, community='public'):
    try:
        iterator = getCmd(SnmpEngine(),
                          CommunityData(community),
                          UdpTransportTarget((ip, 161), timeout=1, retries=0),
                          ContextData(),
                          ObjectType(ObjectIdentity(oid)))
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        if errorIndication or errorStatus:
            return "N/A"
        for varBind in varBinds:
            return str(varBind[1])
    except Exception:
        return "N/A"

def main():
    ip, netmask = get_local_ip()
    if not ip:
        console.print("[red]No se pudo obtener la IP local.[/red]")
        return

    console.print(f"[green]IP local detectada:[/green] {ip}/{netmask}")
    clients = scan_network(ip, netmask)

    if not clients:
        console.print("[yellow]No se encontraron dispositivos SNMP activos.[/yellow]")
        return

    table = Table(title="Resultados SNMP", header_style="bold magenta")
    table.add_column("IP")
    table.add_column("Nombre + OS")
    table.add_column("SysContact")
    table.add_column("Nombre SNMP")
    table.add_column("Ubicación")

    for client in clients:
        os_info = snmp_get(client, '1.3.6.1.2.1.1.1.0')
        contact = snmp_get(client, '1.3.6.1.2.1.1.4.0')
        name = snmp_get(client, '1.3.6.1.2.1.1.5.0')
        location = snmp_get(client, '1.3.6.1.2.1.1.6.0')
        table.add_row(client, os_info, contact, name, location)

    console.print(table)

if __name__ == "__main__":
    main()

