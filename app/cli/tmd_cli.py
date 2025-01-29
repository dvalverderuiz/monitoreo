import subprocess
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import psutil

console = Console()

def get_network_stats():
    """Obtiene estadísticas de red."""
    net_io = psutil.net_io_counters()
    return {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv,
    }

def show_devices():
    """Muestra los dispositivos en la red usando arp-scan."""
    try:
        result = subprocess.run(["arp-scan", "--localnet"], capture_output=True, text=True)
        devices = result.stdout.splitlines()
        
        table = Table(title="Dispositivos en la Red")
        table.add_column("IP", style="cyan")
        table.add_column("MAC", style="magenta")
        table.add_column("Fabricante", style="green")

        for line in devices:
            if "192.168." in line:  # Filtra solo líneas con direcciones IP
                parts = line.split()
                ip = parts[0]
                mac = parts[1]
                manufacturer = " ".join(parts[2:])
                table.add_row(ip, mac, manufacturer)

        console.print(table)
    except FileNotFoundError:
        console.print("[red]Error:[/red] `arp-scan` no está instalado. Instálalo con `sudo apt install arp-scan`.")

def show_menu():
    """Muestra el menú de la aplicación."""
    console.print(Panel("""
[bold]1.[/bold] Mostrar estadísticas de red
[bold]2.[/bold] Listar dispositivos en la red (TMD devices)
[bold]3.[/bold] Salir
""", title="Menú Principal", border_style="blue"))

def main():
    while True:
        show_menu()
        choice = console.input("[bold]Selecciona una opción: [/bold]")

        if choice == "1":
            stats = get_network_stats()
            table = Table(title="Estadísticas de Red")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="magenta")
            table.add_row("Bytes Enviados", f"{stats['bytes_sent']} bytes")
            table.add_row("Bytes Recibidos", f"{stats['bytes_recv']} bytes")
            table.add_row("Paquetes Enviados", f"{stats['packets_sent']} paquetes")
            table.add_row("Paquetes Recibidos", f"{stats['packets_recv']} paquetes")
            console.print(table)

        elif choice == "2":
            console.print("[bold]Ejecutando 'TMD devices'...[/bold]")
            show_devices()

        elif choice == "3":
            console.print("[bold]Saliendo...[/bold]")
            break

        else:
            console.print("[red]Opción no válida. Inténtalo de nuevo.[/red]")

        time.sleep(1)  # Pausa para mejorar la experiencia de usuario

if __name__ == "__main__":
    main()
