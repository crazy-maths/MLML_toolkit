import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "json_files")

PATHS = {
    "config": os.path.join(JSON_DIR, "config.json"),
    "signatures": os.path.join(JSON_DIR, "signatures.json"),
    "signature_morphisms": os.path.join(JSON_DIR, "signature_morphisms.json"),
    "lattices": os.path.join(JSON_DIR, "lattices.json"),
    "filtered_lattices": os.path.join(JSON_DIR, "filtered_lattices.json"),
    "many_lattices": os.path.join(JSON_DIR, "many_lattices.json"),
    "worlds": os.path.join(JSON_DIR, "worlds.json"),
    "kripke_frames": os.path.join(JSON_DIR, "kripke_frames.json"),
    "models": os.path.join(JSON_DIR, "models.json"),
    "kripke_frame_morphisms": os.path.join(JSON_DIR, "kripke_frame_morphisms.json"),
    "model_morphisms": os.path.join(JSON_DIR, "model_morphisms.json"),
    "assets": os.path.join(DATA_DIR, "assets")
}