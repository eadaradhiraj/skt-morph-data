import subprocess
import sys

def test_cli_help():
    r = subprocess.run([sys.executable, "-m", "skt_morph_data.cli", "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "skt-morph" in r.stdout

def test_cli_list():
    r = subprocess.run([sys.executable, "-m", "skt_morph_data.cli", "list", "--gana", "01", "--limit", "2", "--json"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "01.0001" in r.stdout
