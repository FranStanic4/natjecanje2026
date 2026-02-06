import customtkinter as ctk
import sys
from os import getcwd, startfile
from os.path import basename, abspath
from threading import Thread
from psutil import virtual_memory, cpu_percent
from tkinter import messagebox, filedialog
from ctypes import windll
import backend
from traceback import format_exc


# --- Constants & Config ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# --- Admin Check ---
def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    try:
        script = abspath(sys.argv[0])
        params = '"{}"'.format(script)
        cwd = getcwd()
        windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, cwd, 1)
    except Exception as e:
        windll.user32.MessageBoxW(0, f"Error elevating privileges: {e}", "Error", 0)
    sys.exit()


# --- Core Classes ---

class Module:
    def __init__(self, app):
        self.app = app
        self.tab = 1
        
    def setTab(self, newT, loadTab=True):
        self.tab = newT
        if loadTab:
            self.loadTab()
        
    def loadTab(self):
        method_name = f"tab{self.tab}"
        if hasattr(self, method_name):
            for widget in self.app.main_frame.winfo_children():
                widget.destroy()
            getattr(self, method_name)()


# --- UI Components ---
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, str):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", str)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
            self.text_widget.update_idletasks()
        except:
            pass

    def flush(self):
        pass


class InfoCard(ctk.CTkFrame):
    def __init__(self, master, title, value, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=("gray85", "gray17")) 
        
        self.title_lbl = ctk.CTkLabel(self, text=title, font=("Roboto", 12), text_color="gray")
        self.title_lbl.pack(anchor="w", padx=10, pady=(5, 0))
        
        self.value_lbl = ctk.CTkLabel(self, text=value, font=("Roboto", 16, "bold"))
        self.value_lbl.pack(anchor="w", padx=10, pady=(0, 5))


# --- UI Modules ---

class Dashboard(Module):
    def __init__(self, app):
        super().__init__(app)
        self.unlocker = backend
        self.tweaks = backend.RegistryTweaks_F()

    def tab1(self):
        ctk.CTkLabel(self.app.main_frame, text="System Dashboard", font=("Roboto", 24, "bold")).pack(pady=(10, 20), anchor="w")
        
        stats_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        
        mem = virtual_memory()
        InfoCard(stats_frame, "Memory Usage", f"{mem.percent}%").grid(row=0, column=0, padx=5, sticky="ew")
        InfoCard(stats_frame, "CPU Usage", f"{cpu_percent()}%").grid(row=0, column=1, padx=5, sticky="ew")
        
        ctk.CTkLabel(self.app.main_frame, text="Quick Optimizations", font=("Roboto", 18, "bold")).pack(pady=(20, 10), anchor="w")
        
        actions_frame = ctk.CTkFrame(self.app.main_frame)
        actions_frame.pack(fill="x", padx=5)
        
        for i, (name, cmd) in enumerate(self.unlocker.get_optimisation_commands()):
            btn = ctk.CTkButton(actions_frame, text=name, command=lambda c=cmd: self.run_cmd(c), 
                                fg_color="#2B2B2B", hover_color="#3A3A3A", border_width=1, border_color="gray")
            btn.grid(row=i//2, column=i%2, padx=10, pady=5, sticky="ew")
        
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.app.main_frame, text="Registry Tweaks (Advanced)", font=("Roboto", 18, "bold")).pack(pady=(20, 10), anchor="w")
        tweaks_frame = ctk.CTkFrame(self.app.main_frame)
        tweaks_frame.pack(fill="x", padx=5)
        
        tweaks = ["NetworkThrottling", "SystemResponsiveness", "MenuShowDelay", "VisualEffects", "GameMode"]
        for i, tw in enumerate(tweaks):
            btn = ctk.CTkButton(tweaks_frame, text=f"Apply {tw}", command=lambda t=tw: self.apply_tweak(t),
                                fg_color="#006400", hover_color="#008000")
            btn.pack(side="left", padx=5, pady=10, expand=True, fill="x")

    def run_cmd(self, cmd):
        Thread(target=self._run_cmd_thread, args=(cmd,)).start()

    def _run_cmd_thread(self, cmd):
        print(f"Running: {cmd}")
        self.unlocker.run_command(cmd)
        self.app.after(0, self.loadTab)
        
    def apply_tweak(self, tweak):
        res = self.tweaks.apply_tweak(tweak)
        messagebox.showinfo("Registry Tweak", res)
        self.loadTab()


