import sys

def main():
    """Entry point to launch DocuMind AI as a standalone desktop application."""
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Streamlit background server process when running frozen inside PyInstaller bundle
        from streamlit.web import cli as stcli
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        sys.exit(stcli.main())

    from src.desktop_launcher import launch_standalone_app
    launch_standalone_app()

if __name__ == "__main__":
    main()