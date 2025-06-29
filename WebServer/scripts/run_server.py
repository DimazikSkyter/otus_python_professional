import os
import subprocess

with open(".server.pid", "w") as f:
    proc = subprocess.Popen(["python", "webserver_src/httpd.py", "-r", "documents"])
    f.write(str(proc.pid))
