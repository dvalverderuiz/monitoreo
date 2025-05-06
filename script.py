import netifaces
import subprocess
import ipaddress
from rich.console import Console
from rich.table import Table
import time

console = Console()

def get_local_ip():
    """Obtiene la IP y máscara de red local"""
    for iface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(iface):
            for link in netifaces.ifaddresses(iface)[netifaces.AF_INET]:
                ip = link['addr']
                if ip != '127.0.0.1':
                    return ip, link['netmask']
    return None, None

def snmp_walk(ip, oid, community='public', timeout=3):
    """Realiza un walk SNMP usando snmpwalk (CLI)"""
    try:
        cmd = [
            'snmpwalk', '-v2c', 
            '-c', community, 
            '-t', str(timeout),
            '-r', '1',  # 1 reintento
            '-Oq',      # Salida más legible
            ip, 
            oid
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout + 2
        )
        
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            console.print(f"[red]Error en {ip} (OID: {oid}): {result.stderr.strip()}[/red]")
            return []
            
    except subprocess.TimeoutExpired:
        console.print(f"[yellow]Timeout en {ip} (OID: {oid})[/yellow]")
        return []
    except Exception as e:
        console.print(f"[red]Excepción en {ip}: {str(e)}[/red]")
        return []

def scan_snmp_hosts(network, community='public'):
    """Escanea hosts respondiendo a SNMP en la red"""
    responsive_hosts = []
    console.print(f"[bold cyan]Escaneando red: {network}...[/bold cyan]")
    
    for ip in network.hosts():
        ip_str = str(ip)
        # Probamos con un OID básico para detectar si responde
        sys_name = snmp_walk(ip_str, '1.3.6.1.2.1.1.5.0', community)
        
        if sys_name:
            console.print(f"[green]✔ {ip_str} responde a SNMP[/green]")
            responsive_hosts.append(ip_str)
        else:
            console.print(f"[yellow]✖ {ip_str} no responde[/yellow]")
    
    return responsive_hosts

def get_system_info(ip, community='public'):
    """Obtiene información del sistema usando snmpwalk"""
    info = {
        'os': "N/A",
        'name': "N/A",
        'contact': "N/A",
        'location': "N/A",
        'interfaces': []
    }
    
    # Información básica del sistema
    sys_descr = snmp_walk(ip, '1.3.6.1.2.1.1.1.0', community)
    if sys_descr:
        info['os'] = sys_descr[0].split('"')[1] if '"' in sys_descr[0] else sys_descr[0]
    
    sys_name = snmp_walk(ip, '1.3.6.1.2.1.1.5.0', community)
    if sys_name:
        info['name'] = sys_name[0].split('"')[1] if '"' in sys_name[0] else sys_name[0]
    
    sys_contact = snmp_walk(ip, '1.3.6.1.2.1.1.4.0', community)
    if sys_contact:
        info['contact'] = sys_contact[0].split('"')[1] if '"' in sys_contact[0] else sys_contact[0]
    
    sys_location = snmp_walk(ip, '1.3.6.1.2.1.1.6.0', community)
    if sys_location:
        info['location'] = sys_location[0].split('"')[1] if '"' in sys_location[0] else sys_location[0]
    
    # Interfaces de red (ejemplo de información adicional)
    if_indexes = snmp_walk(ip, '1.3.6.1.2.1.2.2.1.1', community)
    if if_indexes:
        info['interfaces'] = [idx.split()[-1] for idx in if_indexes]
    
    return info

def main():
    # Verificar si snmpwalk está instalado
    try:
        subprocess.run(['snmpwalk', '-v'], 
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      timeout=5)
    except Exception as e:
        console.print("[red]Error: net-snmp no está instalado correctamente.[/red]")
        console.print("Instala las herramientas SNMP con:")
        console.print("  Debian/Ubuntu: sudo apt-get install snmp")
        console.print("  Alpine: apk add net-snmp-tools")
        console.print("  CentOS/RHEL: sudo yum install net-snmp-utils")
        return

    # Obtener IP local
    ip, netmask = get_local_ip()
    if not ip:
        console.print("[red]No se pudo obtener la IP local.[/red]")
        return

    console.print(f"[green]IP local detectada:[/green] {ip}/{netmask}")
    net = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
    
    # Escanear
    start_time = time.time()
    clients = scan_snmp_hosts(net)
    scan_duration = time.time() - start_time
    
    if not clients:
        console.print("[yellow]No se encontraron dispositivos SNMP activos.[/yellow]")
        return

    # Mostrar resultados
    console.print(f"\n[bold]Escaneo completado en {scan_duration:.2f} segundos[/bold]")
    table = Table(title="Dispositivos SNMP encontrados", header_style="bold magenta")
    table.add_column("IP", style="cyan")
    table.add_column("Nombre", style="yellow")
    table.add_column("Sistema", style="green")
    table.add_column("Interfaces")
    table.add_column("Ubicación")

    for client in clients:
        info = get_system_info(client)
        
        # Acortar información larga
        os_info = info['os'][:50] + "..." if len(info['os']) > 50 else info['os']
        interfaces = ", ".join(info['interfaces'][:3]) + ("..." if len(info['interfaces']) > 3 else "")
        
        table.add_row(
            client,
            info['name'],
            os_info,
            interfaces,
            info['location']
        )

    console.print(table)

    # Mostrar información detallada para el Alpine específicamente
    alpine_ip = "30.20.10.113"
    if alpine_ip in clients:
        console.print(f"\n[bold]Información detallada para Alpine ({alpine_ip}):[/bold]")
        alpine_info = get_system_info(alpine_ip)
        for key, value in alpine_info.items():
            if key != 'interfaces':
                console.print(f"{key.capitalize():<10}: {value}")
        
        if alpine_info['interfaces']:
            console.print("\nInterfaces de red:")
            for interface in alpine_info['interfaces']:
                if_desc = snmp_walk(alpine_ip, f'1.3.6.1.2.1.2.2.1.2.{interface}')
                if if_desc:
                    console.print(f" - {interface}: {if_desc[0].split()[-1]}")

if __name__ == "__main__":
    main()