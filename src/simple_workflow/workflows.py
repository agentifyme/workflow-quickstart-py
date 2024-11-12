from agentifyme import get_logger, workflow
from pydantic import BaseModel


class SimpleResponse(BaseModel):
    output: str


logger = get_logger()


@workflow(name="Get Output")
def get_output(query: str) -> SimpleResponse:
    _output = SimpleResponse(output=query)
    logger.info(f"Output: {_output}")
    return _output
