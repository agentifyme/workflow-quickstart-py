import asyncio
import os
import random
import time

import openai
from agentifyme import AgentifyMeError, ErrorCategory, ErrorSeverity, task, workflow
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

from local_travel_planner.tasks import get_geo_coordinates, get_reddit_comments, get_reddit_posts, get_weather_forecast, get_wikipedia_info

load_dotenv()

MODEL = "gpt-4o-mini"


class MyWorkflowError(Exception):
    pass


def generate_itinerary(wiki_info, reddit_posts, weather_info, destination):
    """
    Uses OpenAI's Chat Completion API to generate a travel itinerary based on Wikipedia info, Reddit posts, comments, and weather data.
    """
    try:
        prompt = (
            f"Based on the following detailed information from Wikipedia, recent Reddit discussions and comments, and a 3-day weather forecast, "
            f"create a comprehensive 3-day travel itinerary for {destination}.\n\n"
            f"Wikipedia Information:\n"
        )
        for section, content in wiki_info.items():
            prompt += f"--- {section} ---\n"
            # Use BeautifulSoup to parse HTML content to plain text
            soup = BeautifulSoup(content, "html.parser")
            text = soup.get_text()
            prompt += f"{text}\n\n"

        prompt += f"3-Day Weather Forecast:\n{weather_info}\n\n"
        prompt += "Recent Reddit Discussions and Comments:\n"
        for idx, post in enumerate(reddit_posts, 1):
            # Retrieve content or external_content
            content = post.get("content") or post.get("external_content") or "[No content available]"

            # Truncate content for brevity if necessary
            if len(content) > 200:
                content = content[:197] + "..."

            # Retrieve comments
            comments = post.get("comments", [])
            comments_text = ""
            if comments:
                comments_text = "\n".join([f"   - {comment}" for comment in comments[:3]])  # Limit to first 3 comments

            # Add to prompt
            prompt += f"{idx}. {content}\n"
            if comments_text:
                prompt += f"   Comments:\n{comments_text}\n"
            else:
                prompt += f"   Comments: [No comments available]\n"

        prompt += "\nPlease provide a detailed 3-day itinerary, including activities, places to visit, and dining recommendations, considering the weather forecast and the information provided above and also add a section on suggestions on what to pack according to weather and also provide safety measures according to the reddit discuusion and comments."

        # Create messages for ChatCompletion API
        messages = [
            {"role": "system", "content": "You are an assistant that creates detailed and personalized travel itineraries based on provided information."},
            {"role": "user", "content": prompt},
        ]

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Call OpenAI's ChatCompletion API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )

        # Extract the itinerary from the response
        itinerary = response.choices[0].message.content.strip()
        return itinerary
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        return None


# @workflow(name="get-weather", description="Get weather forecast for a given destination and number of days")
# async def get_weather(destination: str, days: int) -> dict:
#     lat, lon = await get_geo_coordinates(destination)
#     if not lat or not lon:
#         logger.error("Could not retrieve geographical coordinates. Exiting.")
#         return
#     logger.info(f"Geographical coordinates retrieved - latitude: {lat}, longitude: {lon}.\n")

#     weather_info, weather_raw = await get_weather_forecast(lat, lon, days)
#     if not weather_info:
#         logger.error("Could not retrieve weather information. Exiting.")
#         return

#     return {"weather_info": weather_raw}


@workflow(name="get-weather", description="Get weather forecast for a given destination and number of days")
def get_weather(destination: str, days: int) -> dict:
    if not destination:
        logger.error("destination cannot be empty.")
        raise ValueError("destination cannot be empty.")

    lat, lon = asyncio.run(get_geo_coordinates(destination))
    if not lat or not lon:
        logger.error("Could not retrieve geographical coordinates. Exiting.")
        return
    logger.info(f"Geographical coordinates retrieved - latitude: {lat}, longitude: {lon}.\n")

    if days < 0:
        logger.error("days cannot be negative.")
        raise ValueError("days cannot be negative.")

    weather_info, weather_raw = asyncio.run(get_weather_forecast(lat, lon, days))
    if not weather_info:
        logger.error("Could not retrieve weather information. Exiting.")
        return

    # create a random time in milliseconds between 10 and days*1000
    random_time = random.randint(10, days * 1000)
    weather_raw["time"] = random_time
    time.sleep(random_time / 1000)

    return weather_raw


