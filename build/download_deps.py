#!/usr/bin/env python3
# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#
# Helper script to download all ISO reference decoder dependencies
# Downloads: MPEG-2 AAC, MPEG-2 video, MPEG-4 AAC, and libtsp

import os
import shutil
import ssl
import subprocess
import sys
import tarfile
import zipfile
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen


def download_with_cookies(url, output_file, cookie_jar=None):
    """Download a file with cookie support"""
    if cookie_jar is None:
        cookie_jar = CookieJar()

    opener = build_opener(HTTPCookieProcessor(cookie_jar))

    print(f"Downloading {output_file.name}...")
    request = Request(url, data=b"ok=I+accept" if "ok=" not in url else None, headers={"User-Agent": "Mozilla/5.0"})

    with opener.open(request) as response:
        with open(output_file, "wb") as f:
            f.write(response.read())

    return cookie_jar


def extract_zip(zip_file, dest_dir):
    """Extract a zip file"""
    print(f"Extracting {zip_file.name}...")
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(dest_dir)


def extract_tar_gz(tar_file, dest_dir):
    """Extract a tar.gz file"""
    print(f"Extracting {tar_file.name}...")
    with tarfile.open(tar_file, "r:gz") as tar_ref:
        tar_ref.extractall(dest_dir)  # noqa: S202


