import os
import yaml
import requests
import traceback
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# WattTime credentials and deployment location
WATTTIME_USERNAME = os.getenv("WATTTIME_USERNAME")
WATTTIME_PASSWORD = os.getenv("WATTTIME_PASSWORD")
DEPLOYMENT_LOCATION = os.getenv("DEPLOYMENT_LOCATION", "Bangalore")

# Map of known locations to coordinates
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

def get_watttime_token(username, password):
    print("Authenticating with WattTime...")
    login_url = 'https://api.watttime.org/login'
    response = requests.get(login_url, auth=HTTPBasicAuth(username, password), proxies={})
    response.raise_for_status()
    return response.json()['token']

def get_region_from_location(token, latitude, longitude):
    print("Fetching region from location...")
    url = 'https://api.watttime.org/v3/region-from-loc'
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'signal_type': 'co2_moer'
    }
    response = requests.get(url, headers=headers, params=params, proxies={})
    response.raise_for_status()
    return response.json()['region']

def fetch_grid_carbon_intensity(token, region):
    print("Fetching grid carbon intensity...")
    url = 'https://api.watttime.org/v3/signal'
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'region': region,
        'signal_type': 'co2_moer'
    }
    response = requests.get(url, headers=headers, params=params, proxies={})
    response.raise_for_status()
    data = response.json()['data']
    return data[0]['value'] if data else None

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

        token = get_watttime_token(WATTTIME_USERNAME, WATTTIME_PASSWORD)
        region = get_region_from_location(token, LATITUDE, LONGITUDE)
        carbon_intensity = fetch_grid_carbon_intensity(token, region)
        embodied_carbon = estimate_embodied_carbon()

        plugin_path = os.path.abspath(os.path.join(repo_path, "node_modules"))

        manifest = {
            'energy': {
                'kwh': energy_kwh,
                'carbon_intensity': carbon_intensity
            },
            'embodied_carbon': embodied_carbon,
            'requests': requests_count,
            'location': {
                'latitude': LATITUDE,
                'longitude': LONGITUDE,
                'region': region
            },
            'plugin_path': plugin_path
        }

        with open(output_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)

        print(f"✅ impact.yaml has been successfully generated at {output_path}")

    except Exception:
        print("❌ An error occurred during manifest generation:")
        traceback.print_exc()

# Run the script
if __name__ == "__main__":
    generate_manifest(repo_path='.')