class FocuseMode(Module):
    def __init__(self, app):
        super().__init__(app)
        self.focus_f = backend.FocusMode_F()
        self.is_enabled = False

    def tab1(self):
        ctk.CTkLabel(self.app.main_frame, text="Focus Mode", font=("Roboto", 24, "bold")).pack(pady=(10, 20), anchor="w")
        
        status_color = "green" if self.is_enabled else "gray"
        status_text = "ACTIVE" if self.is_enabled else "INACTIVE"
        
        status_frame = ctk.CTkFrame(self.app.main_frame, border_color=status_color, border_width=2)
        status_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(status_frame, text=status_text, font=("Roboto", 20, "bold"), text_color=status_color).pack(pady=20)
        
        btn_text = "Disable Focus Mode" if self.is_enabled else "Enable Focus Mode"
        btn_color = "red" if self.is_enabled else "green"
        
        ctk.CTkButton(self.app.main_frame, text=btn_text, fg_color=btn_color, 
                      font=("Roboto", 16), height=40,
                      command=self.toggle_focus).pack(pady=10)
        
        ctk.CTkLabel(self.app.main_frame, text="Focus Mode optimizes Windows 'Focus Assist' settings\nto minimize distractions and suppress notifications.", text_color="gray").pack(pady=10)

    def toggle_focus(self):
        self.is_enabled = not self.is_enabled
        res = self.focus_f.toggle_focus_mode(self.is_enabled)
        messagebox.showinfo("Focus Mode", res)
        self.loadTab()


class RAM(Module):
    def __init__(self, app):
        super().__init__(app)
        self.ram_f = backend

    def tab1(self):
        ctk.CTkLabel(self.app.main_frame, text="RAM Management", font=("Roboto", 24, "bold")).pack(pady=(10, 20), anchor="w")
    
        ram = self.ram_f.get_ram_info()
        bar = ctk.CTkProgressBar(self.app.main_frame)
        bar.pack(fill="x", pady=5)
        bar.set(ram.percent / 100)
        
        ctk.CTkLabel(self.app.main_frame, text=f"Used: {ram.percent}% ({ram.used / (1024**3):.1f} GB) / Total: {ram.total / (1024**3):.1f} GB").pack(pady=(0, 20))
        
        ctk.CTkButton(self.app.main_frame, text="Smart RAM Optimize (Trim Unused + Boost Whitelist)", 
                      height=40, fg_color="#4B0082", hover_color="#8A2BE2",
                      command=self.run_smart_optimize).pack(fill="x", pady=10)

        ctk.CTkButton(self.app.main_frame, text="Enable Large System Cache (Registry Tweak)", 
                      height=30, fg_color="#006400", hover_color="#008000",
                      command=self.enable_cache).pack(fill="x", pady=(0, 20))
    
        ctk.CTkLabel(self.app.main_frame, text="High Memory Processes", font=("Roboto", 16, "bold")).pack(anchor="w")
        
        list_frame = ctk.CTkScrollableFrame(self.app.main_frame, height=350)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        procs = self.ram_f.get_top_processes(15)
        for p in procs:
            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{p['name'][:20]}", width=150, anchor="w", font=("Consolas", 12)).pack(side="left")
            ctk.CTkLabel(row, text=f"{p['memory_info'].rss / (1024*1024):.0f} MB", width=80, anchor="e").pack(side="left")
            
            ctk.CTkButton(row, text="Kill", width=60, fg_color="#8B0000", hover_color="#B22222",
                          command=lambda pid=p['pid']: self.kill_proc(pid)).pack(side="right", padx=5)
            
            ctk.CTkButton(row, text="Boost", width=60, fg_color="#DAA520", hover_color="#FFD700",
                          command=lambda pid=p['pid']: self.boost_proc(pid)).pack(side="right", padx=5)

    def run_smart_optimize(self):
        whitelist = []
        if "ProcManager" in self.app.modules:
            whitelist = self.app.modules["ProcManager"].proc_mon.whitelist
            
        res = self.ram_f.smart_ram_optimization(whitelist)
        messagebox.showinfo("Optimization Result", f"Trimmed: {res['trimmed']}\nBoosted: {res['boosted']}\nErrors: {res['errors']}")
        self.loadTab()

    def enable_cache(self):
        res = self.ram_f.optimize_system_cache()
        messagebox.showinfo("System Cache", res)
        self.loadTab()

    def kill_proc(self, pid):
        self.ram_f.kill_process(pid)
        self.loadTab()
        
    def boost_proc(self, pid):
        res = self.ram_f.set_high_priority(pid)
        messagebox.showinfo("Priority Boost", res)
        self.loadTab()


