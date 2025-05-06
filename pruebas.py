import subprocess
from rich.console import Console
from rich.table import Table
import time

console = Console()

def snmp_scan(target_ips, community='public'):
    """Escanea direcciones IP específicas con SNMP"""
    results = []
    
    for ip in target_ips:
        console.print(f"\n[bold]Probando {ip}...[/bold]")
        
        # Primero probamos ping para ver si el host está vivo
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
        
        # Luego probamos SNMP
        oids = [
            ('1.3.6.1.2.1.1.1.0', 'System Description'),
            ('1.3.6.1.2.1.1.5.0', 'System Name'),
            ('1.3.6.1.2.1.1.6.0', 'Location')
        ]
        
        device_info = {'ip': ip}
        
        for oid, desc in oids:
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
                        value = output.split('=')[1].strip()
                        device_info[desc] = value
                        console.print(f"[green]  {desc}: {value}[/green]")
                    else:
                        device_info[desc] = output
                else:
                    console.print(f"[yellow]  {desc}: No response[/yellow]")
            except Exception as e:
                console.print(f"[red]  Error en {desc}: {str(e)}[/red]")
        
        if len(device_info) > 1:  # Si obtuvo al menos una respuesta SNMP
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

    # IPs específicas a escanear (en lugar de todo el rango)
    target_ips = [
        '30.20.10.10',   # Tu servidor
        '30.20.10.113'   # Tu cliente Alpine
    ]
    
    # Escaneo dirigido
    start_time = time.time()
    devices = snmp_scan(target_ips)
    elapsed_time = time.time() - start_time
    
    # Mostrar resultados
    if devices:
        table = Table(title="Dispositivos SNMP", header_style="bold blue")
        table.add_column("IP", style="cyan")
        table.add_column("Nombre")
        table.add_column("Descripción")
        table.add_column("Ubicación")
        
        for device in devices:
            table.add_row(
                device['ip'],
                device.get('System Name', 'N/A'),
                device.get('System Description', 'N/A')[:50] + '...' if 'System Description' in device else 'N/A',
                device.get('Location', 'N/A')
            )
        
        console.print(table)
    else:
        console.print("[red]No se encontraron dispositivos SNMP.[/red]")
    
    console.print(f"\nTiempo de escaneo: {elapsed_time:.2f} segundos")

if __name__ == "__main__":
    main()