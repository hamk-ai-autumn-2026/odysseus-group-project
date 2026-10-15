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

def wait_for_server(url: str, timeout: float = 15.0, proc: subprocess.Popen = None) -> bool:
    """Polls local server URL until it responds, times out, or the process terminates."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if proc and proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def find_app_path() -> str:
    """Locates app.py across development and packaged environments."""
    # 1. Check parent of src/ (standard repository structure and site-packages layout)
    candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
    if os.path.isfile(candidate):
        return candidate
    # 2. Check current working directory
    candidate = os.path.abspath("app.py")
    if os.path.isfile(candidate):
        return candidate
    # 3. Fallback to candidate path for error reporting
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))

def launch_standalone_app():
    """Launches DocuMind AI in a standalone GUI window without opening a web browser."""
    port = find_free_port(8501)
    server_url = f"http://127.0.0.1:{port}"
    
    app_py_path = find_app_path()
    if not os.path.isfile(app_py_path):
        print(f"❌ Error: Could not locate 'app.py' at {app_py_path}")
        sys.exit(1)
    
    app_dir = os.path.dirname(app_py_path)
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{app_dir}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else app_dir
    
    # Force dark mode for embedded QtWebEngine Chromium renderer
    env["QTWEBENGINE_CHROMIUM_FLAGS"] = "--force-dark-mode"
    
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
        cwd=os.getcwd(),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    try:
        ready = wait_for_server(server_url, timeout=15.0, proc=proc)
        if not ready:
            if proc.poll() is not None:
                _, stderr = proc.communicate(timeout=2)
                err_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""
                print(f"❌ Server process exited prematurely with code {proc.returncode}.")
                if err_text:
                    print(f"Error details:\n{err_text}")
            else:
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
