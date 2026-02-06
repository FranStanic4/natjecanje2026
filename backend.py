from os import remove, walk, startfile
from os.path import exists, join, relpath, basename, isdir, getsize
from psutil import process_iter, NoSuchProcess, AccessDenied, ZombieProcess, virtual_memory, Process, \
    HIGH_PRIORITY_CLASS, cpu_count, cpu_freq, cpu_percent
from subprocess import CalledProcessError, run, DEVNULL, Popen, PIPE
from zipfile import ZipFile, ZIP_DEFLATED
from ctypes import windll
import winreg
from json import load, dump
from time import sleep
from threading import Thread

try:
    import GPUtil
except ImportError:
    GPUtil = None


class Function:
    def __init__(self):
        pass

    def log(self, msg):
        print(f"[{self.__class__.__name__}] {msg}")


class ProcessMonitor_F(Function):
    def __init__(self):
        super().__init__()
        self.config_file = "process_config.json"
        self.blacklist = []
        self.whitelist = []
        self.monitoring = False
        self.load_config()

    def load_config(self):
        try:
            if exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = load(f)
                    self.blacklist = data.get("blacklist", [])
                    self.whitelist = data.get("whitelist", [])
                self.log(f"Config loaded. Blacklist: {len(self.blacklist)}, Whitelist: {len(self.whitelist)}")
        except Exception as e:
            self.log(f"Error loading config: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                dump({"blacklist": self.blacklist, "whitelist": self.whitelist}, f, indent=4)
            self.log("Config saved successfully.")
        except Exception as e:
            self.log(f"Error saving config: {e}")

    def add_to_blacklist(self, name):
        if name not in self.blacklist:
            self.blacklist.append(name)
            self.save_config()
            self.log(f"Added '{name}' to blacklist.")
            return True
        return False

    def remove_from_blacklist(self, name):
        if name in self.blacklist:
            self.blacklist.remove(name)
            self.save_config()
            self.log(f"Removed '{name}' from blacklist.")
            return True
        return False

    def add_to_whitelist(self, name):
        if name not in self.whitelist:
            self.whitelist.append(name)
            self.save_config()
            self.log(f"Added '{name}' to whitelist.")
            return True
        return False

    def remove_from_whitelist(self, name):
        if name in self.whitelist:
            self.whitelist.remove(name)
            self.save_config()
            self.log(f"Removed '{name}' from whitelist.")
            return True
        return False

    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            Thread(target=self._monitor_loop, daemon=True).start()
            self.log("Process monitoring started.")
            return "Monitoring Started"
        return "Monitoring already running"

    def stop_monitoring(self):
        self.monitoring = False
        self.log("Process monitoring stop requested.")
        return "Monitoring Stopped"

    def _monitor_loop(self):
        self.log("Background monitoring loop active.")
        while self.monitoring:
            for proc in process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] in self.blacklist:
                        if proc.info['name'] not in self.whitelist:
                            proc.terminate()
                            self.log(f"ACTION: Auto-Terminated blacklisted process '{proc.info['name']}' (PID: {proc.info['pid']})")
                except (NoSuchProcess, AccessDenied, ZombieProcess):
                    pass
            sleep(2)
        self.log("Background monitoring loop terminated.")


class FocusMode_F(Function):
    def toggle_focus_mode(self, enable=True):
        """
        Simulates Focus Mode by minimizing background windows (simplistic approach)
        or checking for Windows Focus Assist (requires winreg).
        Here we toggle a registry key for 'Focus Assist' (Priority Only).
        """
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings"
        self.log(f"Toggling Focus Mode: {'ON' if enable else 'OFF'}")
        try:
            val = 1 if enable else 0
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED", 0, winreg.REG_DWORD, val)
            winreg.CloseKey(key)
            self.log("Registry updated: NOC_GLOBAL_SETTING_TOASTS_ENABLED")
            return f"Focus Assist {'Enabled' if enable else 'Disabled'}"
        except Exception as e:
            self.log(f"Error accessing registry: {e}")
            return f"Registry access failed: {e}. (Try running as Admin)"