def apply_patch(patch_file, target_dir):
    """Apply a patch file using patch command or git apply"""
    print(f"Applying patch: {patch_file.name}")

    # Try patch command first
    try:
        subprocess.run(["patch", "-d", str(target_dir), "-p1", "-i", str(patch_file)], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try git apply as fallback
    try:
        subprocess.run(
            ["git", "apply", "--directory", str(target_dir), str(patch_file)], check=True, capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Warning: Could not apply patch {patch_file.name}")
        return False


def check_patch_applied(file_path, marker):
    """Check if a patch has already been applied"""
    if not file_path.exists():
        return False
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return marker in f.read()


def download_mpeg2(contrib_dir):
    """Download MPEG-2 reference software (AAC and video)"""
    print()
    print("=== Downloading MPEG-2 reference software ===")

    cookie_jar = CookieJar()
    mpeg2_url = (
        "https://standards.iso.org/ittf/PubliclyAvailableStandards/c039486_ISO_IEC_13818-5_2005_Reference_Software.zip"
    )
    mpeg2_zip = contrib_dir / "c039486_ISO_IEC_13818-5_2005_Reference_Software.zip"

    # Get cookies first
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    opener.open(mpeg2_url)

    # Download with cookies and form data
    download_with_cookies(mpeg2_url, mpeg2_zip, cookie_jar)

    # Extract main archive
    extract_zip(mpeg2_zip, contrib_dir)
    mpeg2_zip.unlink()

    # Clean up unwanted files
    for unwanted in ["iso_cookies.txt", "ipmp.zip", "mpeg2audio.zip", "systems.zip"]:
        (contrib_dir / unwanted).unlink(missing_ok=True)

    # Extract MPEG-2 AAC
    print("Extracting MPEG-2 AAC...")
    mpeg2aac_zip = contrib_dir / "mpeg2aac.zip"
    extract_zip(mpeg2aac_zip, contrib_dir)
    mpeg2aac_zip.unlink()

    # Extract MPEG-2 video
    print("Extracting MPEG-2 video...")
    video_zip = contrib_dir / "video.zip"
    extract_zip(video_zip, contrib_dir)
    video_zip.unlink()


def download_mpeg4(contrib_dir):
    """Download MPEG-4 reference software"""
    print()
    print("=== Downloading MPEG-4 reference software ===")

    cookie_jar = CookieJar()
    mpeg4_url = "https://standards.iso.org/ittf/PubliclyAvailableStandards/c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip"
    mpeg4_zip = contrib_dir / "c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip"

    # Get cookies first
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    opener.open(mpeg4_url)

    # Download with cookies and form data
    download_with_cookies(mpeg4_url, mpeg4_zip, cookie_jar)

    # Extract archive
    extract_zip(mpeg4_zip, contrib_dir)
    mpeg4_zip.unlink()
    (contrib_dir / "iso_cookies.txt").unlink(missing_ok=True)

    # Create obj directory for MPEG-4 AAC build
    obj_dir = contrib_dir / "C050470e_Electronic_inserts" / "audio" / "natural" / "obj"
    obj_dir.mkdir(parents=True, exist_ok=True)


def download_libtsp(contrib_dir):
    """Download libtsp audio library"""
    print()
    print("=== Downloading libtsp audio library ===")

    libtsp_url = "https://www-mmsp.ece.mcgill.ca/Documents/Downloads/libtsp/libtsp-v7r0.tar.gz"
    libtsp_tar = contrib_dir / "libtsp-v7r0.tar.gz"

    # Create an SSL context that does not verify certificates using the public API
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    request = Request(libtsp_url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, context=ssl_context) as response:
        with open(libtsp_tar, "wb") as f:
            f.write(response.read())

    # Extract archive
    extract_tar_gz(libtsp_tar, contrib_dir)
    libtsp_tar.unlink()

    # Set permissions (on Unix systems)
    if os.name != "nt":
        os.chmod(contrib_dir / "libtsp-v7r0", 0o755)


def main():
    # Get script directory and calculate paths
    script_dir = Path(__file__).parent.resolve()
    root_dir = script_dir.parent

    # Get contrib directory from argument or default
    contrib_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else root_dir / "contrib"
    contrib_dir = contrib_dir.resolve()

    subprojects_dir = root_dir / "subprojects"
    packagefiles_dir = subprojects_dir / "packagefiles"

    print("=== Fluster Dependencies Download Script ===")
    print("This script will download ISO reference software for:")
    print("  - MPEG-2 AAC decoder")
    print("  - MPEG-2 video decoder")
    print("  - MPEG-4 AAC decoders")
    print("  - libtsp audio library")
    print()

    # Create contrib directory
    contrib_dir.mkdir(parents=True, exist_ok=True)

    # Download dependencies
    download_mpeg2(contrib_dir)
    download_mpeg4(contrib_dir)
    download_libtsp(contrib_dir)

    # Copy meson.build files to contrib directories
    print()
    print("=== Setting up meson build files ===")

    print("Copying meson.build for MPEG-2 video")
    shutil.copy2(packagefiles_dir / "mpeg2video" / "meson.build", contrib_dir / "video" / "meson.build")

    print("Copying meson.build for MPEG-2 AAC")
    shutil.copy2(packagefiles_dir / "mpeg2aac" / "meson.build", contrib_dir / "mpeg2aac" / "meson.build")

    # Copy compat headers
    print("Copying compat headers for MPEG-2 AAC")
    compat_src = script_dir / "compat" / "macos"
    compat_dst = contrib_dir / "mpeg2aac" / "compat"
    shutil.copytree(compat_src, compat_dst)

    print("Copying meson.build for libtsp")
    shutil.copy2(packagefiles_dir / "libtsp" / "meson.build", contrib_dir / "libtsp-v7r0" / "meson.build")

    # Create symlinks for meson subprojects
    print()
    print("=== Creating symlinks for meson subprojects ===")

    symlinks = [
        ("mpeg2video", "../contrib/video"),
        ("mpeg2aac", "../contrib/mpeg2aac"),
        ("libtsp-v7r0", "../contrib/libtsp-v7r0"),
    ]

    for link_name, target in symlinks:
        link_path = subprojects_dir / link_name
        # Remove existing symlink if it's broken
        if link_path.is_symlink() and not link_path.exists():
            print(f"Removing broken symlink: subprojects/{link_name}")
            link_path.unlink()

        if not link_path.exists():
            print(f"Creating symlink: subprojects/{link_name} -> {target}")
            # On Windows, try symlink first, fall back to junction
            try:
                link_path.symlink_to(target)
            except (OSError, NotImplementedError):
                if os.name == "nt":
                    # Use junction on Windows if symlink fails
                    subprocess.run(
                        ["mklink", "/J", str(link_path), str(link_path.parent / target)], shell=True, check=True
                    )
                else:
                    raise

    # Apply patches to MPEG-4 AAC
    print()
    print("=== Patching MPEG-4 AAC ===")

    mpeg4_dir = contrib_dir / "C050470e_Electronic_inserts" / "audio" / "natural"
    patches_dir = script_dir / "patches"

    apply_patch(patches_dir / "mpeg4aac-windows-headers.patch", contrib_dir / "C050470e_Electronic_inserts")
    apply_patch(patches_dir / "mpeg4aac-darwin.patch", mpeg4_dir)
    apply_patch(patches_dir / "mpeg4aac-ar-fix.patch", mpeg4_dir)
    apply_patch(patches_dir / "mpeg4aac-sed-fix.patch", mpeg4_dir)

    print()
    print("=== All dependencies downloaded successfully! ===")
    print("You can now run: meson setup builddir")


if __name__ == "__main__":
    main()
