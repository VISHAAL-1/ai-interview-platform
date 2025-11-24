import csv
import subprocess
import tempfile
import os
from .config import settings

def extract_opensmile_features(wav_path: str):
    """
    Extract jitter, shimmer, loudness, and voicing
    using OpenSMILE emobase.conf.
    """

    smil_path = settings.OPENSMILE_PATH
    config_path = settings.OPENSMILE_CONFIG_PATH

    if not os.path.isfile(smil_path):
        raise FileNotFoundError(f"Opensmile processed")

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Opensmile processed")

    # Temporary output CSV file
    tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name

    cmd = [
        smil_path,
        "-C", config_path,
        "-I", wav_path,
        "-O", tmp_csv,
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError("Opensmile processed")

    # Parse CSV
    with open(tmp_csv, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    os.remove(tmp_csv)

    if not rows:
        raise ValueError("OpenSMILE CSV empty – config may not output features.")

    row = rows[0]

    return {
        "jitter": float(row.get("jitterLocal_sma", 0)),
        "shimmer": float(row.get("shimmerLocal_sma", 0)),
        "loudness": float(row.get("pcm_intensity_sma", 0)),
        "voicing": float(row.get("voicingFinalUnclipped_sma", 0)),
    }
