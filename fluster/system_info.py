# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
# Author: Ruben Sanchez Sanchez <rsanchez@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <https://www.gnu.org/licenses/>.

import ctypes
import ctypes.util
import os
import platform
import re
import subprocess
from typing import Any, Dict, List, Optional


class SystemInfo:
    """Collects hardware and software information about the system"""

    def __init__(self) -> None:
        self.os_name = platform.system()
        self.os_version = platform.release()
        self.cpu_model = self._get_cpu_model()
        self.gpu_info = self._get_gpu_info()
        self.total_ram = self._get_total_ram()
        self.backend_info = self._get_backend_info()

    @staticmethod
    def _run_command(command: List[str]) -> str:
        """Run a command and return its output, or empty string on failure"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, OSError):
            pass
        return ""

    @staticmethod
    def _parse_wmic_list(output: str, key: str) -> Optional[str]:
        """Parse wmic /format:list output for a specific key"""
        for line in output.split("\n"):
            if line.startswith(f"{key}="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
        return None

    @staticmethod
    def _parse_wmic_table(output: str, skip_header: str) -> Optional[str]:
        """Parse wmic table format, skipping header and empty lines"""
        lines = [item.strip() for item in output.split("\n") if item.strip()]
        for line in lines[1:] if len(lines) > 1 else []:
            if line and line != skip_header:
                return line
        return None

    @staticmethod
    def _bytes_to_gb(bytes_value: int) -> str:
        """Convert bytes to GB with one decimal place"""
        gb = bytes_value / (1024 * 1024 * 1024)
        return f"{gb:.1f} GB"

    def _get_cpu_model(self) -> str:
        """Get CPU model information"""
        try:
            if self.os_name == "Linux":
                with open("/proc/cpuinfo", encoding="utf-8") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":")[1].strip()
            elif self.os_name == "Darwin":
                output = self._run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
                if output:
                    return output
            elif self.os_name == "Windows":
                output = self._run_command(["wmic", "cpu", "get", "name", "/format:list"])
                if output:
                    cpu_name = self._parse_wmic_list(output, "Name")
                    if cpu_name:
                        return cpu_name

                output = self._run_command(["wmic", "cpu", "get", "name"])
                if output:
                    cpu_name = self._parse_wmic_table(output, "Name")
                    if cpu_name:
                        return cpu_name
        except (FileNotFoundError, OSError, ValueError, IndexError):
            pass
        return "Unknown CPU"

    @staticmethod
    def _get_primary_gpu_pci() -> Optional[str]:
        """Get the PCI ID of the primary GPU (Linux only)"""
        try:
            drm_path = "/sys/class/drm"
            if not os.path.exists(drm_path):
                return None

            for device in os.listdir(drm_path):
                if not device.startswith("card") or "-" in device:
                    continue

                boot_vga_file = os.path.join(drm_path, device, "device", "boot_vga")
                if not os.path.exists(boot_vga_file):
                    continue

                with open(boot_vga_file, encoding="utf-8") as f:
                    if f.read().strip() == "1":
                        pci_link = os.path.join(drm_path, device, "device")
                        if os.path.islink(pci_link):
                            pci_path = os.readlink(pci_link)
                            return pci_path.split("/")[-1]
        except (OSError, ValueError, IndexError):
            pass
        return None

    def _get_gpu_info(self) -> List[str]:
        """Get GPU information"""
        gpus = []

        try:
            if self.os_name == "Linux":
                primary_pci = self._get_primary_gpu_pci()

                try:
                    output = self._run_command(["lspci"])
                    if output:
                        for line in output.split("\n"):
                            if "VGA" in line or "3D" in line or "Display" in line:
                                # Extract PCI ID (e.g., "01:00.0")
                                pci_match = re.match(r"([0-9a-f:.]+)\s", line)
                                pci_id = pci_match.group(1) if pci_match else None

                                match = re.search(r":\s*(.+?)(?:\s*\[|\s*\(|$)", line)
                                if match:
                                    gpu_name = match.group(1).strip()
                                    if gpu_name and gpu_name not in gpus:
                                        if primary_pci and pci_id and pci_id in primary_pci:
                                            gpu_name += " [PRIMARY]"
                                        gpus.append(gpu_name)
                except FileNotFoundError:
                    pass

                try:
                    drm_path = "/sys/class/drm"
                    if os.path.exists(drm_path):
                        for device in os.listdir(drm_path):
                            if device.startswith("card") and not device.startswith("card0-"):
                                name_file = os.path.join(drm_path, device, "device", "vendor")
                                if os.path.exists(name_file):
                                    with open(name_file, encoding="utf-8") as f:
                                        vendor_id = f.read().strip()
                                    model_file = os.path.join(drm_path, device, "device", "device")
                                    if os.path.exists(model_file):
                                        with open(model_file, encoding="utf-8") as f:
                                            device_id = f.read().strip()
                                        gpu_info = f"GPU {vendor_id}:{device_id}"
                                        if gpu_info not in gpus and not gpus:
                                            gpus.append(gpu_info)
                except (OSError, ValueError):
                    pass

            elif self.os_name == "Darwin":
                output = self._run_command(["system_profiler", "SPDisplaysDataType"])
                if output:
                    first_gpu = True
                    for line in output.split("\n"):
                        if "Chipset Model:" in line:
                            gpu = line.split(":")[1].strip()
                            if gpu not in gpus:
                                # On macOS, the first GPU listed is typically the primary/active one
                                if first_gpu:
                                    gpu += " [PRIMARY]"
                                    first_gpu = False
                                gpus.append(gpu)

            elif self.os_name == "Windows":
                # Get primary GPU (the one with active display, CurrentRefreshRate > 0)
                primary_gpu_name = None
                output = self._run_command(
                    ["wmic", "path", "win32_VideoController", "get", "Name,CurrentRefreshRate", "/format:csv"]
                )
                if output:
                    for line in output.split("\n"):
                        if "," in line and line.strip() and "Name" not in line:
                            parts = line.split(",")
                            if len(parts) >= 3:
                                refresh_rate = parts[2].strip()
                                gpu_name = parts[1].strip()
                                if refresh_rate and refresh_rate != "0" and refresh_rate.isdigit():
                                    primary_gpu_name = gpu_name
                                    break

                # Get all GPU names
                output = self._run_command(["wmic", "path", "win32_VideoController", "get", "name"])
                if output:
                    lines = output.split("\n")
                    for line in lines[1:]:  # Skip header
                        gpu = line.strip()
                        if gpu and gpu not in gpus:
                            if primary_gpu_name and gpu == primary_gpu_name:
                                gpu += " [PRIMARY]"
                            gpus.append(gpu)
        except (OSError, ValueError):
            pass

        return gpus if gpus else ["Unknown GPU"]

    def _get_total_ram(self) -> str:
        """Get total RAM in GB"""
        try:
            if self.os_name == "Linux":
                with open("/proc/meminfo", encoding="utf-8") as f:
                    for line in f:
                        if "MemTotal" in line:
                            mem_kb = int(line.split()[1])
                            return self._bytes_to_gb(mem_kb * 1024)
            elif self.os_name == "Darwin":
                output = self._run_command(["sysctl", "-n", "hw.memsize"])
                if output:
                    return self._bytes_to_gb(int(output))
            elif self.os_name == "Windows":
                output = self._run_command(["wmic", "computersystem", "get", "totalphysicalmemory", "/format:list"])
                if output:
                    mem_str = self._parse_wmic_list(output, "TotalPhysicalMemory")
                    if mem_str and mem_str.isdigit():
                        return self._bytes_to_gb(int(mem_str))

                output = self._run_command(["wmic", "computersystem", "get", "totalphysicalmemory"])
                if output:
                    mem_str = self._parse_wmic_table(output, "TotalPhysicalMemory")
                    if mem_str and mem_str.isdigit():
                        return self._bytes_to_gb(int(mem_str))
        except (FileNotFoundError, OSError, ValueError, IndexError):
            pass
        return "Unknown"

    @staticmethod
    def _get_vaapi_info() -> Optional[str]:
        """Get VA-API vendor string and version (Linux only)"""
        try:
            libva_path = ctypes.util.find_library("va")
            libva_drm_path = ctypes.util.find_library("va-drm")

            if not libva_path or not libva_drm_path:
                return None

            libva = ctypes.CDLL(libva_path)
            libva_drm = ctypes.CDLL(libva_drm_path)

            va_display_t = ctypes.c_void_p
            va_status_t = ctypes.c_int
            va_status_success = 0
            drm_node = "/dev/dri/renderD128"

            libva_drm.vaGetDisplayDRM.argtypes = [ctypes.c_int]
            libva_drm.vaGetDisplayDRM.restype = va_display_t
            libva.vaInitialize.argtypes = [va_display_t, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
            libva.vaInitialize.restype = va_status_t
            libva.vaQueryVendorString.argtypes = [va_display_t]
            libva.vaQueryVendorString.restype = ctypes.c_char_p
            libva.vaTerminate.argtypes = [va_display_t]
            libva.vaTerminate.restype = va_status_t

            # Suppress libva stderr messages by redirecting to /dev/null
            stderr_fd = os.dup(2)
            devnull_fd = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull_fd, 2)

            try:
                fd = os.open(drm_node, os.O_RDWR)
                try:
                    display = libva_drm.vaGetDisplayDRM(fd)
                    if not display:
                        return None

                    major = ctypes.c_int()
                    minor = ctypes.c_int()
                    status = libva.vaInitialize(display, ctypes.byref(major), ctypes.byref(minor))

                    if status != va_status_success:
                        return None

                    vendor_ptr = libva.vaQueryVendorString(display)
                    if vendor_ptr:
                        vendor_str = vendor_ptr.decode("utf-8")
                        result = f"{vendor_str} (runtime {major.value}.{minor.value})"
                        libva.vaTerminate(display)
                        return result

                    libva.vaTerminate(display)
                    return None
                finally:
                    os.close(fd)
            finally:
                # Restore stderr
                os.dup2(stderr_fd, 2)
                os.close(stderr_fd)
                os.close(devnull_fd)

        except (OSError, AttributeError, ValueError):
            return None

    def _get_backend_info(self) -> Dict[str, str]:
        """Get backend and driver information"""
        backends = {}

        try:
            if self.os_name == "Linux":
                vaapi_info = self._get_vaapi_info()
                if vaapi_info:
                    backends["VA-API"] = vaapi_info

                output = self._run_command(["vdpauinfo"])
                if output:
                    for line in output.split("\n"):
                        if "information string:" in line.lower():
                            backends["VDPAU"] = line.split(":")[1].strip()
                            break

                output = self._run_command(["vulkaninfo", "--summary"])
                if output:
                    for line in output.split("\n"):
                        if "driverName" in line:
                            match = re.search(r"=\s*(.+)", line)
                            if match:
                                backends["Vulkan"] = match.group(1).strip()
                                break

            elif self.os_name == "Darwin":
                try:
                    output = self._run_command(["sw_vers", "-productVersion"])
                    if output:
                        backends["VideoToolbox"] = f"macOS {output}"
                    else:
                        backends["VideoToolbox"] = "Available"
                except (OSError, ValueError):
                    backends["VideoToolbox"] = "Available"

            elif self.os_name == "Windows":
                self._run_command(["dxdiag", "/t", "dxdiag_output.txt"])
                backends["DirectX"] = f"Windows {self.os_version}"

        except (OSError, ValueError):
            pass

        return backends

    def to_dict(self) -> Dict[str, Any]:
        """Convert system information to dictionary format"""
        return {
            "os": f"{self.os_name} {self.os_version}",
            "cpu": self.cpu_model,
            "gpu": self.gpu_info,
            "ram": self.total_ram,
            "backends": self.backend_info,
        }

    def to_markdown(self) -> str:
        """Format system information as Markdown"""
        output = "## System Information\n\n"
        output += f"**OS:** {self.os_name} {self.os_version}\n\n"
        output += f"**CPU:** {self.cpu_model}\n\n"
        output += f"**GPU:** {', '.join(self.gpu_info)}\n\n"
        output += f"**RAM:** {self.total_ram}\n\n"

        if self.backend_info:
            output += "**Backends:**\n"
            for backend, info in self.backend_info.items():
                output += f"- {backend}: {info}\n"
            output += "\n"
        else:
            output += "**Backends:** None detected\n\n"

        return output

    def to_text(self) -> str:
        """Format system information as plain text"""
        output = f"OS: {self.os_name} {self.os_version}\n"
        output += f"CPU: {self.cpu_model}\n"
        output += f"GPU: {', '.join(self.gpu_info)}\n"
        output += f"RAM: {self.total_ram}\n"

        if self.backend_info:
            output += "Backends:\n"
            for backend, info in self.backend_info.items():
                output += f"  {backend}: {info}\n"
        else:
            output += "Backends: None detected\n"

        return output
