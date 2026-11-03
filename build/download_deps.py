#!/usr/bin/env python3
# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#
# Helper script to download all ISO reference decoder dependencies
# Downloads: MPEG-2 AAC, MPEG-2 video, MPEG-4 AAC, MPEG-H, MPEG-4 Visual, and libtsp

import argparse
import hashlib
import os
import re
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


def download_mpegh(contrib_dir):
    """Download the MPEG-H 3D Audio (ISO/IEC 23008-6) reference software"""
    print()
    print("=== Downloading MPEG-H 3D Audio reference software ===")

    mpegh_dir = contrib_dir / "MPEG-H_3DA_refSoft"
    mpegh_url = "https://standards.iso.org/iso-iec/23008/-6/ed-4/en/refSoft_src.zip"
    mpegh_zip = contrib_dir / "refSoft_src.zip"

    if mpegh_dir.exists():
        print(f"Skipping MPEG-H 3D Audio: {mpegh_dir} already exists")
        return

    request = Request(mpegh_url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response:
        mpegh_zip.write_bytes(response.read())
    extract_zip(mpegh_zip, contrib_dir)
    mpegh_zip.unlink()
    next(contrib_dir.glob("MPEG-H_3DA_refSoft_src_*")).rename(mpegh_dir)

    # GCC 13 rejects the Visual Studio "#pragma region" lines placed between an if block and its else
    spatial_decoder = mpegh_dir / "modules/hoaCoder/spatialCoder/spatialDecoding/src/SpatialDecoder.cpp"
    source = spatial_decoder.read_text(encoding="utf-8", errors="ignore")
    spatial_decoder.write_text(re.sub(r"^[ \t]*#pragma (end)?region.*\n", "", source, flags=re.M), encoding="utf-8")


# Forward declarations that would clash with the std:: names brought in by the compat header
MPEG4_VIDEO_FORWARD_DECLARATION = re.compile(
    rb"^[ \t]*class[ \t]+(istream|ostream|ifstream|strstreambuf)[ \t]*;[ \t]*\r?\n", re.M
)
# "ios::bin" is the pre-standard spelling of "ios::binary"
MPEG4_VIDEO_IOS_BIN = re.compile(rb"\bios::bin\b")


def adapt_mpeg4_video_sources(source_dir):
    """Adapt the MPEG-4 Visual reference software, which predates C++98, to build with current compilers"""
    for path in source_dir.rglob("*"):
        if not path.is_file() or path.suffix not in (".c", ".cpp", ".h", ".hpp"):
            continue
        original = path.read_bytes()
        adapted = MPEG4_VIDEO_IOS_BIN.sub(b"ios::binary", MPEG4_VIDEO_FORWARD_DECLARATION.sub(b"", original))
        if adapted != original:
            path.write_bytes(adapted)


def download_mpeg4_video(contrib_dir):
    """Download the MPEG-4 Visual (ISO/IEC 14496-5) reference software, which builds vm_dec"""
    print()
    print("=== Downloading MPEG-4 Visual reference software ===")

    mpeg4_video_dir = contrib_dir / "MPEG-4_video_refSoft"
    mpeg4_video_zip = contrib_dir / "mpeg4_video_refsoft.zip"
    mpeg4_video_url = (
        "https://standards.iso.org/ittf/PubliclyAvailableStandards/"
        "c039392_ISO_IEC_14496-5_2001_Amd%205_2004(E)_Reference_Software.zip"
    )
    # The zip holds several implementations, only this one produces vm_dec
    implementation = "microsoft-v2.5-040207-NTU/"

    if mpeg4_video_dir.exists():
        print(f"Skipping download of MPEG-4 Visual: {mpeg4_video_dir} already exists")
        # Re-apply the source rewrites, in case the tree was extracted before they were added
        adapt_mpeg4_video_sources(mpeg4_video_dir)
        return

    # Get cookies first, then download with cookies and form data
    cookie_jar = CookieJar()
    build_opener(HTTPCookieProcessor(cookie_jar)).open(mpeg4_video_url)
    download_with_cookies(mpeg4_video_url, mpeg4_video_zip, cookie_jar)
    if not zipfile.is_zipfile(mpeg4_video_zip):
        print(f"Error: {mpeg4_video_zip.name} is not a zip file, the download was probably refused")
        sys.exit(1)

    print(f"Extracting {implementation} from {mpeg4_video_zip.name}...")
    # Extract into a temporary directory renamed once complete, so that an interrupted run
    # never leaves a partial MPEG-4_video_refSoft behind
    tmp_dir = contrib_dir / f".{mpeg4_video_dir.name}.tmp"
    shutil.rmtree(tmp_dir, ignore_errors=True)
    with zipfile.ZipFile(mpeg4_video_zip) as zip_ref:
        for member in zip_ref.infolist():
            _, found, relative_path = member.filename.partition(implementation)
            if not found or not relative_path or ".." in Path(relative_path).parts:
                continue
            target = tmp_dir / relative_path
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zip_ref.read(member))
    mpeg4_video_zip.unlink()
    if not tmp_dir.exists():
        print(f"Error: {implementation} not found in the downloaded MPEG-4 Visual reference software")
        sys.exit(1)
    adapt_mpeg4_video_sources(tmp_dir)
    tmp_dir.rename(mpeg4_video_dir)


