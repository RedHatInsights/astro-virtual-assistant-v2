from typing import List

from virtual_assistant.assistant import Response, Query, ResponseType
from virtual_assistant.assistant.response_processor.response_processor import (
    ResponseProcessor,
)


class CombineEmpty(ResponseProcessor):
    async def process(self, responses: List[Response], query: Query):
        combined_responses: List[Response] = []
        for response in responses:
            if response.type == ResponseType.OPTIONS and not response.text:
                if (
                    len(combined_responses) > 0
                    and combined_responses[-1].type == ResponseType.TEXT
                ):
                    combined_responses[-1] = response.model_copy(
                        update={
                            "text": combined_responses[-1].text,
                        }
                    )
                    continue

            combined_responses.append(response)

        return combined_responses
