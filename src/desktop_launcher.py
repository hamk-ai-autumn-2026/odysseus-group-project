import sys
import os
import time
import socket
import subprocess
import urllib.request
import webview

def find_free_port(default_port: int = 8501) -> int:
    """Finds an available local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", default_port))
            return default_port
        except OSError:
            # Port in use, request open port from OS
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

def wait_for_server(url: str, timeout: float = 15.0) -> bool:
    """Polls local server URL until it responds or times out."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def launch_standalone_app():
    """Launches DocuMind AI in a standalone GUI window without opening a web browser."""
    port = find_free_port(8501)
    server_url = f"http://127.0.0.1:{port}"
    
    # Root dir of project
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app_py_path = os.path.join(root_dir, "app.py")
    
    # Force dark mode for embedded QtWebEngine Chromium renderer
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--force-dark-mode"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_py_path,
        "--server.port", str(port),
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
        "--theme.base", "dark",
        "--theme.primaryColor", "#8b5cf6",
        "--theme.backgroundColor", "#0f172a",
        "--theme.secondaryBackgroundColor", "#1e293b",
        "--theme.textColor", "#f8fafc",
        "--server.runOnSave", "false",
        "--browser.gatherUsageStats", "false",
        "--global.developmentMode", "false"
    ]
    
    print(f"🚀 Starting DocuMind AI local server on port {port}...")
    proc = subprocess.Popen(
        cmd,
        cwd=root_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    try:
        ready = wait_for_server(server_url, timeout=15.0)
        if not ready:
            print("⚠️ Server launch timed out. Terminating background process.")
            proc.terminate()
            sys.exit(1)
            
        print("✨ Server ready! Opening standalone window...")
        
        # Create pywebview standalone window
        window = webview.create_window(
            title="DocuMind AI - Local Document Intelligence",
            url=server_url,
            width=1340,
            height=900,
            resizable=True,
            min_size=(960, 640),
            text_select=True,
            confirm_close=False
        )
        
        # Start webview loop using Qt GUI backend (blocks until user closes window)
        try:
            webview.start(gui="qt", private_mode=False)
        except Exception:
            webview.start(private_mode=False)
        
    finally:
        print("🛑 Closing standalone window and shutting down server process...")
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("👋 DocuMind AI shutdown complete.")

if __name__ == "__main__":
    launch_standalone_app()
