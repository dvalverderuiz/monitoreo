import subprocess
from rich.console import Console
from rich.table import Table
import time
import re
import argparse

console = Console()

def clean_snmp_output(output):
    """Limpia la salida SNMP eliminando tipos y comillas"""
    if not output:
        return "N/A"
    
    if ': ' in output:
        output = output.split(': ', 1)[1]
    
    output = output.replace('\"', '').strip()

    if output.startswith('Timeticks: ('):
        return format_uptime(output)
    
    return output if output else "N/A"

def clean_mac_address(mac):
    """Limpia y formatea correctamente una dirección MAC"""
    # Eliminar todos los caracteres no hexadecimales
    clean_mac = re.sub(r'[^0-9A-Fa-f]', '', mac)
    # Formatear en pares de caracteres separados por :
    if len(clean_mac) == 12:  # Longitud correcta para MAC
        return ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)]).lower()
    return mac  # Si no tiene formato válido, devolver original

def format_uptime(ticks):
    """Formatea los ticks de uptime a días/horas/minutos"""
    try:
        ticks = int(re.search(r'\((\d+)\)', ticks).group(1)) // 100
        days = ticks // (24*3600)
        hours = (ticks % (24*3600)) // 3600
        minutes = (ticks % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    except:
        return ticks

def get_snmp_data(ip, community, oid, timeout=2):
    """Obtiene datos SNMP de forma robusta"""
    try:
        result = subprocess.run(
            ['snmpget', '-v2c', '-c', community, '-t', '1', '-r', '0', ip, oid],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if '=' in output:
                return output.split('=', 1)[1].strip()
        return None
    except:
        return None

def get_system_info(ip, community='public'):
    """Obtiene información básica del sistema"""
    info = {'ip': ip}
    
    try:
        subprocess.run(
            ['ping', '-c', '1', '-W', '1', ip],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except:
        return None
    
    oid_mapping = {
        'System Description': '1.3.6.1.2.1.1.1.0',
        'System Name': '1.3.6.1.2.1.1.5.0',
        'Location': '1.3.6.1.2.1.1.6.0',
        'Uptime': '1.3.6.1.2.1.1.3.0',
        'Contact': '1.3.6.1.2.1.1.4.0'
    }
    
    for desc, oid in oid_mapping.items():
        value = get_snmp_data(ip, community, oid)
        if value:
            info[desc] = clean_snmp_output(value)
    
    return info if len(info) > 1 else None

def get_interfaces_info(ip, community='public'):
    """Obtiene información de interfaces de red con mejor formato"""
    try:
        result = subprocess.run(
            ['snmpwalk', '-v2c', '-c', community, '-t', '1', '-r', '0', ip, '1.3.6.1.2.1.2.2.1'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return None
            
        interfaces = {}
        
        for line in result.stdout.splitlines():
            if '=' not in line:
                continue
                
            oid_part, value_part = line.split('=', 1)
            oid_parts = oid_part.strip().split('.')
            
            if len(oid_parts) < 2:
                continue
                
            oid_type = oid_parts[-2]
            if_index = oid_parts[-1]
            value = value_part.strip()
            
            if if_index not in interfaces:
                interfaces[if_index] = {}
            
            if oid_type == '2':  # Interface Description
                interfaces[if_index]['name'] = clean_snmp_output(value)
            elif oid_type == '6':  # MAC Address
                if 'Hex-STRING:' in value:
                    mac = value.replace('Hex-STRING:', '').strip().upper()
                    interfaces[if_index]['mac'] = clean_mac_address(mac)
            elif oid_type == '8':  # Interface Status
                interfaces[if_index]['status'] = 'Up' if '1' in value else 'Down'
        
        # Filtrar interfaces válidas
        valid_interfaces = {}
        for if_id, if_data in interfaces.items():
            if 'name' in if_data or 'mac' in if_data:
                valid_interfaces[if_id] = if_data
        
        return valid_interfaces if valid_interfaces else None
        
    except Exception as e:
        console.print(f"[red]Error obteniendo interfaces: {str(e)}[/red]")
        return None

def display_devices_table(devices):
    """Muestra la tabla de dispositivos con formato mejorado"""
    if not devices:
        console.print("[red]No se encontraron dispositivos SNMP.[/red]")
        return
    
    table = Table(title="Dispositivos SNMP", header_style="bold blue")
    table.add_column("IP", style="cyan")
    table.add_column("Nombre")
    table.add_column("Descripción")
    table.add_column("Ubicación")
    table.add_column("Uptime")
    table.add_column("Contacto")
    
    for device in devices:
        table.add_row(
            device['ip'],
            device.get('System Name', 'N/A'),
            device.get('System Description', 'N/A')[:50] + ('...' if len(device.get('System Description', '')) > 50 else ''),
            device.get('Location', 'N/A'),
            device.get('Uptime', 'N/A'),
            device.get('Contact', 'N/A')
        )
    
    console.print(table)

def display_interfaces_table(devices):
    """Muestra las interfaces con el formato mejorado"""
    if not devices:
        console.print("[yellow]No hay dispositivos para mostrar interfaces[/yellow]")
        return
    
    for device in devices:
        interfaces = get_interfaces_info(device['ip'])
        if not interfaces:
            console.print(f"[yellow]No se encontraron interfaces para {device.get('System Name', device['ip'])}[/yellow]")
            continue
            
        if_table = Table(title=f"Interfaces de {device.get('System Name', device['ip'])}", 
                        header_style="bold green")
        if_table.add_column("ID")
        if_table.add_column("Nombre")
        if_table.add_column("MAC")
        if_table.add_column("Estado")
        
        for if_id, if_data in sorted(interfaces.items(), key=lambda x: int(x[0])):
            if_table.add_row(
                if_id,
                if_data.get('name', 'N/A'),
                if_data.get('mac', 'N/A'),
                if_data.get('status', 'N/A')
            )
        
        console.print(if_table)

def main():
    parser = argparse.ArgumentParser(description='Monitor de dispositivos SNMP')
    parser.add_argument('modo', choices=['dispositivos', 'interfaces', 'todo'], 
                       help='Qué información mostrar (dispositivos, interfaces, todo)')
    parser.add_argument('--ips', nargs='+', default=['30.20.10.10', '30.20.10.113'],
                       help='Direcciones IP a escanear')
    parser.add_argument('--comunidad', default='public',
                       help='Comunidad SNMP (por defecto: public)')
    
    args = parser.parse_args()
    
    try:
        subprocess.run(['snmpget', '-v'], 
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      timeout=2)
    except:
        console.print("[red]Error: net-snmp no está instalado.[/red]")
        console.print("Instálalo con: sudo apt-get install snmp")
        return
    
    start_time = time.time()
    devices = []
    
    for ip in args.ips:
        device = get_system_info(ip, args.comunidad)
        if device:
            devices.append(device)
    
    elapsed_time = time.time() - start_time
    
    if args.modo == 'dispositivos':
        display_devices_table(devices)
    elif args.modo == 'interfaces':
        display_interfaces_table(devices)
    elif args.modo == 'todo':
        display_devices_table(devices)
        display_interfaces_table(devices)
    
    console.print(f"\nTiempo de escaneo: [bold cyan]{elapsed_time:.2f}[/bold cyan] segundos")

if __name__ == "__main__":
    main()