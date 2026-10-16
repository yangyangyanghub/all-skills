import json
import os

_SPECS_PATH = os.path.join(os.path.dirname(__file__), "..", "specs", "photo-specs.json")


def load_specs():
    with open(_SPECS_PATH, encoding="utf-8") as f:
        return json.load(f)["specs"]


def get_spec(key):
    for spec in load_specs():
        if spec["id"] == key or key in spec.get("aliases", []):
            return spec
    raise KeyError(f"unknown spec: {key}")


def list_specs():
    return load_specs()


if __name__ == "__main__":
    for spec in load_specs():
        print(f"{spec['id']:16s} {spec['name']:12s} {spec['mm'][0]}x{spec['mm'][1]}mm  {spec['px'][0]}x{spec['px'][1]}px @{spec['dpi']}dpi")