class CPU(Module):
    def __init__(self, app):
        super().__init__(app)
        self.overclock_f = backend

    def tab1(self):
        ctk.CTkLabel(self.app.main_frame, text="CPU & Power", font=("Roboto", 24, "bold")).pack(pady=(10, 20), anchor="w")
        
        info = self.overclock_f.get_cpu_info()
        
        grid = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        grid.pack(fill="x")
        
        InfoCard(grid, "Frequency", f"{info['frequency']} MHz").pack(side="left", fill="x", expand=True, padx=5)
        InfoCard(grid, "Physical Cores", str(info['physical_cores'])).pack(side="left", fill="x", expand=True, padx=5)
        InfoCard(grid, "Logical Cores", str(info['logical_cores'])).pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkLabel(self.app.main_frame, text="Power Management", font=("Roboto", 18, "bold")).pack(pady=(30, 10), anchor="w")
        
        ctk.CTkButton(self.app.main_frame, text="Enable Ultimate Performance Plan", 
                      height=50, font=("Roboto", 16),
                      command=self.set_high_perf).pack(fill="x", pady=10)
        
        ctk.CTkButton(self.app.main_frame, text="Unpark All CPU Cores (Max Performance)", 
                      height=40, fg_color="#8B0000", hover_color="#B22222",
                      command=self.unpark_cores).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.app.main_frame, text="* This forces the Windows 'High Performance' power scheme.", text_color="gray").pack()
        ctk.CTkLabel(self.app.main_frame, text="* 'Unpark' forces all cores to stay active (100% min state).", text_color="gray").pack()

    def set_high_perf(self):
        res = self.overclock_f.set_power_plan_high_performance()
        messagebox.showinfo("Power Plan", res)
        self.loadTab()
        
    def unpark_cores(self):
        res = self.overclock_f.unpark_cpu_cores()
        messagebox.showinfo("CPU Unpark", res)
        self.loadTab()


class GPU(Module):
    def __init__(self, app):
        super().__init__(app)
        self.gpu_f = backend.GPU_F()

    def tab1(self):
        ctk.CTkLabel(self.app.main_frame, text="GPU Statistics", font=("Roboto", 24, "bold")).pack(pady=(10, 20), anchor="w")
        
        gpus = self.gpu_f.get_gpu_info()
        
        for gpu in gpus:
            card = ctk.CTkFrame(self.app.main_frame)
            card.pack(fill="x", pady=10)
            
            ctk.CTkLabel(card, text=gpu.get("name", "Unknown GPU"), font=("Roboto", 18, "bold")).pack(pady=10, padx=10, anchor="w")
            
            if "error" in gpu:
                ctk.CTkLabel(card, text=gpu["error"], text_color="red").pack(padx=10, pady=10)
            elif gpu.get("load") != "N/A":
                grid = ctk.CTkFrame(card, fg_color="transparent")
                grid.pack(fill="x", padx=10, pady=10)
                
                ctk.CTkLabel(grid, text="Load").grid(row=0, column=0, sticky="w", padx=10)
                ctk.CTkLabel(grid, text=gpu['load'], font=("Roboto", 14, "bold")).grid(row=1, column=0, sticky="w", padx=10)
                
                ctk.CTkLabel(grid, text="Memory").grid(row=0, column=1, sticky="w", padx=10)
                ctk.CTkLabel(grid, text=f"{gpu['memory_used']} / {gpu['memory_total']}", font=("Roboto", 14, "bold")).grid(row=1, column=1, sticky="w", padx=10)
                
                ctk.CTkLabel(grid, text="Temp").grid(row=0, column=2, sticky="w", padx=10)
                ctk.CTkLabel(grid, text=gpu.get('temperature', 'N/A'), font=("Roboto", 14, "bold")).grid(row=1, column=2, sticky="w", padx=10)
            else:
                ctk.CTkLabel(card, text="No active load data available (GPU might be idle or unsupported).", text_color="gray").pack(padx=10, pady=10)
        
        ctk.CTkLabel(self.app.main_frame, text="GPU Optimization", font=("Roboto", 18, "bold")).pack(pady=(20, 10), anchor="w")
        
        btns_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        btns_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(btns_frame, text="Optimize Windows GPU Settings (Sched + Priority)", 
                      fg_color="#006400", hover_color="#008000",
                      command=self.optimize_gpu).pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(btns_frame, text="Launch MSI Afterburner (Manual Overclock)", 
                      fg_color="#8B0000", hover_color="#B22222",
                      command=self.launch_afterburner).pack(side="left", fill="x", expand=True, padx=5)
                      
        ctk.CTkLabel(self.app.main_frame, text="* 'Optimize' enables Hardware Scheduling (Restart Required).", text_color="gray").pack(pady=5)
        ctk.CTkLabel(self.app.main_frame, text="* Use MSI Afterburner for Frequency/Voltage control (Safe Software Overclocking).", text_color="gray").pack(pady=0)

    def optimize_gpu(self):
        res = self.gpu_f.optimize_gpu_settings()
        messagebox.showinfo("GPU Optimization", res)
        self.loadTab()
        
    def launch_afterburner(self):
        res = self.gpu_f.launch_overclock_tool()
        if "not found" in res:
            if messagebox.askyesno("Tool Missing", f"{res}\n\nWould you like to open the download page?"):
                import webbrowser
                webbrowser.open("https://www.msi.com/Landing/afterburner/graphics-cards")
        else:
            messagebox.showinfo("Launcher", res)