@workflow(name="generate-travel-plan", description="Generate a travel plan for a given location and number of days")
async def generate_travel_plan(destination: str, days: int) -> dict:
    """
    Generates a travel plan for a given location and number of days.

    :param destination: The name of the destination (e.g., 'Delhi')
    :param days: The number of days for the travel plan
    :return: A string containing the travel plan
    """
    logger.info(f"Generating travel plan for {destination} for {days} days")

    wiki_info, wiki_raw = await get_wikipedia_info(destination)
    if not wiki_info:
        logger.error("Could not retrieve Wikipedia information. Exiting.")
        return
    logger.info("Wikipedia Information Retrieved.\n")

    lat, lon = await get_geo_coordinates(destination)
    if not lat or not lon:
        logger.error("Could not retrieve geographical coordinates. Exiting.")
        return
    logger.info(f"Geographical coordinates retrieved - latitude: {lat}, longitude: {lon}.\n")

    weather_info, weather_raw = await get_weather_forecast(lat, lon, days)
    if not weather_info:
        logger.error("Could not retrieve weather information. Exiting.")
        return
    logger.info("Weather Information Retrieved.\n")

    logger.info(f"Travel Plan for {destination} for {days} days:\n{wiki_info}\n{weather_info}")

    # Fetch Reddit Posts
    logger.info(f"Fetching recent Reddit discussions from r/travel related to '{destination}'...")
    reddit_posts, reddit_raw = await get_reddit_posts(destination, subreddit="travel", limit=5)
    if not reddit_posts:
        logger.warning("Could not retrieve Reddit posts. Proceeding without Reddit data.\n")
    else:
        logger.info(f"Retrieved {len(reddit_posts)} Reddit posts.\n")

    # Fetch Comments for Each Reddit Post
    if reddit_posts:
        logger.info("Fetching comments for each Reddit post...\n")
        for idx, post in enumerate(reddit_posts, 1):
            permalink = post.get("permalink", "")
            if permalink:
                comments = await get_reddit_comments(permalink, limit=3)  # Fetch top 3 comments
                post["comments"] = comments
            else:
                post["comments"] = []
        logger.info("Comments Retrieved.\n")

    # Print Reddit Response
    if reddit_posts:
        logger.info("=== Reddit Response ===")
        for idx, post in enumerate(reddit_posts, 1):
            # Retrieve content or external_content
            content = post.get("content") or post.get("external_content") or "[No content available]"

            # Truncate content for brevity if necessary
            if len(content) > 200:
                content = content[:197] + "..."

            # Retrieve comments
            comments = post.get("comments", [])
            comments_text = ""
            if comments:
                comments_text = "\n".join([f"   - {comment}" for comment in comments])

            # Print content and comments
            logger.info(f"{idx}. {content}\n")
            if comments_text:
                logger.info(f"   Comments:\n{comments_text}\n")
            else:
                logger.info(f"   Comments: [No comments available]\n")

    itinerary = generate_itinerary(wiki_info, reddit_posts, weather_info, destination)
    if not itinerary:
        logger.error("Could not generate itinerary. Exiting.")
        return
    logger.info(f"Travel Plan for {destination} for {days} days")

    return {
        "destination": destination,
        "days": days,
        "itinerary": itinerary[:1000],
    }


@workflow(name="get-env", description="Get environment variables")
async def get_env() -> dict:
    logger.info("Getting environment variables")
    env_vars = dict(os.environ)
    return env_vars


def main():
    # asyncio.run(generate_travel_plan(destination="Phoenix, Arizona", days=3))
    asyncio.run(get_weather(destination="Phoenix, Arizona", days=3))


if __name__ == "__main__":
    main()
