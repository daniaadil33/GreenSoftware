import os
import yaml

# Path to your local repo
repo_path = "."

# Count lines of code in .js, .ts, .tsx files
def count_lines_of_code(path):
    loc = 0
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith((".js", ".ts", ".tsx")):
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        loc += sum(1 for line in f if line.strip())
                except Exception:
                    pass
    return loc

# Estimate energy usage based on LOC
def estimate_energy(loc):
    return round(loc * 0.0005, 3)  # 0.0005 kWh per line

# Count functional units (e.g., API endpoints)
def count_requests(path):
    count = 0
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".ts") and "api" in root:
                count += 1
    return count if count > 0 else 100

# Extract values
loc = count_lines_of_code(repo_path)
energy = estimate_energy(loc)
requests = count_requests(repo_path)
grid_intensity = 300
embodied_carbon = 950

# Create impact.yaml
manifest = {
    "schema": 1,
    "name": "SCI Calculation for Next Calculator",
    "description": "Dynamically calculate SCI using extracted values",
    "initialize": {
        "plugins": {
            "extract": {
                "method": "MockObservations",
                "path": "mock-observations",
                "config": {
                    "observations": {
                        "energy": energy,
                        "grid/carbon-intensity": grid_intensity,
                        "embodied-carbon": embodied_carbon,
                        "requests": requests
                    }
                }
            },
            "sci-o": {
                "method": "SCI-O",
                "path": "sci-o"
            },
            "sci-m": {
                "method": "SCI-M",
                "path": "sci-m"
            },
            "sci": {
                "method": "SCI",
                "path": "sci",
                "config": {
                    "functional-unit": "requests",
                    "functional-unit-time": "1 day"
                }
            }
        }
    },
    "tree": {
        "children": {
            "main": {
                "pipeline": {
                    "compute": ["extract", "sci-o", "sci-m", "sci"]
                }
            }
        }
    },
    "output": {
        "format": "json"
    }
}

# Save to impact.yaml
with open("impact.yaml", "w") as f:
    yaml.dump(manifest, f, sort_keys=False)

print("impact.yaml generated successfully.")
print(f"Lines of Code: {loc}, Energy: {energy} kWh, Requests: {requests}")
