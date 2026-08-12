import psutil
import platform
import os
import time

async def get_cpu_usage() -> str:
    """Get the current CPU usage percentage."""
    usage = psutil.cpu_percent(interval=0.5)
    return f"{usage}%"

async def get_memory_usage() -> str:
    """Get the current RAM usage."""
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    used_gb = mem.used / (1024 ** 3)
    return f"Used: {used_gb:.1f}GB / Total: {total_gb:.1f}GB ({mem.percent}%)"

async def get_disk_usage() -> str:
    """Get the disk usage of the primary drive."""
    # Handle windows vs macos paths
    path = "C:\\" if platform.system() == "Windows" else "/"
    disk = psutil.disk_usage(path)
    free_gb = disk.free / (1024 ** 3)
    total_gb = disk.total / (1024 ** 3)
    return f"Free: {free_gb:.1f}GB / Total: {total_gb:.1f}GB ({disk.percent}% used)"

async def get_os_info() -> str:
    """Get system and OS information."""
    return f"{platform.system()} {platform.release()} ({platform.architecture()[0]}) - {platform.node()}"

async def run_powershell_command(command: str) -> str:
    """Run an arbitrary powershell command."""
    if platform.system() != "Windows":
        return "Error: Powershell is only available on Windows."
    import subprocess
    try:
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return f"Success:\n{result.stdout.strip()}"
        else:
            return f"Error:\n{result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"

async def get_gpu_usage() -> str:
    """Get the current GPU usage."""
    import subprocess
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            if len(parts) == 4:
                return f"GPU Util: {parts[0].strip()}% | Memory: {parts[1].strip()}MB / {parts[2].strip()}MB | Temp: {parts[3].strip()}C"
            return f"GPU Info: {result.stdout.strip()}"
        return "GPU not found or nvidia-smi failed."
    except Exception as e:
        return f"Failed to get GPU usage: {e}"

async def get_bluetooth_battery() -> str:
    """Get Bluetooth devices battery levels."""
    import subprocess
    if platform.system() != "Windows":
        return "Only supported on Windows."
    cmd = "Get-PnpDevice -Class Bluetooth | Get-PnpDeviceProperty -KeyName '{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2' | Select-Object InstanceId, Data"
    try:
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split('\n')
        batteries = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                batteries.append(f"Device: {parts[0].split('\\')[-1]} - Battery: {parts[-1]}%")
        if batteries:
            return "\n".join(batteries)
        return "No Bluetooth battery data found."
    except Exception as e:
        return f"Failed to get bluetooth battery: {e}"

async def toggle_system_radio(radio_type: str, state: str) -> str:
    """Toggle Wi-Fi or Bluetooth natively using winsdk."""
    if platform.system() != "Windows":
        return "Only supported on Windows."
    try:
        import winsdk.windows.devices.radios as radios
        radio_list = await radios.Radio.get_radios_async()
        
        target_kind = 1 # WiFi
        if radio_type.lower() == "bluetooth": 
            target_kind = 3
            
        enable = state.lower() in ["on", "enable", "true", "1"]
        target_state = radios.RadioState.ON if enable else radios.RadioState.OFF
        
        for radio in radio_list:
            if radio.kind == target_kind:
                await radio.set_state_async(target_state)
                return f"Successfully turned {radio_type} {'ON' if enable else 'OFF'}."
                
        return f"Could not find a {radio_type} radio on this system."
    except ImportError:
        return "Error: winsdk is not installed."
    except Exception as e:
        return f"Failed to toggle {radio_type}: {e}"

def register_system_tools(registry):
    registry.register(
        name="get_cpu_usage",
        description="Get current CPU usage percentage",
        parameters={"type": "object", "properties": {}},
        func=get_cpu_usage,
        permission_level=0
    )
    
    registry.register(
        name="get_memory_usage",
        description="Get current RAM usage",
        parameters={"type": "object", "properties": {}},
        func=get_memory_usage,
        permission_level=0
    )
    
    registry.register(
        name="get_disk_usage",
        description="Get disk space usage for primary drive",
        parameters={"type": "object", "properties": {}},
        func=get_disk_usage,
        permission_level=0
    )

    registry.register(
        name="get_os_info",
        description="Get operating system version and hostname",
        parameters={"type": "object", "properties": {}},
        func=get_os_info,
        permission_level=0
    )

    registry.register(
        name="run_powershell_command",
        description="Run an arbitrary Windows Powershell command. Useful for changing settings, controlling network (e.g. netsh), managing files, or opening ms-settings URIs (like 'start ms-settings:wifi').",
        parameters={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
        func=run_powershell_command,
        permission_level=1
    )

    registry.register(
        name="get_gpu_usage",
        description="Get current GPU usage, memory, and temperature",
        parameters={"type": "object", "properties": {}},
        func=get_gpu_usage,
        permission_level=0
    )

    registry.register(
        name="get_bluetooth_battery",
        description="Get the battery percentage of all connected Bluetooth devices (e.g. mouse, keyboard)",
        parameters={"type": "object", "properties": {}},
        func=get_bluetooth_battery,
        permission_level=0
    )

    registry.register(
        name="toggle_system_radio",
        description="Natively turns Wi-Fi or Bluetooth on or off.",
        parameters={
            "type": "object", 
            "properties": {
                "radio_type": {"type": "string", "description": "'wifi' or 'bluetooth'"},
                "state": {"type": "string", "description": "'on' or 'off'"}
            },
            "required": ["radio_type", "state"]
        },
        func=toggle_system_radio,
        permission_level=1
    )
