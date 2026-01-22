import warnings 
   
    @default("inkscape")
    def _inkscape_default(self):
        # Windows: Secure registry lookup FIRST (CVE-2025-53000 fix)
        if sys.platform == "win32":
            wr_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            try:
                rkey = winreg.OpenKey(wr_handle, r"SOFTWARE\Classes\inkscape.svg\DefaultIcon")
                inkscape_full = winreg.QueryValueEx(rkey, "")[0].split(",")[0]  # Fix: remove ",0"
                if os.path.isfile(inkscape_full):
                    return inkscape_full
            except (FileNotFoundError, OSError, IndexError):
                pass  # Safe fallback

        # Block CWD in PATH search (CVE-2025-53000)
        os.environ["NODEFAULTCURRENTDIRECTORYINEXEPATH"] = "1"

        # Resolve inkscape via shutil.which
        if sys.platform == "win32":
            inkscape_path = which("inkscape.com") or which("inkscape.exe")
        else:
            inkscape_path = which("inkscape")

        # Extra safety for Python < 3.12 on Windows:
        # If which() resolved to a path in CWD even though CWD is not on PATH,
        # warn and treat as "not found".
        if sys.platform == "win32" and inkscape_path and sys.version_info < (3, 12):
            try:
                cwd = os.path.realpath(os.getcwd())
                resolved = os.path.realpath(inkscape_path)
                in_cwd = os.path.commonpath([cwd, resolved]) == cwd

                # Determine whether CWD is explicitly on PATH ("" and "." count as CWD)
                path_entries = os.environ.get("PATH", "").split(os.pathsep)
                cwd_on_path = any(
                    (p in ("", ".") or os.path.realpath(os.path.expandvars(p.strip('"'))) == cwd)
                    for p in path_entries
                    if p is not None
                )

                if in_cwd and not cwd_on_path:
                    
                    warnings.warn(
                        "shutil.which('inkscape') resolved to an executable in the current "
                        "working directory even though CWD is not on PATH. Ignoring this "
                        "result for security reasons (CVE-2025-53000).",
                        RuntimeWarning,
                        stacklevel=2,
                    )
                    inkscape_path = None
            except Exception:
                # If detection fails for any reason, prefer safety: ignore CWD result
                inkscape_path = None

        if inkscape_path is not None:
            return inkscape_path

        # macOS: EXACT original order preserved
        if sys.platform == "darwin":
            if os.path.isfile(INKSCAPE_APP_v1):
                return INKSCAPE_APP_v1
            # Order is important. If INKSCAPE_APP exists, prefer it over
            # the executable in the MacOS directory.
            if os.path.isfile(INKSCAPE_APP):
                return INKSCAPE_APP

        msg = "Inkscape executable not found in safe paths"
        raise FileNotFoundError(msg)