def download_libtsp(contrib_dir):
    """Download libtsp audio library"""
    print()
    print("=== Downloading libtsp audio library ===")

    libtsp_dir = contrib_dir / "libtsp-v7r0"
    libtsp_url = "https://www-mmsp.ece.mcgill.ca/Documents/Downloads/libtsp/libtsp-v7r0.tar.gz"
    libtsp_tar = contrib_dir / "libtsp-v7r0.tar.gz"
    expected_md5 = "16dd8d9e7bcfed773982f11d9269ce24"

    # Skip download if already present and tarball MD5 matches
    if libtsp_dir.exists() and libtsp_tar.exists():
        actual_md5 = hashlib.md5(libtsp_tar.read_bytes()).hexdigest()
        if actual_md5 == expected_md5:
            print(f"Skipping libtsp: {libtsp_dir} already exists (MD5 verified)")
            _fix_libtsp_permissions(libtsp_dir)
            return
        print("MD5 mismatch on cached tarball, re-downloading...")

    # Create an SSL context that does not verify certificates using the public API
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    request = Request(libtsp_url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, context=ssl_context) as response:
        data = response.read()
        with open(libtsp_tar, "wb") as f:
            f.write(data)

    # Verify MD5 checksum
    actual_md5 = hashlib.md5(data).hexdigest()
    if actual_md5 != expected_md5:
        print(f"MD5 checksum mismatch for {libtsp_tar.name}:")
        print(f"  Expected: {expected_md5}")
        print(f"  Got:      {actual_md5}")
        libtsp_tar.unlink()
        sys.exit(1)
    print(f"MD5 checksum verified: {actual_md5}")

    # Extract archive
    extract_tar_gz(libtsp_tar, contrib_dir)
    libtsp_tar.unlink()

    # Fix permissions (the tarball ships read-only files)
    _fix_libtsp_permissions(libtsp_dir)


def _fix_libtsp_permissions(libtsp_dir):
    """Ensure files and directories under libtsp_dir are writable."""
    if os.name != "nt":
        subprocess.run(["chmod", "-R", "u+rwx", str(libtsp_dir)], check=True)


def create_subproject_link(link_path, target):
    """Create a directory link from subprojects/ to a local source tree.

    Windows distinguishes file and directory links. ``symlink_to`` defaults to
    a file symlink there, which Meson cannot use as a subproject directory; it
    then falls back to the stub .wrap file, which has no source_filename to
    download. Use a junction on Windows and a symlink elsewhere.
    """
    # Remove an existing broken or wrong-type link, but leave a valid directory
    # (including a junction) in place.
    if link_path.is_symlink() and not link_path.is_dir():
        print(f"Removing invalid subproject link: {link_path}")
        link_path.unlink()

    if link_path.exists():
        if not link_path.is_dir():
            print(f"Error: {link_path} exists but is not a directory")
            sys.exit(1)
        return

    print(f"Creating subproject link: {link_path} -> {target}")
    if os.name == "nt":
        # Junctions do not need developer mode or SeCreateSymbolicLinkPrivilege
        # and are always treated as directories by Meson. cmd.exe needs native
        # Windows paths, so normalize the separators before invoking mklink.
        # cmd.exe treats forward slashes in paths as switches (e.g. D:/a/...),
        # so force native separators even if pathlib produced a POSIX-looking
        # path under MSYS2.
        link_arg = os.path.normpath(str(link_path)).replace("/", "\\")
        target_arg = os.path.normpath(str((link_path.parent / target).resolve())).replace("/", "\\")
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", link_arg, target_arg],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            print(f"Error: could not create junction {link_arg} -> {target_arg}")
            sys.exit(1)
    else:
        link_path.symlink_to(target)

    if not link_path.is_dir():
        print(f"Error: {link_path} was not created as a directory")
        sys.exit(1)


