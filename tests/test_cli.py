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

def test_cli_decline_formats():
    for fmt, marker in [
        ("table", "vibhakti"),
        ("markdown", "| vibhakti | ekavacana |"),
        ("html", '<table class="subanta-table">'),
        ("csv", "vibhakti,ekavacana,dvivacana,bahuvacana"),
        ("latex", "\\begin{tabular}"),
        ("anki", "rAma [m] - prathamA ekavacana\trAmaH\tsubanta:a_m"),
        ("json", '"forms"'),
    ]:
        r = subprocess.run([sys.executable, "-m", "skt_morph_data.cli", "decline", "rAma", "--gender", "m", "--format", fmt], capture_output=True, text=True)
        assert r.returncode == 0, f"Failed for format {fmt}: {r.stderr}"
        assert marker in r.stdout, f"Marker '{marker}' not in stdout for format {fmt}"

def test_cli_decline_participle_anki():
    r = subprocess.run([sys.executable, "-m", "skt_morph_data.cli", "decline-participle", "BU", "ktavatu", "--gender", "m", "-f", "anki"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "krdanta:ktavatu" in r.stdout
    assert "BUtavAn" in r.stdout

def test_cli_analyze_participle():
    r = subprocess.run([sys.executable, "-m", "skt_morph_data.cli", "analyze", "BUtavatA"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "participle_decl" in r.stdout
    assert "BU" in r.stdout
    assert "ktavatu" in r.stdout

def test_cli_purvadi():
    r = subprocess.run([sys.executable, "-m", "skt_morph_data.cli", "decline", "pUrva", "--category", "pronoun", "--gender", "m"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "pUrve / pUrvAH" in r.stdout
    assert "pUrvasmAt / pUrvAt" in r.stdout
