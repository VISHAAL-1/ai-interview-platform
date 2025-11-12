import subprocess
import tempfile
import os
from .config import settings

def extract_opensmile_features(wav_path: str, config="IS09_emotion.conf"):
    """
    Calls OpenSMILE SMILExtract binary to extract features into CSV.
    Requires OpenSMILE installed and config file present.
    Returns path to CSV.
    """
    smil = settings.OPENSMMILE_PATH
    if not os.path.exists(smil):
        raise FileNotFoundError(f"OpenSMILE not found at {smil}")

    tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
    cmd = [smil, "-C", config, "-I", wav_path, "-O", tmp_csv]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"OpenSMILE failed: {proc.stderr}")
    return tmp_csv
