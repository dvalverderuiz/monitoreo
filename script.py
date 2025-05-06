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

def snmp_get(ip, oid, community='public', timeout=3):
    """Realiza una consulta SNMP usando snmpget (CLI)"""
    try:
        cmd = [
            'snmpget', '-v2c', 
            '-c', community, 
            '-t', str(timeout),
            '-r', '1',  # 1 reintento
            '-Ovq',     # Solo muestra el valor
            ip, 
            oid
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout + 1
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            console.print(f"[red]Error en {ip} (OID: {oid}): {result.stderr.strip()}[/red]")
            return "N/A"
            
    except subprocess.TimeoutExpired:
        console.print(f"[yellow]Timeout en {ip} (OID: {oid})[/yellow]")
        return "N/A"
    except Exception as e:
        console.print(f"[red]Excepción en {ip}: {str(e)}[/red]")
        return "N/A"

def scan_snmp_hosts(network, community='public'):
    """Escanea hosts respondiendo a SNMP en la red"""
    responsive_hosts = []
    console.print(f"[bold cyan]Escaneando red: {network}...[/bold cyan]")
    
    for ip in network.hosts():
        ip_str = str(ip)
        sys_descr = snmp_get(ip_str, '1.3.6.1.2.1.1.1.0', community)
        
        if sys_descr != "N/A":
            console.print(f"[green]✔ {ip_str} responde a SNMP[/green]")
            responsive_hosts.append(ip_str)
        else:
            console.print(f"[yellow]✖ {ip_str} no responde[/yellow]")
    
    return responsive_hosts

def test_alpine_client():
    """Función específica para probar el cliente Alpine"""
    alpine_ip = "30.20.10.113"
    console.print(f"\n[bold]Probando conexión específica a Alpine ({alpine_ip})[/bold]")
    
    oids_to_test = [
        ('1.3.6.1.2.1.1.1.0', 'System Description'),
        ('1.3.6.1.2.1.1.5.0', 'System Name'),
    ]
    
    for oid, desc in oids_to_test:
        result = snmp_get(alpine_ip, oid)
        console.print(f"{desc} ({oid}): {result}")

def main():
    # Verificar si snmpget está instalado
    try:
        subprocess.run(['snmpget', '-h'], capture_output=True, check=True)
    except FileNotFoundError:
        console.print("[red]Error: snmpget no está instalado. Instala net-snmp:[/red]")
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
    
    # Probar específicamente el Alpine primero
    test_alpine_client()
    
    # Escanear toda la red
    net = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
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
    table.add_column("Sistema Operativo", style="green")
    table.add_column("Nombre", style="yellow")
    table.add_column("Contacto")
    table.add_column("Ubicación")

    for client in clients:
        os_info = snmp_get(client, '1.3.6.1.2.1.1.1.0') or "Desconocido"
        name = snmp_get(client, '1.3.6.1.2.1.1.5.0') or "N/A"
        contact = snmp_get(client, '1.3.6.1.2.1.1.4.0') or "N/A"
        location = snmp_get(client, '1.3.6.1.2.1.1.6.0') or "N/A"
        
        # Acortar información larga de OS
        if len(os_info) > 50:
            os_info = os_info[:47] + "..."
        
        table.add_row(client, os_info, name, contact, location)

    console.print(table)

if __name__ == "__main__":
    main()