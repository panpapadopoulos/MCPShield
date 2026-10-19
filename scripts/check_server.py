"""Start an owned local API process, verify HTTP/static assets, always stop it."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent

def main():
    # Bind an available ephemeral loopback port before launching the test process.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        port = sock.getsockname()[1]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    child = subprocess.Popen([sys.executable,"-m","uvicorn","shield.api:app","--host","127.0.0.1","--port",str(port)],
                             cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
    base = "http://127.0.0.1:" + str(port)
    try:
        for _ in range(50):
            if child.poll() is not None:
                raise RuntimeError("API process exited before readiness")
            try:
                with urlopen(base + "/api/health",timeout=1) as response:
                    assert json.load(response)["simulation_only"] is True
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError("API readiness timed out")
        with urlopen(base + "/",timeout=3) as response:
            html=response.read().decode()
        assert "MCPShield" in html
        import re
        assets=re.findall(r'(?:src|href)="(/assets/[^"]+)"',html)
        assert len(assets)>=2
        for asset in assets:
            with urlopen(base+asset,timeout=3) as response:
                assert response.status==200 and len(response.read())>0
        print("PASS: live Uvicorn health, dashboard HTML, and compiled JS/CSS assets")
    finally:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()

if __name__=="__main__":
    main()