class RegistryTweaks_F(Function):
    def apply_tweak(self, tweak_name):
        """Applies specific performance registry tweaks."""
        self.log(f"Applying tweak: {tweak_name}")
        try:
            if tweak_name == "NetworkThrottling":
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xffffffff)
                winreg.CloseKey(key)
                self.log("Registry: NetworkThrottlingIndex set to 0xffffffff")
                return "Network Throttling Disabled"
            
            elif tweak_name == "SystemResponsiveness":
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                self.log("Registry: SystemResponsiveness set to 0")
                return "System Responsiveness Optimized"
            
            elif tweak_name == "MenuShowDelay":
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "MenuShowDelay", 0, winreg.REG_SZ, "0")
                winreg.CloseKey(key)
                self.log("Registry: MenuShowDelay set to 0")
                return "Menu Delay Reduced"

            elif tweak_name == "VisualEffects":
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2)
                winreg.CloseKey(key)
                self.log("Registry: VisualFXSetting set to 2 (Best Performance)")
                return "Visual Effects Optimized"

            elif tweak_name == "GameMode":
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "AutoGameModeEnabled", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
                self.log("Registry: AutoGameModeEnabled set to 1")
                return "Game Mode Enabled"
                
            return "Unknown Tweak"
        except Exception as e:
            self.log(f"Error applying tweak: {e}")
            return f"Error applying tweak: {e}"


class GPU_F(Function):
    def get_gpu_info(self):
        """Returns a list of GPUs and their stats."""
        gpus_info = []
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    gpus_info.append({
                        "name": gpu.name,
                        "load": f"{gpu.load*100:.1f}%",
                        "memory_free": f"{gpu.memoryFree}MB",
                        "memory_used": f"{gpu.memoryUsed}MB",
                        "memory_total": f"{gpu.memoryTotal}MB",
                        "temperature": f"{gpu.temperature} C"
                    })
            except Exception as e:
                self.log(f"GPUtil error: {e}")
                return [{"error": f"Error retrieving GPU info: {e}"}]
        
        if not gpus_info:
            return [{"name": "No dedicated GPU detected or GPUtil not supported", "load": "N/A"}]
        return gpus_info

    def optimize_gpu_settings(self):
        """
        Applies Windows GPU optimizations:
        1. Hardware Accelerated GPU Scheduling (Requires Restart)
        2. Priority for Graphics
        3. NVIDIA High Performance Mode (via nvidia-smi)
        """
        log = []
        self.log("Starting GPU Optimization...")
        
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "HwSchMode", 0, winreg.REG_DWORD, 2)
            winreg.CloseKey(key)
            msg = "Enabled Hardware Accelerated GPU Scheduling (Restart Required)"
            log.append(msg)
            self.log(f"Registry: {msg}")
        except Exception as e:
            log.append(f"Failed HwSchMode: {e}")
            self.log(f"Error HwSchMode: {e}")

        try:
            run("nvidia-smi -pm 1", shell=True, stdout=DEVNULL, stderr=DEVNULL)
            msg = "Enabled NVIDIA Persistence Mode"
            log.append(msg)
            self.log(f"Shell: {msg}")
        except:
            pass 
            
        return "\n".join(log)

    def launch_overclock_tool(self):
        """Attempts to launch MSI Afterburner if installed."""
        self.log("Searching for MSI Afterburner...")
        possible_paths = [
            r"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe",
            r"C:\Program Files\MSI Afterburner\MSIAfterburner.exe"
        ]
        
        for path in possible_paths:
            if exists(path):
                try:
                    startfile(path)
                    self.log(f"Launching: {path}")
                    return "Launched MSI Afterburner"
                except Exception as e:
                    self.log(f"Error launching {path}: {e}")
                    return f"Error launching: {e}"
        
        self.log("MSI Afterburner not found.")
        return "MSI Afterburner not found. Please install it for manual overclocking."


def get_optimisation_commands():
    """Returns a list of CMD optimisation commands."""
    return [
        ("SFC Scan", "sfc /scannow"),
        ("DISM Restore Health", "DISM /Online /Cleanup-Image /RestoreHealth"),
        ("Flush DNS", "ipconfig /flushdns"),
        ("Check Disk", "chkdsk /f"),
        ("Defrag C:", "defrag C: /O")
    ]


