import asyncio
from datetime import datetime

import agentifyme


async def hello_world():
    try:
        client = agentifyme.AsyncClient(local_mode=True)
        output = await client.run_workflow(
            name="hello-world",
            input={
                "name": "arun",
                "age": 12,
                "current_time": datetime.now(),
            },
        )
        print(output)
    except agentifyme.AgentifyMeError as e:
        print(e)
        print(e.error_code)
        print(e.error_type)
        print(e.traceback)


if __name__ == "__main__":
    asyncio.run(hello_world())
