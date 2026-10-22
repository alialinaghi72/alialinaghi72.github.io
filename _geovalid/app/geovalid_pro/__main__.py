"""Entry point: no arguments → GUI; 'run' / 'sample' / --help → command line."""
import sys


def _attach_console() -> None:
    """A windowed Windows exe has no console; attach to the parent one so CLI output is visible."""
    if sys.platform == "win32" and (sys.stdout is None or not sys.stdout.isatty()):
        try:
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
                sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)
        except Exception:
            pass


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("run", "sample", "--help", "-h", "--version"):
        _attach_console()
        from .cli import main as cli_main
        return cli_main(sys.argv[1:])
    from .gui.app import main as gui_main
    return gui_main()


if __name__ == "__main__":
    sys.exit(main())
