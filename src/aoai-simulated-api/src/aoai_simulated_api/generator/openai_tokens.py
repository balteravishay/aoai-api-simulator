import logging
import tiktoken

logger = logging.getLogger(__name__)

# For details on the token counting, see https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken


def get_max_completion_tokens(request_body, model_name: str, prompt_tokens: int) -> int:
    max_tokens = request_body.get("max_tokens")

    # Based on https://platform.openai.com/docs/guides/text-generation/managing-tokens
    default_max_tokens = 128000 if model_name == "gpt-4o" else 4097

    upper_limit = default_max_tokens - prompt_tokens
    if max_tokens is None or max_tokens > upper_limit:
        max_tokens = upper_limit

    return max_tokens


def num_tokens_from_string(string: str, model: str) -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens


# pylint: disable=invalid-name
gpt_35_turbo_warning_issued = False
gpt_4_warning_issued = False
# pylint: enable=invalid-name


def num_tokens_from_messages(messages, model):
    """Return the number of tokens used by a list of messages."""
    # pylint: disable-next=global-statement
    global gpt_35_turbo_warning_issued, gpt_4_warning_issued
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        if not gpt_35_turbo_warning_issued:
            logger.warning(
                "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613."
            )
            gpt_35_turbo_warning_issued = True
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        if not gpt_4_warning_issued:
            logger.warning("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            gpt_4_warning_issued = True
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"num_tokens_from_messages() is not implemented for model {model}. "
            + "See https://github.com/openai/openai-python/blob/main/chatml.md for information "
            + " on how messages are converted to tokens."
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
