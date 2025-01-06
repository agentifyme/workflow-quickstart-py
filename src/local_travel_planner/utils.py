import httpx
from bs4 import BeautifulSoup


def fetch_external_url_content(url):
    """
    Fetches and extracts meaningful content from an external URL.
    """
    try:
        response = httpx.get(url, headers={"User-Agent": "travel-planner-app/0.1"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract text from <p> tags as a simple method
        paragraphs = soup.find_all("p")
        content = "\n".join([para.get_text() for para in paragraphs[:5]])  # Limit to first 5 paragraphs
        return content
    except httpx.RequestError as e:
        print(f"Error fetching external URL content from {url}: {e}")
        return "[Could not retrieve external content]"
    except Exception as e:
        print(f"Error processing external URL content from {url}: {e}")
        return "[Error processing external content]"


def map_weather_code_to_description(code):
    """
    Maps Open-Meteo weather codes to human-readable descriptions.
    Reference: https://open-meteo.com/en/docs#weathercode
    """
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return weather_codes.get(code, "Unknown weather condition")
