import os
import yaml
import requests
import traceback

# Configuration
ELECTRICITYMAPS_API_TOKEN = "8UjTrDMM1u8JwZKisnm7"
DEPLOYMENT_LOCATION = "Bangalore"

location_map = {
    "Bangalore": (12.97, 77.59),
    "Delhi": (28.61, 77.20),
    "Mumbai": (19.07, 72.87),
    "Chennai": (13.08, 80.27),
    "Hyderabad": (17.38, 78.48)
}

LATITUDE, LONGITUDE = location_map.get(DEPLOYMENT_LOCATION, (12.97, 77.59))

def count_lines_of_code(repo_path):
    total_lines = 0
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".ts", ".js", ".py")):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        total_lines += sum(1 for line in f if line.strip())
                except Exception:
                    continue
    return total_lines

def count_requests(repo_path):
    request_count = 0
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".ts", ".js", ".py")):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        for line in f:
                            if 'fetch(' in line or 'axios.' in line or 'requests.' in line:
                                request_count += 1
                except Exception:
                    continue
    return request_count

def estimate_energy_usage(lines_of_code):
    return round(lines_of_code * 0.0001, 4)

def fetch_carbon_intensity(lat, lon, token):
    print("Fetching carbon intensity from Electricity Maps...")
    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?lat={lat}&lon={lon}"
    headers = {
        "auth-token": token
    }
    try:
        response = requests.get(url, headers=headers, proxies={})
        response.raise_for_status()
        data = response.json()
        return data.get("carbonIntensity")
    except Exception:
        print("⚠️ Could not fetch carbon intensity from API. Using default value 449.")
        return 449

def estimate_embodied_carbon(provider="aws", hardware="serverless"):
    if provider == "aws" and hardware == "serverless":
        return 950
    elif provider == "aws" and hardware == "vm":
        return 1200
    elif provider == "gcp":
        return 1000
    else:
        return 1100

def generate_manifest(repo_path, output_path='impact.yaml'):
    try:
        print("Counting lines of code...")
        lines_of_code = count_lines_of_code(repo_path)
        print(f"Lines of code: {lines_of_code}")

        print("Counting HTTP requests...")
        requests_count = count_requests(repo_path)
        print(f"HTTP requests found: {requests_count}")

        print("Estimating energy usage...")
        energy_kwh = estimate_energy_usage(lines_of_code)
        print(f"Estimated energy usage: {energy_kwh} kWh")

        carbon_intensity = fetch_carbon_intensity(LATITUDE, LONGITUDE, ELECTRICITYMAPS_API_TOKEN)
        print(f"Carbon intensity: {carbon_intensity} gCO2/kWh")

        embodied_carbon = estimate_embodied_carbon()

        plugin_path = '@grnsft/if-plugins/sci'

        manifest = {
            'name': 'next-calculator',
            'initialize': {
                'type': 'node',
                'path': '.',
                'plugins': {
                    'sci': {
                        'path': plugin_path,
                        'method': 'node'
                    }
                }
            },
            'tree': {
                'type': 'static',
                'nodes': [
                    {
                        'name': 'main',
                        'type': 'function',
                        'data': {
                            'requests': requests_count,
                            'energy': {
                                'kwh': energy_kwh,
                                'carbon_intensity': carbon_intensity
                            },
                            'embodied_carbon': embodied_carbon,
                            'location': {
                                'latitude': LATITUDE,
                                'longitude': LONGITUDE
                            },
                            'plugin_path': plugin_path
                        }
                    }
                ]
            }
        }

        with open(output_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)

        print(f"✅ impact.yaml has been successfully generated at {output_path}")

    except Exception:
        print("❌ An error occurred during manifest generation:")
        traceback.print_exc()

if __name__ == "__main__":
    generate_manifest(repo_path='.')
