import pexpect
import sys
import os
from pathlib import Path

def run_with_password(command, password):
    child = pexpect.spawn(command, timeout=600)
    # Output logic to show progress
    child.logfile_read = sys.stdout.buffer
    
    while True:
        try:
            # Expect either a password prompt or end of process
            index = child.expect(['[Pp]assword:', pexpect.EOF, pexpect.TIMEOUT])
            
            if index == 0:
                child.sendline(password)
            elif index == 1:
                break
            elif index == 2:
                print("\n[Error] Command timed out")
                sys.exit(1)
        except Exception as e:
            # If process ends before we see password prompt
            break
            
    child.close()
    return child.exitstatus

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vps_auth_helper.py 'command'")
        sys.exit(1)
        
    # Load password from .env.vps
    env_path = Path(__file__).resolve().parents[1] / ".env.vps"
    password = ""
    if env_path.exists():
        with open(env_path, "r") as f:
            line = f.readline()
            if "VPS_PASSWORD=" in line:
                password = line.split("=", 1)[1].strip().strip('"')
    
    if not password:
        print("[Error] VPS_PASSWORD not found in .env.vps")
        sys.exit(1)
        
    command = sys.argv[1]
    status = run_with_password(command, password)
    sys.exit(status)