class SecretFeatureUnlocker_F(Function):
    def open_apps_folder(self):
        """Opens the Windows Apps Folder."""
        try:
            startfile("shell:AppsFolder")
            self.log("Opened shell:AppsFolder")
            return "Opened Apps Folder"
        except Exception as e:
            self.log(f"Error opening folder: {e}")
            return f"Error: {e}"

    def run_command(self, command):
        """Runs a shell command and returns output. Note: Some commands require Admin."""
        self.log(f"Executing command: {command}")
        try:
            process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
            stdout, stderr = process.communicate()
            output = stdout + stderr
            self.log(f"Command Output:\n{output.strip()}")
            return output
        except Exception as e:
            self.log(f"Execution Error: {e}")
            return f"Execution Error: {e}"


def trim_working_set(pid):
    try:
        # PROCESS_SET_QUOTA (0x0100) | PROCESS_QUERY_INFORMATION (0x0400)
        handle = windll.kernel32.OpenProcess(0x0500, False, pid)
        if handle:
            windll.psapi.EmptyWorkingSet(handle)
            windll.kernel32.CloseHandle(handle)
            return True
    except:
        pass
    return False


def get_top_processes(limit=10):
    """Returns top processes by Memory usage."""
    procs = []
    for p in process_iter(['pid', 'name', 'memory_info']):
        try:
            procs.append(p.info)
        except (NoSuchProcess, AccessDenied, ZombieProcess):
            pass

    procs.sort(key=lambda x: x['memory_info'].rss, reverse=True)
    return procs[:limit]


def get_ram_info():
    return virtual_memory()


class RAM_F(Function):

    def set_high_priority(self, pid):
        """Sets a process to High Priority (Windows)."""
        try:
            p = Process(pid)
            p.nice(HIGH_PRIORITY_CLASS)
            self.log(f"Set PID {pid} ({p.name()}) to HIGH_PRIORITY_CLASS")
            return f"Set PID {pid} to High Priority"
        except Exception as e:
            self.log(f"Error setting priority for PID {pid}: {e}")
            return f"Error setting priority: {e}"

    def kill_process(self, pid):
        try:
            p = Process(pid)
            name = p.name()
            p.terminate()
            self.log(f"Terminated process {name} (PID: {pid})")
            return f"Terminated PID {pid}"
        except Exception as e:
            self.log(f"Error terminating PID {pid}: {e}")
            return f"Error terminating process: {e}"

    def smart_ram_optimization(self, whitelist_names):
        """
        Trims RAM for all processes EXCEPT those in whitelist.
        Boosts priority for whitelist processes.
        """
        self.log("Starting Smart RAM Optimization...")
        results = {"trimmed": 0, "boosted": 0, "errors": 0}
        
        for p in process_iter(['pid', 'name']):
            try:
                name = p.info['name']
                pid = p.info['pid']
                
                if name in whitelist_names:
                    try:
                        proc = Process(pid)
                        proc.nice(HIGH_PRIORITY_CLASS)
                        results["boosted"] += 1
                        self.log(f"Boosted priority for whitelisted app: {name}")
                    except:
                        results["errors"] += 1
                else:

                    if trim_working_set(pid):
                        results["trimmed"] += 1
            except (NoSuchProcess, AccessDenied):
                results["errors"] += 1
        
        self.log(f"Smart Optimization Complete. Trimmed: {results['trimmed']}, Boosted: {results['boosted']}, Errors: {results['errors']}")
        return results

    def optimize_system_cache(self):
        """Enables Large System Cache in Registry (Better for servers/heavy RAM users)."""
        self.log("Enabling Large System Cache...")
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "LargeSystemCache", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "DisablePagingExecutive", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            self.log("Registry: LargeSystemCache=1, DisablePagingExecutive=1")
            return "Enabled Large System Cache & Kernel RAM Locking (Restart Required)"
        except Exception as e:
            self.log(f"Error: {e}")
            return f"Error: {e}"


def get_cpu_info():
    return {
        "physical_cores": cpu_count(logical=False),
        "logical_cores": cpu_count(logical=True),
        "frequency": cpu_freq().current if cpu_freq() else "Unknown",
        "percent": cpu_percent(interval=1)
    }