class Storage(Module):
    def __init__(self, app):
        super().__init__(app)
        self.storage_f = backend.Storage_F()
        self.scan_result_frame = None

    def tab1(self):
        ctk.CTkLabel(self.app.main_frame, text="Storage Optimizer", font=("Roboto", 24, "bold")).pack(pady=(10, 20), anchor="w")
        
        ctk.CTkButton(self.app.main_frame, text="Open Windows Apps Folder", 
                                 command=lambda: startfile("shell:AppsFolder"),
                                 fg_color="transparent", border_width=1, border_color="gray").pack(fill="x", pady=10)
        
        ctk.CTkButton(self.app.main_frame, text="Apply NTFS Optimizations (Disable Last Access Update)", 
                      fg_color="#006400", hover_color="#008000",
                      command=self.optimize_ntfs).pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(self.app.main_frame, text="Large File Hunter", font=("Roboto", 18, "bold")).pack(pady=(20, 10), anchor="w")
        ctk.CTkLabel(self.app.main_frame, text="Find files larger than 500MB to reclaim space.", text_color="gray").pack(anchor="w")
        
        ctk.CTkButton(self.app.main_frame, text="Select Drive/Folder to Scan...", command=self.scan_dir).pack(fill="x", pady=10)
        
        self.scan_result_frame = ctk.CTkScrollableFrame(self.app.main_frame, height=250)
        self.scan_result_frame.pack(fill="both", expand=True, pady=10)

    def optimize_ntfs(self):
        res = self.storage_f.optimize_ntfs()
        messagebox.showinfo("Storage Tweak", res)
        self.loadTab()

    def scan_dir(self):
        path = filedialog.askdirectory()
        if path:
            Thread(target=self._scan_thread, args=(path,)).start()
    
    def _scan_thread(self, path):
        for w in self.scan_result_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.scan_result_frame, text="Scanning... This may take a moment.").pack(pady=20)
        
        files = self.storage_f.find_huge_files(path)
        
        for w in self.scan_result_frame.winfo_children(): w.destroy()
            
        if not files:
            ctk.CTkLabel(self.scan_result_frame, text="No huge files found.").pack(pady=20)
            return

        for fpath, size_mb in files:
            row = ctk.CTkFrame(self.scan_result_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{basename(fpath)}", width=200, anchor="w", font=("Consolas", 12)).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{size_mb:.0f} MB", width=80).pack(side="left", padx=5)
            ctk.CTkButton(row, text="Zip", width=60, command=lambda p=fpath: self.zip_file(p)).pack(side="right", padx=5)

    def zip_file(self, path):
        res = self.storage_f.zip_item(path)
        messagebox.showinfo("Zip Result", res)
        self.loadTab()


