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
from typing import Any, Dict, List, Optional, Tuple

from fluster.utils import run_command_with_output


class SystemInfo:
    """Collects hardware and software information about the system"""

    # ARM CPU implementer (JEP106) identifiers, keyed by the "CPU implementer" field.
    _ARM_IMPLEMENTERS = {
        0x41: "ARM",
        0x42: "Broadcom",
        0x43: "Cavium",
        0x44: "DEC",
        0x46: "Fujitsu",
        0x48: "HiSilicon",
        0x4E: "NVIDIA",
        0x50: "APM",
        0x51: "Qualcomm",
        0x53: "Samsung",
        0x56: "Marvell",
        0x61: "Apple",
        0x69: "Intel",
        0x6D: "Microsoft",
        0x70: "Phytium",
        0xC0: "Ampere",
    }

    # ARM (implementer 0x41) core names, keyed by the "CPU part" field.
    _ARM_PARTS = {
        0xB02: "ARM11 MPCore",
        0xB36: "ARM1136",
        0xB56: "ARM1156",
        0xB76: "ARM1176",
        0xC05: "Cortex-A5",
        0xC07: "Cortex-A7",
        0xC08: "Cortex-A8",
        0xC09: "Cortex-A9",
        0xC0D: "Cortex-A17",
        0xC0E: "Cortex-A17",
        0xC0F: "Cortex-A15",
        0xC14: "Cortex-R4",
        0xC15: "Cortex-R5",
        0xC17: "Cortex-R7",
        0xC18: "Cortex-R8",
        0xC20: "Cortex-M0",
        0xC21: "Cortex-M1",
        0xC23: "Cortex-M3",
        0xC24: "Cortex-M4",
        0xC27: "Cortex-M7",
        0xD01: "Cortex-A32",
        0xD02: "Cortex-A34",
        0xD03: "Cortex-A53",
        0xD04: "Cortex-A35",
        0xD05: "Cortex-A55",
        0xD06: "Cortex-A65",
        0xD07: "Cortex-A57",
        0xD08: "Cortex-A72",
        0xD09: "Cortex-A73",
        0xD0A: "Cortex-A75",
        0xD0B: "Cortex-A76",
        0xD0C: "Neoverse-N1",
        0xD0D: "Cortex-A77",
        0xD0E: "Cortex-A76AE",
        0xD13: "Cortex-R52",
        0xD15: "Cortex-R82",
        0xD40: "Neoverse-V1",
        0xD41: "Cortex-A78",
        0xD42: "Cortex-A78AE",
        0xD44: "Cortex-X1",
        0xD46: "Cortex-A510",
        0xD47: "Cortex-A710",
        0xD48: "Cortex-X2",
        0xD49: "Neoverse-N2",
        0xD4A: "Neoverse-E1",
        0xD4B: "Cortex-A78C",
        0xD4C: "Cortex-X1C",
        0xD4D: "Cortex-A715",
        0xD4E: "Cortex-X3",
        0xD4F: "Neoverse-V2",
        0xD80: "Cortex-A520",
        0xD81: "Cortex-A720",
        0xD82: "Cortex-X4",
        0xD84: "Neoverse-V3",
        0xD8E: "Neoverse-N3",
    }

    # Qualcomm (implementer 0x51) core names, keyed by the "CPU part" field.
    _QCOM_PARTS = {
        0x00F: "Scorpion",
        0x02D: "Scorpion",
        0x04D: "Krait",
        0x06F: "Krait",
        0x201: "Kryo",
        0x205: "Kryo",
        0x211: "Kryo",
        0x800: "Falkor V1/Kryo",
        0x801: "Kryo V2",
        0x802: "Kryo 3XX Gold",
        0x803: "Kryo 3XX Silver",
        0x804: "Kryo 4XX Gold",
        0x805: "Kryo 4XX Silver",
        0xC00: "Falkor",
        0xC01: "Saphira",
    }

    # NVIDIA (implementer 0x4e) core names, keyed by the "CPU part" field.
    _NVIDIA_PARTS = {
        0x000: "Denver",
        0x003: "Denver 2",
        0x004: "Carmel",
    }

    # Apple (implementer 0x61) core names, keyed by the "CPU part" field.
    _APPLE_PARTS = {
        0x000: "Swift",
        0x001: "Cyclone",
        0x002: "Typhoon",
        0x003: "Typhoon/Capri",
        0x004: "Twister",
        0x005: "Twister/Elba/Malta",
        0x006: "Hurricane",
        0x007: "Hurricane/Myst",
        0x008: "Monsoon",
        0x009: "Mistral",
        0x00B: "Vortex",
        0x00C: "Tempest",
        0x00F: "Tempest-M9",
        0x010: "Vortex/Aruba",
        0x011: "Tempest/Aruba",
        0x012: "Lightning",
        0x013: "Thunder",
        0x020: "Icestorm-A14",
        0x021: "Firestorm-A14",
        0x022: "Icestorm-M1",
        0x023: "Firestorm-M1",
        0x024: "Icestorm-M1-Pro",
        0x025: "Firestorm-M1-Pro",
        0x028: "Icestorm-M1-Max",
        0x029: "Firestorm-M1-Max",
        0x030: "Blizzard-M2",
        0x031: "Avalanche-M2",
        0x032: "Blizzard-M2-Pro",
        0x033: "Avalanche-M2-Pro",
        0x034: "Blizzard-M2-Max",
        0x035: "Avalanche-M2-Max",
    }

    # Per-implementer "CPU part" -> core-name tables.
    _PART_TABLES = {
        0x41: _ARM_PARTS,
        0x4E: _NVIDIA_PARTS,
        0x51: _QCOM_PARTS,
        0x61: _APPLE_PARTS,
    }

    def __init__(self) -> None:
        self.os_name = platform.system()
        self.os_version = platform.release()
        self.cpu_model = self._get_cpu_model()
        self.gpu_info = self._get_gpu_info()
        self.total_ram = self._get_total_ram()
        self.backend_info = self._get_backend_info()

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
                    cpuinfo = f.read()
                for line in cpuinfo.split("\n"):
                    if "model name" in line:
                        return line.split(":")[1].strip()
                # ARM cores expose no "model name"; describe them from the MIDR
                # fields instead.
                arm_model = self._get_arm_cpu_model(cpuinfo)
                if arm_model:
                    return arm_model
            elif self.os_name == "Darwin":
                output = run_command_with_output(["sysctl", "-n", "machdep.cpu.brand_string"], check=False)
                if output:
                    return output
            elif self.os_name == "Windows":
                cpu_name = None
                output = run_command_with_output(["wmic", "cpu", "get", "name", "/format:list"], check=False)
                if output:
                    cpu_name = self._parse_wmic_list(output, "Name")
                else:
                    output = run_command_with_output(["wmic", "cpu", "get", "name"], check=False)
                    if output:
                        cpu_name = self._parse_wmic_table(output, "Name")

                if cpu_name:
                    return cpu_name
        except (FileNotFoundError, OSError, ValueError, IndexError):
            pass
        return "Unknown CPU"

    @classmethod
    def _get_arm_cpu_model(cls, cpuinfo: str) -> Optional[str]:
        """Describe ARM cores (ARM, Qualcomm, NVIDIA, Apple) from /proc/cpuinfo MIDR fields.

        Such cores report no "model name"; instead each processor block carries a
        "CPU implementer" (vendor) and "CPU part" (core) code. Returns a summary
        grouping identical cores with their counts (e.g.
        "ARM Cortex-A78C x4, ARM Cortex-X1C x4" or "Qualcomm Kryo 4XX Gold x1"),
        or None when no core is found.
        """

        def _parse_hex(line: str) -> Optional[int]:
            try:
                return int(line.split(":", 1)[1].strip(), 16)
            except (ValueError, IndexError):
                return None

        cores: List[Tuple[int, int]] = []
        implementer: Optional[int] = None
        for line in cpuinfo.split("\n"):
            if line.startswith("CPU implementer"):
                implementer = _parse_hex(line)
            elif line.startswith("CPU part"):
                part = _parse_hex(line)
                if implementer is not None and part is not None:
                    cores.append((implementer, part))
                implementer = None

        if not cores:
            return None

        # Count identical cores while preserving first-seen order.
        counts: Dict[Tuple[int, int], int] = {}
        for key in cores:
            counts[key] = counts.get(key, 0) + 1

        descriptions = []
        for implementer, part in counts:
            vendor = cls._ARM_IMPLEMENTERS.get(implementer, f"0x{implementer:02x}")
            core = cls._PART_TABLES.get(implementer, {}).get(part, f"part 0x{part:03x}")
            descriptions.append(f"{vendor} {core} x{counts[(implementer, part)]}")

        return ", ".join(descriptions)

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
        try:
            if self.os_name == "Linux":
                return self._get_gpu_info_linux()
            elif self.os_name == "Darwin":
                return self._get_gpu_info_macos()
            elif self.os_name == "Windows":
                return self._get_gpu_info_windows()
        except (OSError, ValueError):
            pass

        return ["Unknown GPU"]

    def _get_gpu_info_linux(self) -> List[str]:
        """Get GPU information on Linux"""
        gpus = []
        primary_pci = self._get_primary_gpu_pci()

        try:
            output = run_command_with_output(["sh", "-c", "lspci | grep -E 'VGA|3D|Display'"], check=False)
            if output:
                for line in output.split("\n"):
                    if not line.strip():
                        continue

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

        return gpus if gpus else ["Unknown GPU"]

    @staticmethod
    def _get_gpu_info_macos() -> List[str]:
        """Get GPU information on macOS"""
        gpus = []
        output = run_command_with_output(["system_profiler", "SPDisplaysDataType"], check=False)
        if output:
            first_gpu = True
            for line in output.split("\n"):
                if "Chipset Model:" in line:
                    gpu = line.split(":")[1].strip()
                    if gpu not in gpus:
                        if first_gpu:
                            gpu += " [PRIMARY]"
                            first_gpu = False
                        gpus.append(gpu)

        return gpus if gpus else ["Unknown GPU"]

    @staticmethod
    def _get_gpu_info_windows() -> List[str]:
        """Get GPU information on Windows"""
        gpus = []

        # Get all GPUs with refresh rate info to identify primary in one pass
        output = run_command_with_output(
            ["wmic", "path", "win32_VideoController", "get", "Name,CurrentRefreshRate", "/format:csv"], check=False
        )
        if output:
            for line in output.split("\n"):
                if "," in line and line.strip() and "Name" not in line:
                    parts = line.split(",")
                    if len(parts) >= 3:
                        gpu_name = parts[1].strip()
                        refresh_rate = parts[2].strip()

                        if gpu_name and gpu_name not in gpus:
                            # Primary GPU is the one with active display (refresh rate > 0)
                            if refresh_rate and refresh_rate != "0" and refresh_rate.isdigit():
                                gpu_name += " [PRIMARY]"
                            gpus.append(gpu_name)

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
                output = run_command_with_output(["sysctl", "-n", "hw.memsize"], check=False)
                if output:
                    return self._bytes_to_gb(int(output))
            elif self.os_name == "Windows":
                mem_str = None
                output = run_command_with_output(
                    ["wmic", "computersystem", "get", "totalphysicalmemory", "/format:list"],
                    check=False,
                )
                if output:
                    mem_str = self._parse_wmic_list(output, "TotalPhysicalMemory")
                else:
                    output = run_command_with_output(
                        ["wmic", "computersystem", "get", "totalphysicalmemory"],
                        check=False,
                    )
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

                output = run_command_with_output(["sh", "-c", "vdpauinfo"], check=False)
                if output:
                    for line in output.split("\n"):
                        if "information string:" in line.lower():
                            backends["VDPAU"] = line.split(":")[1].strip()
                            break

                output = run_command_with_output(["sh", "-c", "vulkaninfo", "--summary"], check=False)
                if output:
                    for line in output.split("\n"):
                        if "driverName" in line:
                            match = re.search(r"=\s*(.+)", line)
                            if match:
                                backends["Vulkan"] = match.group(1).strip()
                                break

                nvdec_info = self._detect_nvdec()
                if nvdec_info:
                    backends["NVDEC"] = nvdec_info

                quicksync_info = self._detect_quicksync()
                if quicksync_info:
                    backends["QuickSync"] = quicksync_info

                v4l2_m2m_info = self._detect_v4l2_m2m()
                if v4l2_m2m_info:
                    backends["V4L2 M2M"] = v4l2_m2m_info

            elif self.os_name == "Darwin":
                try:
                    output = run_command_with_output(["sw_vers", "-productVersion"], check=False)
                    if output:
                        backends["VideoToolbox"] = f"macOS {output}"
                    else:
                        backends["VideoToolbox"] = "Available"
                except (OSError, ValueError):
                    backends["VideoToolbox"] = "Available"

            elif self.os_name == "Windows":
                directx_version = self._detect_directx()
                if directx_version:
                    backends["DirectX"] = directx_version

        except (OSError, ValueError):
            pass

        return backends

    @staticmethod
    def _detect_nvdec() -> Optional[str]:
        """Detect NVIDIA NVDEC hardware decoder (Linux only)"""
        try:
            output = run_command_with_output(["sh", "-c", "lspci | grep -iE '(VGA|3D|Display).*NVIDIA'"], check=False)
            if not output:
                return None

            nvidia_smi_output = run_command_with_output(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], check=False
            )
            if nvidia_smi_output:
                driver_version = nvidia_smi_output.strip().split("\n")[0]
                return f"Available (NVIDIA Driver {driver_version})"

            if os.path.exists("/dev/nvidia0"):
                return "Available"

        except (OSError, ValueError):
            pass

        return None

    def _detect_quicksync(self) -> Optional[str]:
        """Detect Intel QuickSync hardware decoder (Linux only)"""
        try:
            output = run_command_with_output(["sh", "-c", "lspci | grep -iE '(VGA|Display).*Intel'"], check=False)
            if not output:
                return None

            vaapi_info = self._get_vaapi_info()
            if not vaapi_info or "Intel" not in vaapi_info:
                return None

            candidates = [
                "libmfx.so.1",
                "libmfx.so",
                ctypes.util.find_library("mfx"),
                "libvpl.so.2",
                "libvpl.so",
                "libmfx-gen.so.1.2",
                "libmfx-gen.so.1.2.9",
            ]
            for lib_name in candidates:
                if not lib_name:
                    continue
                try:
                    ctypes.CDLL(lib_name)
                    return f"Available ({vaapi_info})"
                except OSError:
                    continue

        except (OSError, ValueError):
            pass

        return None

    @staticmethod
    def _v4l2_card_type(node: str) -> Optional[str]:
        """Return the V4L2 node's card type if it exposes the M2M capability, else None.

        Codecs expose themselves as V4L2 memory-to-memory (M2M) devices, reporting
        the ``Video Memory-to-Memory`` capability in their per-node ``Device Caps``.
        """
        output = run_command_with_output(["v4l2-ctl", "-d", node, "--info"], check=False)
        if not output:
            return None

        card = None
        in_device_caps = False
        is_m2m = False
        for line in output.split("\n"):
            stripped = line.strip()
            if stripped.startswith("Card type"):
                card = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Device Caps"):
                in_device_caps = True
            elif in_device_caps:
                # Capability entries are indented deeper than the "Device Caps"
                # header; a shallower line marks the end of the block.
                if line.startswith("\t\t"):
                    if "Memory-to-Memory" in stripped:
                        is_m2m = True
                else:
                    in_device_caps = False

        return card if is_m2m else None

    @staticmethod
    def _v4l2_is_decoder(node: str) -> bool:
        """Return True if the V4L2 M2M node is a decoder rather than an encoder.

        A decoder consumes a compressed bitstream on its OUTPUT queue and produces
        raw frames on its CAPTURE queue; an encoder does the reverse, exposing only
        compressed formats on CAPTURE. Note that a raw ``compressed`` band format
        (e.g. QCOM Q08C) can appear alongside NV12, so a device is treated as a
        decoder when its OUTPUT queue is compressed and its CAPTURE queue offers at
        least one uncompressed format.
        """

        def _has_compressed(args: List[str]) -> bool:
            output = run_command_with_output(["v4l2-ctl", "-d", node] + args, check=False)
            return bool(output) and any(
                "compressed" in line for line in output.split("\n") if re.match(r"\s*\[\d+\]:", line)
            )

        def _has_uncompressed(args: List[str]) -> bool:
            output = run_command_with_output(["v4l2-ctl", "-d", node] + args, check=False)
            return bool(output) and any(
                "compressed" not in line for line in output.split("\n") if re.match(r"\s*\[\d+\]:", line)
            )

        return _has_compressed(["--list-formats-out"]) and _has_uncompressed(["--list-formats"])

    @classmethod
    def _detect_v4l2_m2m(cls) -> Optional[str]:
        """Detect V4L2 memory-to-memory (M2M) decoder devices via v4l2-ctl (Linux only).

        Returns a human-readable list of decoder devices, or None when v4l2-ctl is
        unavailable or no M2M decoder is present.
        """
        try:
            listing = run_command_with_output(["v4l2-ctl", "-A"], check=False)
            if not listing:
                return None

            video_nodes = [line.strip() for line in listing.split("\n") if line.strip().startswith("/dev/video")]

            devices = []
            for node in video_nodes:
                card = cls._v4l2_card_type(node)
                if card is None or not cls._v4l2_is_decoder(node):
                    continue
                devices.append(f"{card} ({node})")

            if devices:
                return ", ".join(devices)
        except (OSError, ValueError):
            pass

        return None

    @staticmethod
    def _detect_directx() -> Optional[str]:
        """Detect DirectX version on Windows"""
        try:
            output = run_command_with_output(
                ["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\DirectX').Version"],
                check=False,
            )
            if output and output.strip():
                return f"DirectX {output.strip()}"

            system32_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")

            for version, dll_name in [("12", "d3d12.dll"), ("11", "d3d11.dll"), ("10", "d3d10.dll")]:
                dll_path = os.path.join(system32_path, dll_name)
                if os.path.exists(dll_path):
                    return f"DirectX {version} Available"

        except (OSError, ValueError):
            pass

        return None

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