def prompt_iso_license(auto_accept=False):
    """Prompt the user to accept the ISO licence agreement before downloading.

    Args:
        auto_accept: If True, skip the interactive prompt and accept automatically.
    """
    license_text = """
International Organization for Standardization

Licence Agreement for Publicly Available Standards

You are about to download a document protected by copyright.
When you download (an) ISO publication(s) from this site, you must accept the
ISO Customer Licence Agreement ("Licence Agreement"), excluding clauses
2. Watermark, 5. Paper copies, and 6. Codes and Graphical Symbols (and their
Collections).

See: https://www.iso.org/terms-conditions-licence-agreement.html#Customer-Licence

Should you have any questions about this Licence Agreement, please contact:
copyright@iso.org

"""
    if auto_accept:
        print(license_text)
        print("Licence accepted (via --accept-license).\n")
        return True

    print(license_text)
    while True:
        response = input("Do you accept the ISO Licence Agreement? [y/N]: ").strip().lower()
        if response in ("y", "yes"):
            print("Licence accepted.\n")
            return True
        if response in ("", "n", "no"):
            print("Licence not accepted. Cannot download ISO reference software.")
            return False
        print("Please answer 'y' or 'n'.")


def main():
    parser = argparse.ArgumentParser(
        description="Download ISO reference decoder dependencies "
        "(MPEG-2 AAC, MPEG-2 video, MPEG-4 AAC, MPEG-H, MPEG-4 Visual, libtsp)"
    )
    parser.add_argument(
        "dest_dir",
        nargs="?",
        type=Path,
        help="Destination directory for downloaded dependencies (default: <repo_root>/contrib)",
    )
    parser.add_argument(
        "--accept-license",
        action="store_true",
        help="Accept the ISO Licence Agreement non-interactively",
    )
    args = parser.parse_args()

    # Get script directory and calculate paths
    script_dir = Path(__file__).parent.resolve()
    root_dir = script_dir.parent

    # Get contrib directory from argument or default
    contrib_dir = (args.dest_dir or root_dir / "contrib").resolve()

    subprojects_dir = root_dir / "subprojects"
    packagefiles_dir = subprojects_dir / "packagefiles"

    print("=== Fluster Dependencies Download Script ===")
    print("This script will download ISO reference software for:")
    print("  - MPEG-2 AAC decoder")
    print("  - MPEG-2 video decoder")
    print("  - MPEG-4 AAC decoders")
    print("  - MPEG-H 3D Audio decoder")
    print("  - MPEG-4 Visual decoder")
    print("  - libtsp audio library")
    print()

    # Prompt user to accept ISO licence before downloading
    if not prompt_iso_license(auto_accept=args.accept_license):
        sys.exit(1)

    # Create contrib directory
    contrib_dir.mkdir(parents=True, exist_ok=True)

    # Download dependencies
    download_mpeg2(contrib_dir)
    download_mpeg4(contrib_dir)
    download_mpegh(contrib_dir)
    download_mpeg4_video(contrib_dir)
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
    shutil.copytree(compat_src, compat_dst, dirs_exist_ok=True)

    print("Copying meson.build for libtsp")
    shutil.copy2(packagefiles_dir / "libtsp" / "meson.build", contrib_dir / "libtsp-v7r0" / "meson.build")

    print("Copying meson.build for MPEG-4 Visual")
    shutil.copy2(packagefiles_dir / "mpeg4video" / "meson.build", contrib_dir / "MPEG-4_video_refSoft" / "meson.build")

    # Create symlinks for meson subprojects
    print()
    print("=== Creating symlinks for meson subprojects ===")

    symlinks = [
        ("mpeg2video", "../contrib/video"),
        ("mpeg2aac", "../contrib/mpeg2aac"),
        ("mpeg4video", "../contrib/MPEG-4_video_refSoft"),
        ("libtsp-v7r0", "../contrib/libtsp-v7r0"),
    ]

    for link_name, target in symlinks:
        create_subproject_link(subprojects_dir / link_name, target)

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
