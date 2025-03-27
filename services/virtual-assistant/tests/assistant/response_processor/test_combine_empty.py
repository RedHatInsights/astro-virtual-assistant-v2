from virtual_assistant.assistant import (
    Query,
    ResponseText,
    ResponseOptions,
    ResponseOption,
    ResponseType,
)
from virtual_assistant.assistant.response_processor.combine_empty import CombineEmpty


async def test_combine_simple_case():
    processor = CombineEmpty()

    result = await processor.process(
        [
            ResponseText(text="What is 2 + 2 ?"),
            ResponseOptions(
                options=[
                    ResponseOption(text="3", value="3"),
                    ResponseOption(text="4", value="4"),
                    ResponseOption(text="5 for large enough 2's", value="5"),
                ]
            ),
        ],
        Query(text="test"),
    )

    assert len(result) == 1
    assert result[0].type == ResponseType.OPTIONS
    assert result[0].text == "What is 2 + 2 ?"
    assert len(result[0].options) == 3
    assert result[0].options[0].value == "3"
    assert result[0].options[1].value == "4"
    assert result[0].options[2].value == "5"


async def test_combine_complex_case():
    processor = CombineEmpty()

    result = await processor.process(
        [
            ResponseText(text="Let me ask you something"),
            ResponseText(text="What is 2 + 2 ?"),
            ResponseOptions(
                options=[
                    ResponseOption(text="3", value="3"),
                    ResponseOption(text="4", value="4"),
                    ResponseOption(text="5 for large enough 2's", value="5"),
                ]
            ),
            ResponseText(text="Do you know?"),
            ResponseText(text="Answer!"),
            ResponseOptions(
                options=[
                    ResponseOption(text="yes", value="yes"),
                    ResponseOption(text="no", value="no"),
                ]
            ),
            ResponseOptions(
                options=[
                    ResponseOption(text="yes", value="yes"),
                    ResponseOption(text="no", value="no"),
                ]
            ),
        ],
        Query(text="test"),
    )

    assert len(result) == 5
    assert result[0].type == ResponseType.TEXT
    assert result[0].text == "Let me ask you something"

    assert result[1].type == ResponseType.OPTIONS
    assert result[1].text == "What is 2 + 2 ?"
    assert len(result[1].options) == 3
    assert result[1].options[0].value == "3"
    assert result[1].options[1].value == "4"
    assert result[1].options[2].value == "5"

    assert result[2].type == ResponseType.TEXT
    assert result[2].text == "Do you know?"

    assert result[3].type == ResponseType.OPTIONS
    assert result[3].text == "Answer!"
    assert len(result[3].options) == 2
    assert result[3].options[0].value == "yes"
    assert result[3].options[1].value == "no"

    assert result[4].type == ResponseType.OPTIONS
    assert result[4].text is None
    assert len(result[4].options) == 2
    assert result[4].options[0].value == "yes"
    assert result[4].options[1].value == "no"


async def test_combine_nothing_to_combine_option_without_previous_text():
    processor = CombineEmpty()

    result = await processor.process(
        [
            ResponseOptions(
                options=[
                    ResponseOption(text="3", value="3"),
                    ResponseOption(text="4", value="4"),
                    ResponseOption(text="5 for large enough 2's", value="5"),
                ]
            ),
            ResponseText(text="What is 2 + 2 ?"),
        ],
        Query(text="test"),
    )

    assert len(result) == 2
    assert result[0].type == ResponseType.OPTIONS
    assert result[0].text is None
    assert len(result[0].options) == 3
    assert result[0].options[0].value == "3"
    assert result[0].options[1].value == "4"
    assert result[0].options[2].value == "5"

    assert result[1].type == ResponseType.TEXT
    assert result[1].text == "What is 2 + 2 ?"


async def test_combine_nothing_to_combine_option_with_text():
    processor = CombineEmpty()

    result = await processor.process(
        [
            ResponseText(text="What is 2 + 2 ?"),
            ResponseOptions(
                text="Choose one option:",
                options=[
                    ResponseOption(text="3", value="3"),
                    ResponseOption(text="4", value="4"),
                    ResponseOption(text="5 for large enough 2's", value="5"),
                ],
            ),
        ],
        Query(text="test"),
    )

    assert len(result) == 2
    assert result[0].type == ResponseType.TEXT
    assert result[0].text == "What is 2 + 2 ?"

    assert result[1].type == ResponseType.OPTIONS
    assert result[1].text == "Choose one option:"
    assert len(result[1].options) == 3
    assert result[1].options[0].value == "3"
    assert result[1].options[1].value == "4"
    assert result[1].options[2].value == "5"