class ProcessManager(Module):
    def __init__(self, app):
        super().__init__(app)
        self.proc_mon = backend.ProcessMonitor_F()

    def tab1(self):
        ctk.CTkLabel(self.app.main_frame, text="Process Manager (Blacklist/Whitelist)", font=("Roboto", 24, "bold")).pack(pady=(10, 20), anchor="w")
        
        control_frame = ctk.CTkFrame(self.app.main_frame)
        control_frame.pack(fill="x", pady=10)
        
        self.status_lbl = ctk.CTkLabel(control_frame, text="Status: Stopped", font=("Roboto", 16, "bold"), text_color="red")
        self.status_lbl.pack(side="left", padx=20)
        
        self.toggle_btn = ctk.CTkButton(control_frame, text="Start Monitoring", fg_color="green", command=self.toggle_monitoring)
        self.toggle_btn.pack(side="right", padx=20, pady=10)
        
        if self.proc_mon.monitoring:
            self.status_lbl.configure(text="Status: Active", text_color="green")
            self.toggle_btn.configure(text="Stop Monitoring", fg_color="red")
            
        lists_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        lists_frame.pack(fill="both", expand=True, pady=10)
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=1)
        
        self.build_list_panel(lists_frame, "Blacklist (Auto-Kill)", self.proc_mon.blacklist, 0, "red", self.add_blacklist, self.remove_blacklist)
        
        self.build_list_panel(lists_frame, "Whitelist (Protected)", self.proc_mon.whitelist, 1, "green", self.add_whitelist, self.remove_whitelist)
        
    def build_list_panel(self, parent, title, data_list, col, color, add_cmd, remove_cmd):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=col, sticky="nsew", padx=10)
        
        ctk.CTkLabel(frame, text=title, font=("Roboto", 16, "bold"), text_color=color).pack(pady=10)
        
        entry = ctk.CTkEntry(frame, placeholder_text="Process Name (e.g. chrome.exe)")
        entry.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(frame, text="Add", command=lambda: add_cmd(entry)).pack(fill="x", padx=10, pady=5)
        
        scroll = ctk.CTkScrollableFrame(frame)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        for item in data_list:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=item).pack(side="left")
            ctk.CTkButton(row, text="X", width=30, fg_color="red", command=lambda i=item: remove_cmd(i)).pack(side="right")

    def toggle_monitoring(self):
        if self.proc_mon.monitoring:
            self.proc_mon.stop_monitoring()
        else:
            self.proc_mon.start_monitoring()
        self.loadTab()

    def add_blacklist(self, entry):
        val = entry.get()
        if val:
            if self.proc_mon.add_to_blacklist(val):
                self.loadTab()
            else:
                messagebox.showwarning("Error", "Already in list")

    def remove_blacklist(self, val):
        self.proc_mon.remove_from_blacklist(val)
        self.loadTab()

    def add_whitelist(self, entry):
        val = entry.get()
        if val:
            if self.proc_mon.add_to_whitelist(val):
                self.loadTab()
            else:
                messagebox.showwarning("Error", "Already in list")

    def remove_whitelist(self, val):
        self.proc_mon.remove_from_whitelist(val)
        self.loadTab()


# --- Main Application ---

class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OPTIMISE")
        self.geometry("1100x850")
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="OPTIMISE", font=("Roboto", 24, "bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))
        
        # Navigation
        self.modules = {
            "Dashboard": Dashboard(self),
            "Focus Mode": FocuseMode(self),
            "RAM": RAM(self),
            "CPU": CPU(self),
            "GPU": GPU(self),
            "Storage": Storage(self),
            "ProcManager": ProcessManager(self)
        }
        
        self.nav_buttons = {}
        for i, (name, _) in enumerate(self.modules.items()):
            btn = ctk.CTkButton(self.sidebar, text=name, 
                                fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                anchor="w", font=("Roboto", 16),
                                command=lambda n=name: self.show_module(n))
            btn.grid(row=i+1, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons[name] = btn
            
        # Main Content
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray10"))
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        self.content_padding = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_padding.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Console
        self.console_frame = ctk.CTkFrame(self, height=150, corner_radius=0, fg_color=("gray90", "gray15"))
        self.console_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.console_frame.grid_propagate(False)
        
        self.console_header = ctk.CTkFrame(self.console_frame, height=30, fg_color="transparent")
        self.console_header.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(self.console_header, text="System Output & Logs", font=("Roboto", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(self.console_header, text="Clear", width=50, height=20, 
                      fg_color="#333", command=lambda: self.console_text.configure(state="normal") or self.console_text.delete("1.0", "end") or self.console_text.configure(state="disabled")).pack(side="right", padx=5)
        
        self.console_text = ctk.CTkTextbox(self.console_frame, font=("Consolas", 11), activate_scrollbars=True)
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.console_text.configure(state="disabled")
        

        sys.stdout = ConsoleRedirector(self.console_text)
        sys.stderr = ConsoleRedirector(self.console_text)
        
        print("System Initialized...")
        print("Admin privileges: Active")
        print("Waiting for user command...")

        for mod in self.modules.values():
            mod.app = self
            mod.app.main_frame = self.content_padding 

        # Footer
        self.footer = ctk.CTkLabel(self.sidebar, text="v2.0 Admin", text_color="gray")
        self.footer.grid(row=10, column=0, padx=20, pady=20, sticky="s")

        self.show_module("Dashboard")

    def show_module(self, name):
        for _, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent")

        self.nav_buttons[name].configure(fg_color=("gray75", "gray25"))
        
        module = self.modules[name]
        module.loadTab()


if __name__ == "__main__":
    try:
        app = Application()
        app.mainloop()
    except Exception as e:
        err_msg = f"An error occurred:\n{e}\n\n{format_exc()}"
        windll.user32.MessageBoxW(0, err_msg, "Critical Error", 0x10)
