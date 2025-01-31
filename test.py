import asyncio
from datetime import datetime

import agentifyme


async def hello_world():
    try:
        client = agentifyme.AsyncClient(endpoint="http://quickstart:63419", local_mode=True)
        output = await client.run_workflow(
            name="get-env-2",
        )
        print(output)
    except agentifyme.AgentifyMeError as e:
        print(e)
        print(e.error_code)
        print(e.error_type)
        print(e.traceback)


if __name__ == "__main__":
    asyncio.run(hello_world())