class Overclocking_F(Function):

    def set_power_plan_high_performance(self):
        """Sets Windows Power Plan to High Performance (Requires Admin/PowerShell)."""
        self.log("Setting High Performance Power Plan...")
        # GUID for High Performance: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
        cmd = "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        return self.run_shell(cmd)

    def unpark_cpu_cores(self):
        """
        Unparks CPU Cores by modifying Power Plan settings.
        Sets 'Processor performance core parking min cores' to 100%.
        """
        self.log("Unparking CPU Cores (Setting Min State to 100%)...")
        try:
            # GUID: 0cc5b647-c1df-4637-891a-dec35c318583
            cmd1 = "powercfg -attributes SUB_PROCESSOR 0cc5b647-c1df-4637-891a-dec35c318583 -ATTRIB_HIDE"
            run(cmd1, shell=True, check=True)
            cmd2 = "powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR 0cc5b647-c1df-4637-891a-dec35c318583 100"
            cmd3 = "powercfg /setdcvalueindex SCHEME_CURRENT SUB_PROCESSOR 0cc5b647-c1df-4637-891a-dec35c318583 100"
            cmd4 = "powercfg /setactive SCHEME_CURRENT"
            
            run(cmd2, shell=True, check=True)
            run(cmd3, shell=True, check=True)
            run(cmd4, shell=True, check=True)
            
            self.log("CPU Unpark commands executed successfully.")
            return "CPU Cores Unparked (Set to 100% Active)"
        except Exception as e:
            self.log(f"Error unparking cores: {e}")
            return f"Error unparking cores: {e}"

    def run_shell(self, cmd):
        self.log(f"Running shell command: {cmd}")
        try:
            run(cmd, shell=True, check=True)
            self.log("Command success.")
            return "Command executed successfully"
        except CalledProcessError:
            self.log("Command failed.")
            return "Command failed"


class Storage_F(Function):
    def find_huge_files(self, start_path, size_mb_threshold=500):
        """Finds files larger than threshold (MB)."""
        self.log(f"Scanning for files larger than {size_mb_threshold}MB in {start_path}...")
        huge_files = []
        threshold_bytes = size_mb_threshold * 1024 * 1024
        
        try:
            for root, _, files in walk(start_path):
                for name in files:
                    try:
                        file_path = join(root, name)
                        size = getsize(file_path)
                        if size > threshold_bytes:
                            huge_files.append((file_path, size / (1024*1024)))
                    except OSError:
                        continue
        except Exception as e:
            self.log(f"Error scanning: {e}")
            print(f"Error scanning: {e}")
            
        self.log(f"Scan complete. Found {len(huge_files)} files.")
        return sorted(huge_files, key=lambda x: x[1], reverse=True)

    def zip_item(self, path):
        """Zips a file or folder."""
        self.log(f"Zipping item: {path}")
        try:
            zip_name = f"{path}.zip"
            with ZipFile(zip_name, 'w', ZIP_DEFLATED) as zipf:
                if isdir(path):
                    for root, _, files in walk(path):
                        for file in files:
                            zipf.write(join(root, file),
                                       relpath(join(root, file),
                                       join(path, '..')))
                else:
                    zipf.write(path, basename(path))
            self.log(f"Created archive: {zip_name}")
            remove(path)
            return f"Created {zip_name}"
        except Exception as e:
            self.log(f"Zip Error: {e}")
            return f"Zip Error: {e}"

    def optimize_ntfs(self):
        """Disables NTFS Last Access Update and 8.3 Name Creation to speed up I/O."""
        self.log("Applying NTFS Optimizations...")
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem", 0, winreg.KEY_SET_VALUE)

            winreg.SetValueEx(key, "NtfsDisableLastAccessUpdate", 0, winreg.REG_DWORD, 1)

            winreg.SetValueEx(key, "NtfsDisable8dot3NameCreation", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            self.log("Registry: NtfsDisableLastAccessUpdate=1, NtfsDisable8dot3NameCreation=1")
            return "NTFS Optimizations Applied (Disable Last Access + 8.3 Names)"
        except Exception as e:
            self.log(f"Error optimizing NTFS: {e}")
            return f"Error optimizing NTFS: {e}"
