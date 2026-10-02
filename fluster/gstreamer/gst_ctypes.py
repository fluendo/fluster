# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
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

"""
ctypes bindings for GStreamer.

This module provides minimal ctypes bindings for GStreamer to run pipelines
without depending on the GStreamer Python bindings (gi.repository.Gst).
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import platform
from typing import NamedTuple, Optional, Tuple

# Platform-specific sizes
_POINTER_SIZE = ctypes.sizeof(ctypes.c_void_p)
_GSIZE = ctypes.c_uint64 if _POINTER_SIZE == 8 else ctypes.c_uint32
_GTYPE = _GSIZE  # GType is same size as gsize
_GQUARK = ctypes.c_uint32

# GStreamer type definitions
GST_STATE_VOID_PENDING = 0
GST_STATE_NULL = 1
GST_STATE_READY = 2
GST_STATE_PAUSED = 3
GST_STATE_PLAYING = 4

GST_STATE_CHANGE_FAILURE = 0
GST_STATE_CHANGE_SUCCESS = 1
GST_STATE_CHANGE_ASYNC = 2
GST_STATE_CHANGE_NO_PREROLL = 3

GST_MESSAGE_UNKNOWN = 0
GST_MESSAGE_EOS = 1 << 0
GST_MESSAGE_ERROR = 1 << 1
GST_MESSAGE_WARNING = 1 << 2
GST_MESSAGE_INFO = 1 << 3
GST_MESSAGE_TAG = 1 << 4
GST_MESSAGE_BUFFERING = 1 << 5
GST_MESSAGE_STATE_CHANGED = 1 << 6
GST_MESSAGE_STATE_DIRTY = 1 << 7
GST_MESSAGE_STEP_DONE = 1 << 8
GST_MESSAGE_CLOCK_PROVIDE = 1 << 9
GST_MESSAGE_CLOCK_LOST = 1 << 10
GST_MESSAGE_NEW_CLOCK = 1 << 11
GST_MESSAGE_STRUCTURE_CHANGE = 1 << 12
GST_MESSAGE_STREAM_STATUS = 1 << 13
GST_MESSAGE_APPLICATION = 1 << 14
GST_MESSAGE_ELEMENT = 1 << 15
GST_MESSAGE_SEGMENT_START = 1 << 16
GST_MESSAGE_SEGMENT_DONE = 1 << 17
GST_MESSAGE_DURATION_CHANGED = 1 << 18
GST_MESSAGE_LATENCY = 1 << 19
GST_MESSAGE_ASYNC_START = 1 << 20
GST_MESSAGE_ASYNC_DONE = 1 << 21
GST_MESSAGE_REQUEST_STATE = 1 << 22
GST_MESSAGE_STEP_START = 1 << 23
GST_MESSAGE_QOS = 1 << 24
GST_MESSAGE_PROGRESS = 1 << 25
GST_MESSAGE_TOC = 1 << 26
GST_MESSAGE_RESET_TIME = 1 << 27
GST_MESSAGE_STREAM_START = 1 << 28
GST_MESSAGE_NEED_CONTEXT = 1 << 29
GST_MESSAGE_HAVE_CONTEXT = 1 << 30
GST_MESSAGE_ANY = 0xFFFFFFFF

GST_CLOCK_TIME_NONE = 0xFFFFFFFFFFFFFFFF
GST_SECOND = 1000000000

GST_CORE_ERROR_MISSING_PLUGIN = 12
GST_STREAM_ERROR_NOT_IMPLEMENTED = 3
GST_STREAM_ERROR_CODEC_NOT_FOUND = 6

GST_FLOW_NOT_NEGOTIATED = -4

# GStreamer framework/installation paths
GST_FRAMEWORK_PATH_MACOS = "/Library/Frameworks/GStreamer.framework"
GST_FRAMEWORK_LIBRARIES_MACOS = f"{GST_FRAMEWORK_PATH_MACOS}/Libraries"
GST_FRAMEWORK_PLUGINS_MACOS = f"{GST_FRAMEWORK_PATH_MACOS}/Versions/Current/lib/gstreamer-1.0"

# Homebrew paths (Apple Silicon and Intel)
GST_HOMEBREW_PREFIX_ARM64 = "/opt/homebrew"
GST_HOMEBREW_PREFIX_X86_64 = "/usr/local"


class GErrorStruct(ctypes.Structure):
    """GLib GError structure."""

    _fields_ = [
        ("domain", _GQUARK),
        ("code", ctypes.c_int),
        ("message", ctypes.c_char_p),
    ]


class _GstMiniObject(ctypes.Structure):
    """Public fields of GstMiniObject.

    Only the field order and sizes matter here: ctypes derives the padding, so
    the struct matches the C layout on both 32- and 64-bit systems.
    """

    _fields_ = [
        ("type", _GTYPE),
        ("refcount", ctypes.c_int),
        ("lockstate", ctypes.c_int),
        ("flags", ctypes.c_uint),
        ("copy", ctypes.c_void_p),
        ("dispose", ctypes.c_void_p),
        ("free", ctypes.c_void_p),
        ("n_qdata", ctypes.c_uint),
        ("qdata", ctypes.c_void_p),
    ]


class _GstMessageHead(ctypes.Structure):
    """Leading public fields of GstMessage, enough to read GST_MESSAGE_TYPE()."""

    _fields_ = [("mini_object", _GstMiniObject), ("type", ctypes.c_uint)]


class GstMessageError(NamedTuple):
    """Structured GstMessage error details."""

    domain: int
    code: int
    message: str
    debug: str
    # "flow-return" from the error details, set by GST_ELEMENT_FLOW_ERROR.
    flow_return: Optional[int] = None


class GStreamerInstallation:
    """Detects and provides paths for GStreamer installation."""

    _instance: Optional["GStreamerInstallation"] = None

    def __new__(cls) -> "GStreamerInstallation":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Skip re-initialization if already detected
        if hasattr(self, "_detected"):
            return
        self._lib_path: Optional[str] = None
        self._plugin_path: Optional[str] = None
        self._bin_path: Optional[str] = None  # Windows only
        self._detected = self._detect()

    def _detect(self) -> bool:
        """Detect GStreamer installation based on platform."""
        system = platform.system()

        if system == "Darwin":
            return self._detect_macos()
        elif system == "Windows":
            return self._detect_windows()
        elif system == "Linux":
            return self._detect_linux()
        return False

    def _detect_macos(self) -> bool:
        """Detect GStreamer on macOS (Framework or Homebrew)."""
        # Check GStreamer Framework first
        if os.path.exists(GST_FRAMEWORK_PATH_MACOS):
            self._lib_path = GST_FRAMEWORK_LIBRARIES_MACOS
            self._plugin_path = GST_FRAMEWORK_PLUGINS_MACOS
            return True

        # Check Homebrew (Apple Silicon first, then Intel)
        for prefix in [GST_HOMEBREW_PREFIX_ARM64, GST_HOMEBREW_PREFIX_X86_64]:
            gst_lib = os.path.join(prefix, "lib", "libgstreamer-1.0.dylib")
            if os.path.exists(gst_lib):
                self._lib_path = os.path.join(prefix, "lib")
                plugin_path = os.path.join(self._lib_path, "gstreamer-1.0")
                if os.path.exists(plugin_path):
                    self._plugin_path = plugin_path
                return True

        return False

    def _detect_windows(self) -> bool:
        """Detect GStreamer on Windows."""
        gst_root = os.environ.get("GSTREAMER_1_0_ROOT_MSVC_X86_64") or os.environ.get("GSTREAMER_1_0_ROOT_X86_64")
        if gst_root and os.path.exists(gst_root):
            self._bin_path = os.path.join(gst_root, "bin")
            self._lib_path = self._bin_path  # On Windows, DLLs are in bin
            self._plugin_path = os.path.join(gst_root, "lib", "gstreamer-1.0")
            return True

        # Try common installation paths
        for path in [
            "C:\\gstreamer\\1.0\\msvc_x86_64",
            "C:\\gstreamer\\1.0\\x86_64",
        ]:
            if os.path.exists(path):
                self._bin_path = os.path.join(path, "bin")
                self._lib_path = self._bin_path
                self._plugin_path = os.path.join(path, "lib", "gstreamer-1.0")
                return True

        return False

    def _detect_linux(self) -> bool:
        """Detect GStreamer on Linux (uses system paths)."""
        # Linux typically uses system paths, no special detection needed
        # Libraries are found via ldconfig/LD_LIBRARY_PATH
        # Check if we can find the library via ctypes
        lib_path = ctypes.util.find_library("gstreamer-1.0")
        return lib_path is not None

    def find_library(self, name: str) -> Optional[str]:
        """Find a specific library by name."""
        system = platform.system()

        if system == "Darwin":
            if self._lib_path:
                lib_file = os.path.join(self._lib_path, f"lib{name}.dylib")
                if os.path.exists(lib_file):
                    return lib_file
            # Fallback to ctypes.util.find_library
            return ctypes.util.find_library(name)

        elif system == "Windows":
            if self._lib_path:
                # MSVC ships "glib-2.0-0.dll" while MinGW ships
                # "libglib-2.0-0.dll", so probe both spellings.
                for lib_name in (f"lib{name}-0.dll", f"{name}-0.dll", f"lib{name}.dll", f"{name}.dll"):
                    lib_file = os.path.join(self._lib_path, lib_name)
                    if os.path.exists(lib_file):
                        return lib_file
            # Fallback to ctypes.util.find_library
            return ctypes.util.find_library(name)

        elif system == "Linux":
            # Try ctypes.util.find_library first
            lib_path = ctypes.util.find_library(name)
            if lib_path:
                return lib_path
            # Try common paths
            for path in [f"lib{name}.so.0", f"lib{name}.so"]:
                try:
                    ctypes.CDLL(path)
                    return path
                except OSError:
                    continue

        return None

    def get_environment(self, base: Optional[dict[str, str]] = None) -> dict[str, str]:
        """Get environment variables needed to run GStreamer correctly.

        Args:
            base: Environment the returned variables will be applied on top of.
                Existing values (``PATH``, ``DYLD_LIBRARY_PATH``, ...) are read
                from it instead of the system environment so callers can pass a
                custom environment (e.g. a development setup) and have its
                variables preserved. Defaults to ``os.environ``.
        """
        source = os.environ if base is None else base
        env: dict[str, str] = {}
        system = platform.system()

        if system == "Darwin":
            if self._lib_path:
                current_dyld = source.get("DYLD_LIBRARY_PATH", "")
                if self._lib_path not in current_dyld:
                    env["DYLD_LIBRARY_PATH"] = f"{self._lib_path}:{current_dyld}" if current_dyld else self._lib_path
            if self._plugin_path:
                env["GST_PLUGIN_SYSTEM_PATH"] = self._plugin_path

        elif system == "Windows":
            if self._bin_path:
                current_path = source.get("PATH", "")
                if self._bin_path not in current_path:
                    env["PATH"] = f"{self._bin_path};{current_path}"
            if self._plugin_path:
                env["GST_PLUGIN_SYSTEM_PATH"] = self._plugin_path

        # Linux typically uses system paths, no special env needed

        return env


class GStreamerError(Exception):
    """Exception raised for GStreamer errors."""


class GstCtypes:
    """ctypes-based GStreamer bindings (singleton)."""

    _instance: Optional["GstCtypes"] = None

    def __new__(cls) -> "GstCtypes":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Skip re-initialization if already set up
        if hasattr(self, "_gst"):
            return
        self._gst: Optional[ctypes.CDLL] = None
        self._glib: Optional[ctypes.CDLL] = None
        self._gobject: Optional[ctypes.CDLL] = None
        self._initialized = False

    def _load_libraries(self) -> None:
        if self._gst is not None:
            return

        installation = GStreamerInstallation()

        # Find and load GLib first
        glib_path = installation.find_library("glib-2.0")
        if not glib_path:
            raise GStreamerError("Could not find GLib library")
        self._glib = ctypes.CDLL(glib_path)

        # Find and load GObject
        gobject_path = installation.find_library("gobject-2.0")
        if not gobject_path:
            raise GStreamerError("Could not find GObject library")
        self._gobject = ctypes.CDLL(gobject_path)

        # Find and load GStreamer
        gst_path = installation.find_library("gstreamer-1.0")
        if not gst_path:
            raise GStreamerError("Could not find GStreamer library")
        self._gst = ctypes.CDLL(gst_path)

        self._setup_function_signatures()

    def _setup_function_signatures(self) -> None:
        """Set up ctypes function signatures for GStreamer functions."""
        if self._gst is None or self._glib is None or self._gobject is None:
            return

        # GLib functions
        self._glib.g_free.argtypes = [ctypes.c_void_p]
        self._glib.g_free.restype = None

        # gst_init_check: argv is a nullable char** so it is declared as
        # c_void_p and passed as NULL, as fluster has no custom options.
        self._gst.gst_init_check.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self._gst.gst_init_check.restype = ctypes.c_int

        # gst_is_initialized
        self._gst.gst_is_initialized.argtypes = []
        self._gst.gst_is_initialized.restype = ctypes.c_int

        # gst_deinit
        self._gst.gst_deinit.argtypes = []
        self._gst.gst_deinit.restype = None

        # gst_parse_launch
        self._gst.gst_parse_launch.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        self._gst.gst_parse_launch.restype = ctypes.c_void_p

        # gst_element_set_state
        self._gst.gst_element_set_state.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._gst.gst_element_set_state.restype = ctypes.c_int

        # gst_element_get_bus
        self._gst.gst_element_get_bus.argtypes = [ctypes.c_void_p]
        self._gst.gst_element_get_bus.restype = ctypes.c_void_p

        # gst_bus_timed_pop_filtered
        self._gst.gst_bus_timed_pop_filtered.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint]
        self._gst.gst_bus_timed_pop_filtered.restype = ctypes.c_void_p

        # gst_message_get_structure
        self._gst.gst_message_get_structure.argtypes = [ctypes.c_void_p]
        self._gst.gst_message_get_structure.restype = ctypes.c_void_p

        # gst_structure_get_name
        self._gst.gst_structure_get_name.argtypes = [ctypes.c_void_p]
        self._gst.gst_structure_get_name.restype = ctypes.c_char_p

        # gst_structure_get_int
        self._gst.gst_structure_get_int.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
        self._gst.gst_structure_get_int.restype = ctypes.c_int

        # gst_message_parse_error
        self._gst.gst_message_parse_error.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self._gst.gst_message_parse_error.restype = None

        # gst_message_parse_error_details
        self._gst.gst_message_parse_error_details.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        self._gst.gst_message_parse_error_details.restype = None

        # gst_core_error_quark
        self._gst.gst_core_error_quark.argtypes = []
        self._gst.gst_core_error_quark.restype = _GQUARK

        # gst_stream_error_quark
        self._gst.gst_stream_error_quark.argtypes = []
        self._gst.gst_stream_error_quark.restype = _GQUARK

        # gst_message_parse_warning
        self._gst.gst_message_parse_warning.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self._gst.gst_message_parse_warning.restype = None

        # gst_message_unref
        self._gst.gst_message_unref.argtypes = [ctypes.c_void_p]
        self._gst.gst_message_unref.restype = None

        # gst_object_unref
        self._gst.gst_object_unref.argtypes = [ctypes.c_void_p]
        self._gst.gst_object_unref.restype = None

        # gst_structure_to_string
        self._gst.gst_structure_to_string.argtypes = [ctypes.c_void_p]
        self._gst.gst_structure_to_string.restype = ctypes.c_void_p

        # gst_error_get_message
        self._gst.gst_error_get_message.argtypes = [_GQUARK, ctypes.c_int]
        self._gst.gst_error_get_message.restype = ctypes.c_void_p

        # g_error_free
        self._glib.g_error_free.argtypes = [ctypes.c_void_p]
        self._glib.g_error_free.restype = None

    def _read_string(self, pointer: Optional[int]) -> str:
        """Read a NUL-terminated C string returned by GLib/GStreamer and free it.

        GStreamer helpers hand out strings owned by the caller, so the
        cast/decode/``g_free`` sequence is centralised here to keep the call
        sites short and to make sure the allocation is always released.
        """
        if not pointer:
            return ""
        if self._glib is None:
            raise GStreamerError("GStreamer not initialized")
        glib = self._glib

        value = ctypes.cast(pointer, ctypes.c_char_p).value
        glib.g_free(pointer)
        return value.decode("utf-8", errors="replace") if value else ""

    def _take_gerror(self, error_ptr: Optional[int]) -> Tuple[int, int, str]:
        """Read a GLib ``GError``, free it and return (domain, code, message)."""
        if not error_ptr:
            return 0, 0, ""
        if self._glib is None:
            raise GStreamerError("GStreamer not initialized")
        glib = self._glib

        gerror = ctypes.cast(error_ptr, ctypes.POINTER(GErrorStruct)).contents
        message = gerror.message.decode("utf-8", errors="replace") if gerror.message else ""
        domain, code = int(gerror.domain), int(gerror.code)
        glib.g_error_free(error_ptr)
        return domain, code, message

    def _decode_gerror(self, error_ptr: Optional[int]) -> str:
        """Describe a GLib ``GError`` and release it.

        The description combines the error message with the translated text of
        its domain/code, so callers can report why GStreamer failed instead of
        a generic message. The error is consumed (freed) by this function.
        """
        if not error_ptr:
            return ""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")

        domain, code, message = self._take_gerror(error_ptr)
        code_description = self._read_string(self._gst.gst_error_get_message(domain, code))

        if message and code_description and message != code_description:
            return f"{message} [{code_description}] (domain={domain}, code={code})"
        return message or code_description or f"domain={domain}, code={code}"

    def init(self) -> None:
        """Initialize GStreamer."""
        self._load_libraries()
        if self._gst is None:
            raise GStreamerError("GStreamer library not loaded")

        if self._gst.gst_is_initialized():
            self._initialized = True
            return

        argc = ctypes.c_int(0)
        error = ctypes.c_void_p()
        result = self._gst.gst_init_check(ctypes.byref(argc), None, ctypes.byref(error))

        if not result:
            detail = self._decode_gerror(error.value)
            if detail:
                raise GStreamerError(f"GStreamer initialization failed: {detail}")
            raise GStreamerError("GStreamer initialization failed")
        self._initialized = True

    def deinit(self) -> None:
        """Deinitialize GStreamer."""
        if self._gst is not None and self._initialized:
            self._gst.gst_deinit()
            self._initialized = False

    def parse_launch(self, pipeline_description: str) -> ctypes.c_void_p:
        """Parse and create a pipeline from a description string."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")

        error = ctypes.c_void_p()
        pipeline = self._gst.gst_parse_launch(pipeline_description.encode("utf-8"), ctypes.byref(error))

        if error.value:
            # gst_parse_launch() can report an error and still return a partially
            # built pipeline (e.g. when an element does not exist). The caller
            # never receives it, so it has to be released here or it leaks.
            self.object_unref(pipeline)
            detail = self._decode_gerror(error.value)
            error_msg = f"Failed to parse pipeline: {pipeline_description}"
            raise GStreamerError(f"{error_msg}: {detail}" if detail else error_msg)

        if not pipeline:
            raise GStreamerError(f"Failed to create pipeline: {pipeline_description}")

        return ctypes.cast(pipeline, ctypes.c_void_p)

    def element_set_state(self, element: ctypes.c_void_p, state: int) -> int:
        """Set the state of an element."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")
        return int(self._gst.gst_element_set_state(element, state))

    def element_get_bus(self, element: ctypes.c_void_p) -> ctypes.c_void_p:
        """Get the bus of an element."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")
        return ctypes.cast(self._gst.gst_element_get_bus(element), ctypes.c_void_p)

    def bus_timed_pop_filtered(
        self, bus: ctypes.c_void_p, timeout: int, message_types: int
    ) -> Optional[ctypes.c_void_p]:
        """Pop a message from the bus with a timeout and filter."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")
        msg = self._gst.gst_bus_timed_pop_filtered(bus, timeout, message_types)
        return msg if msg else None

    def message_get_type(self, message: Optional[ctypes.c_void_p]) -> int:
        """Get the type of a message.

        There is no exported function equivalent to the ``GST_MESSAGE_TYPE()``
        macro, so the field is read straight from the struct. Using a ctypes
        Structure lets ctypes compute the offset and padding for the current
        architecture. ``GstMessageType`` is an unsigned enum (extended types
        set the high bit), so it is read as unsigned to avoid sign-extension.
        A NULL message has no type and reports ``GST_MESSAGE_UNKNOWN``.
        """
        if not message:
            return GST_MESSAGE_UNKNOWN
        return int(ctypes.cast(message, ctypes.POINTER(_GstMessageHead)).contents.type)

    def core_error_quark(self) -> int:
        """Get the GStreamer core error quark."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")
        return int(self._gst.gst_core_error_quark())

    def stream_error_quark(self) -> int:
        """Get the GStreamer stream error quark."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")
        return int(self._gst.gst_stream_error_quark())

    def message_parse_error(self, message: ctypes.c_void_p) -> GstMessageError:
        """Parse an error message."""
        if self._gst is None or self._glib is None:
            raise GStreamerError("GStreamer not initialized")

        error = ctypes.c_void_p()
        debug = ctypes.c_void_p()
        self._gst.gst_message_parse_error(message, ctypes.byref(error), ctypes.byref(debug))

        domain, code, error_msg = self._take_gerror(error.value)
        return GstMessageError(
            domain, code, error_msg, self._read_string(debug.value), self._error_flow_return(message)
        )

    def _error_flow_return(self, message: ctypes.c_void_p) -> Optional[int]:
        """Return the "flow-return" detail of an error message, if it has one."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")

        # The details structure is owned by the message: do not free it.
        details = ctypes.c_void_p()
        self._gst.gst_message_parse_error_details(message, ctypes.byref(details))
        flow_return = ctypes.c_int()
        if details.value and self._gst.gst_structure_get_int(details, b"flow-return", ctypes.byref(flow_return)):
            return flow_return.value
        return None

    def message_parse_warning(self, message: ctypes.c_void_p) -> Tuple[str, str]:
        """Parse a warning message."""
        if self._gst is None or self._glib is None:
            raise GStreamerError("GStreamer not initialized")

        error = ctypes.c_void_p()
        debug = ctypes.c_void_p()
        self._gst.gst_message_parse_warning(message, ctypes.byref(error), ctypes.byref(debug))

        return self._take_gerror(error.value)[2], self._read_string(debug.value)

    def message_get_structure(self, message: ctypes.c_void_p) -> Optional[ctypes.c_void_p]:
        """Get the structure of a message."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")
        structure = self._gst.gst_message_get_structure(message)
        return structure if structure else None

    def structure_get_name(self, structure: ctypes.c_void_p) -> str:
        """Get the name of a structure (e.g. "missing-plugin")."""
        if self._gst is None:
            raise GStreamerError("GStreamer not initialized")
        name = ctypes.cast(self._gst.gst_structure_get_name(structure), ctypes.c_char_p)
        return name.value.decode("utf-8", errors="replace") if name.value else ""

    def structure_to_string(self, structure: ctypes.c_void_p) -> str:
        """Convert a structure to a string."""
        if self._gst is None or self._glib is None:
            raise GStreamerError("GStreamer not initialized")
        return self._read_string(self._gst.gst_structure_to_string(structure))

    def message_unref(self, message: ctypes.c_void_p) -> None:
        """Unref a message."""
        if self._gst is None:
            return
        if message:
            self._gst.gst_message_unref(message)

    def object_unref(self, obj: ctypes.c_void_p) -> None:
        """Unref an object."""
        if self._gst is None:
            return
        if obj:
            self._gst.gst_object_unref(obj)
