import subprocess
from rich.console import Console
from rich.table import Table
import time
import re

console = Console()

def clean_snmp_output(output):
    """Limpia la salida SNMP eliminando tipos y comillas"""
    # Elimina 'STRING: ', 'Hex-STRING: ', etc.
    if ': ' in output:
        output = output.split(': ', 1)[1]
    
    # Elimina comillas dobles y escapadas
    output = output.replace('\"', '').strip()
    
    # Caso especial para Timeticks
    if output.startswith('Timeticks: ('):
        return format_uptime(output)
    
    return output

def format_uptime(ticks):
    """Formatea los ticks de uptime a días/horas/minutos"""
    try:
        # Extrae el número entre paréntesis
        ticks = int(re.search(r'\((\d+)\)', ticks).group(1)) // 100  # Convertir a segundos
        days = ticks // (24*3600)
        hours = (ticks % (24*3600)) // 3600
        minutes = (ticks % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    except:
        return ticks

def snmp_scan(target_ips, community='public'):
    """Escanea direcciones IP específicas con SNMP"""
    results = []
    
    for ip in target_ips:
        console.print(f"\n[bold]Probando {ip}...[/bold]")
        
        # Primero probamos ping
        try:
            subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            console.print(f"[green]✔ {ip} responde a ping[/green]")
        except:
            console.print(f"[yellow]✖ {ip} no responde a ping[/yellow]")
            continue
        
        # Información básica del sistema
        base_oids = [
            ('1.3.6.1.2.1.1.1.0', 'System Description'),
            ('1.3.6.1.2.1.1.5.0', 'System Name'),
            ('1.3.6.1.2.1.1.6.0', 'Location'),
            ('1.3.6.1.2.1.1.3.0', 'Uptime'),
            ('1.3.6.1.2.1.1.4.0', 'Contact'),
        ]
        
        # Información de interfaces de red
        interface_oids = [
            ('1.3.6.1.2.1.2.2.1.6', 'MAC Address'),
            ('1.3.6.1.2.1.2.2.1.2', 'Interface Description'),
            ('1.3.6.1.2.1.2.2.1.8', 'Interface Status'),
        ]
        
        device_info = {'ip': ip}
        
        # Obtener información básica
        for oid, desc in base_oids:
            try:
                result = subprocess.run(
                    ['snmpget', '-v2c', '-c', community, '-t', '1', '-r', '0', ip, oid],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if '=' in output:
                        value = output.split('=', 1)[1].strip()
                        device_info[desc] = clean_snmp_output(value)
                        console.print(f"[green]  {desc}: {device_info[desc]}[/green]")
            except Exception as e:
                console.print(f"[red]  Error en {desc}: {str(e)}[/red]")
        
        # Obtener información de interfaces
        try:
            result = subprocess.run(
                ['snmpwalk', '-v2c', '-c', community, '-t', '1', '-r', '0', ip, '1.3.6.1.2.1.2.2.1'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                interfaces = {}
                
                for line in result.stdout.splitlines():
                    if '=' not in line:
                        continue
                    
                    oid_part, value_part = line.split('=', 1)
                    oid_parts = oid_part.strip().split('.')
                    if_index = oid_parts[-2]
                    oid_type = oid_parts[-1]
                    
                    value = value_part.strip()
                    
                    if if_index not in interfaces:
                        interfaces[if_index] = {}
                    
                    if oid_type == '2':  # Interface Description
                        interfaces[if_index]['name'] = clean_snmp_output(value)
                    elif oid_type == '6':  # MAC Address
                        if 'Hex-STRING:' in value:
                            mac = value.replace('Hex-STRING:', '').strip().upper()
                            mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
                            interfaces[if_index]['mac'] = mac
                    elif oid_type == '8':  # Interface Status
                        interfaces[if_index]['status'] = 'Up' if '1' in value else 'Down'
                
                device_info['Interfaces'] = interfaces
                
        except Exception as e:
            console.print(f"[red]  Error obteniendo interfaces: {str(e)}[/red]")
        
        if len(device_info) > 1:
            results.append(device_info)
    
    return results

def main():
    # Verificar instalación de snmpget
    try:
        subprocess.run(['snmpget', '-v'], 
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      timeout=2)
    except:
        console.print("[red]Error: net-snmp no está instalado.[/red]")
        console.print("Instálalo con: sudo apt-get install snmp")
        return

    target_ips = [
        '30.20.10.10',   # Tu servidor
        '30.20.10.113'   # Tu cliente Alpine
    ]
    
    start_time = time.time()
    devices = snmp_scan(target_ips)
    elapsed_time = time.time() - start_time
    
    if devices:
        # Tabla principal
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
        
        # Tabla de interfaces para cada dispositivo
        for device in devices:
            if 'Interfaces' in device and device['Interfaces']:
                if_table = Table(title=f"Interfaces de {device.get('System Name', device['ip'])}", 
                               header_style="bold green")
                if_table.add_column("ID")
                if_table.add_column("Nombre")
                if_table.add_column("MAC")
                if_table.add_column("Estado")
                
                for if_id, if_data in sorted(device['Interfaces'].items(), key=lambda x: int(x[0])):
                    if_table.add_row(
                        if_id,
                        if_data.get('name', 'N/A'),
                        if_data.get('mac', 'N/A'),
                        if_data.get('status', 'N/A')
                    )
                
                console.print(if_table)
            else:
                console.print(f"[yellow]No se encontraron interfaces para {device.get('System Name', device['ip'])}[/yellow]")
    else:
        console.print("[red]No se encontraron dispositivos SNMP.[/red]")
    
    console.print(f"\nTiempo de escaneo: {elapsed_time:.2f} segundos")

if __name__ == "__main__":
    main()