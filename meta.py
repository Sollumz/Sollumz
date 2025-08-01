def sollumz_version() -> str:
    CACHE_KEY = "_cached_version"
    if not (version := getattr(sollumz_version, CACHE_KEY, None)):
        import re
        from pathlib import Path
        addon_dir = Path(__file__).parent.absolute()
        manifest_path = addon_dir / "blender_manifest.toml"
        # tomllib is not included in Blender 4.0, so use some regex to get the version
        manifest = manifest_path.read_text()
        version_match = re.search(r'^version\s*=\s*\"([^\"]+)\"', manifest, re.MULTILINE)
        version = version_match.group(1) if version_match else "unknown version"
        if "$Format:%h$" in version:
            # When installed for development from a repo the manifest won't have the exact commit
            commit = "dirty"
            if (addon_dir / ".git").is_dir():
                try:
                    # Try to get the commit hash from git
                    import subprocess
                    commit = subprocess.check_output(
                        ["git", "-C", str(addon_dir), "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
                    dirty = bool(subprocess.check_output(["git", "-C", str(addon_dir), "status", "--porcelain"]))
                    if dirty:
                        commit += "-dirty"
                except Exception:
                    # Just ignore any error, simply append "dirty"
                    pass

            version = version.replace("$Format:%h$", commit)

        setattr(sollumz_version, CACHE_KEY, version)

    return version
