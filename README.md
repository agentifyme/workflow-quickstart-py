# Local Travel Planner

This is a simple travel planner that uses the AgentifyMe framework to generate a travel plan for a given destination and number of days.

## Requirements

- Python 3.12+
- AgentifyMe
- OpenAI API key


## Running the workflow

```python
import agentifyme
import asyncio
from loguru import logger

from openai import OpenAI

def main():
    try:
        client = agentifyme.Client(local_mode=True)
        input = {"name":"arun", "age":-12}
        output = client.run_workflow(name="hello-world-d", input=input)
        print(output)
    except agentifyme.AgentifyMeError as e:
        logger.error(e)
    except Exception as e:
        logger.error(e)

async def async_main():
    client = agentifyme.AsyncClient(local_mode=True)
    input = {"name":"arun", "age":-1}
    output = await client.run_workflow(name="hello-world-d", input=input)
    print(output)

if __name__ == "__main__":
    main()
    # asyncio.run(async_main())

```