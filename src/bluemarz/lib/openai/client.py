from http import HTTPMethod
import logging
import os
from typing import Any

import aiofile

import httpx

from bluemarz.core.models import SessionFile
from bluemarz.lib.openai import models
from bluemarz.utils.model_utils import desserialize_response as _desserialize
from bluemarz.utils.model_utils import to_dict as _to_dict

from bluemarz.utils.http_client import HTTPClient

BASE_URL: str = "https://api.openai.com/v1/"
BASE_HEADERS: dict[str, Any] = {"OpenAI-Beta": "assistants=v2"}

_client: HTTPClient = HTTPClient(BASE_URL, headers=BASE_HEADERS)


def _get_auth_headers(openai_key: str) -> dict[str, Any]:
    return {"Authorization": "Bearer " + openai_key}


async def retrieve_assistant(
    openai_key: str, id_assistant: str
) -> models.OpenAiAssistantSpec:
    path: str = f"/assistants/{id_assistant}"

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.OpenAiAssistantSpec)
    except Exception as ex:
        logging.error(f"Error in retrieve_assistant: {ex}")
        raise


async def create_message(
    openai_key: str,
    thread_id: str,
    role: str,
    content: str,
    files: list[models.OpenAiFileSpec] = None,
) -> models.ThreadMessage:
    body = {"role": role}
    if content:
        body["content"] = content
    else:
        body["content"] = " "

    if files:
        body["attachments"] = [
            {"file_id": file.id, "tools": [{"type": "file_search"}]} for file in files
        ]

    path: str = f"/threads/{thread_id}/messages"

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.POST, path, headers=_get_auth_headers(openai_key), json=body
        ).asend()
        return _desserialize(response, models.ThreadMessage)
    except Exception as ex:
        logging.error(f"Error in create_text_message: {ex}")
        raise


async def create_run(
    openai_key: str,
    thread: models.OpenAiThreadSpec,
    assistant: models.OpenAiAssistantSpec,
    additional_tools: list[models.OpenAiAssistantToolSpec],
) -> models.OpenAiThreadRun:
    tools: list[models.OpenAiAssistantToolSpec] = []
    if additional_tools:
        tools.extend(additional_tools)
    if assistant.tools:
        tools.extend(assistant.tools)

    # if files:
    found: bool = False
    for tool in tools:
        if tool.type == models.OpenAiAssistantToolType.FILE_SEARCH:
            found = True

    if not found:
        tools.append(
            models.OpenAiAssistantToolSpec(
                type=models.OpenAiAssistantToolType.FILE_SEARCH
            )
        )

    path: str = f"/threads/{thread.id}/runs"
    body = {
        "assistant_id": assistant.id,
        "tools": [_to_dict(t) for t in tools],
    }

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.POST, path, headers=_get_auth_headers(openai_key), json=body
        ).asend()
        return _desserialize(response, models.OpenAiThreadRun)
    except Exception as ex:
        logging.error(f"Error in create_run: {ex}")
        raise


async def get_run(
    openai_key: str, thread_id: str, run_id: str
) -> models.OpenAiThreadRun:
    path: str = f"/threads/{thread_id}/runs/{run_id}"

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.OpenAiThreadRun)
    except Exception as ex:
        logging.error(f"Error in get_run: {ex}")
        raise


async def cancel_run(
    openai_key: str, thread_id: str, run_id: str
) -> models.OpenAiThreadRun:
    path: str = f"/threads/{thread_id}/runs/{run_id}/cancel"

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.POST, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.OpenAiThreadRun)
    except Exception as ex:
        logging.error(f"Error in cancel_run: {ex}")
        raise


async def create_run_from_text_message(
    openai_key: str, assistant_id: str, input_msg: str
) -> models.OpenAiThreadRun:
    path: str = "/threads/runs"
    body = {
        "assistant_id": assistant_id,
        "thread": {"messages": [{"role": "user", "content": input_msg}]},
    }

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.POST, path, headers=_get_auth_headers(openai_key), json=body
        ).asend()
        return _desserialize(response, models.OpenAiThreadRun)
    except Exception as ex:
        logging.error(f"Error in create_run_from_text_message: {ex}")
        raise


async def get_run_status(openai_key: str, thread_id: str, run_id: str) -> str:
    path: str = f"/threads/{thread_id}/runs/{run_id}"

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return response.json()["status"]
    except Exception as ex:
        logging.error(f"Error in get_run_status: {ex}")
        raise


async def retrieve_message(
    openai_key: str, thread_id: str, message_id: str
) -> models.ThreadMessage:
    path: str = f"/threads/{thread_id}/messages/{message_id}"

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.ThreadMessage)
    except Exception as ex:
        logging.error(f"Error in retrieve_message: {ex}")
        raise


async def submit_tool_output(
    openai_key: str, thread_id: str, run_id: str, outputs: list[dict[str, str]]
) -> models.OpenAiThreadRun:
    path: str = f"/threads/{thread_id}/runs/{run_id}/submit_tool_outputs"
    body = {"tool_outputs": outputs}

    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.POST, path, headers=_get_auth_headers(openai_key), json=body
        ).asend()
        return _desserialize(response, models.OpenAiThreadRun)
    except Exception as ex:
        logging.error(f"Error in submit_tool_output: {ex}")
        raise


async def get_run_step(
    openai_key: str, thread_id: str, run_id: str, step_id: str
) -> models.ThreadRunStep:
    path: str = f"/threads/{thread_id}/runs/{run_id}/steps/{step_id}"
    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.ThreadRunStep)
    except Exception as ex:
        logging.error(f"Error in get_run_step: {ex}")
        raise


async def get_steps(
    openai_key: str, thread_id: str, run_id: str
) -> list[models.ThreadRunStep]:
    path: str = f"/threads/{thread_id}/runs/{run_id}/steps"
    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        ret_data = response.json()
        return [models.ThreadRunStep.model_validate(stp) for stp in ret_data["data"]]
    except Exception as ex:
        logging.error(f"Error in get_run_steps: {ex}")
        raise


async def create_session(openai_key: str) -> models.OpenAiThreadSpec:
    path: str = "/threads"
    params = {"messages": "", "tool_resource": "", "metadata": ""}
    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.POST, path, params=params, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.OpenAiThreadSpec)
    except Exception as ex:
        logging.error(f"Error in create_session: {ex}")
        raise


async def get_session(openai_key: str, thread_id: str) -> models.OpenAiThreadSpec:
    path: str = f"/threads/{thread_id}"
    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.OpenAiThreadSpec)
    except Exception as ex:
        logging.error(f"Error in get_session: {ex}")
        raise


async def get_assistant(
    openai_key: str, assistant_id: str
) -> models.OpenAiAssistantSpec:
    path: str = f"/assistants/{assistant_id}"
    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        return _desserialize(response, models.OpenAiAssistantSpec)
    except Exception as ex:
        logging.error(f"Error in get_assistant: {ex}")
        raise


async def get_thread_messages(
    openai_key: str, thread_id: str
) -> list[models.ThreadMessage]:
    path: str = f"/threads/{thread_id}/messages"
    try:
        response: httpx.Response = await _client.request(
            HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
        ).asend()
        ret_data = response.json()
        return [models.ThreadMessage.model_validate(stp) for stp in ret_data["data"]]
    except Exception as ex:
        logging.error(f"Error in get_thread_messages: {ex}")
        raise


async def delete_session(openai_key: str, thread_id: str) -> None:
    path: str = f"/threads/{thread_id}"
    params = {}
    try:
        await _client.request(
            HTTPMethod.DELETE,
            path,
            params=params,
            headers=_get_auth_headers(openai_key),
        ).asend()
    except Exception as ex:
        logging.error(f"Error in delete_session: {ex}")
        raise


async def get_files(
    openai_key: str, file_ids: list[str]
) -> list[models.OpenAiFileSpec]:
    base_path: str = "/files"
    fetched_files: list[models.OpenAiFileSpec] = []
    for file_id in file_ids:
        try:
            path = base_path + "/" + file_id
            response: httpx.Response = await _client.request(
                HTTPMethod.GET, path, headers=_get_auth_headers(openai_key)
            ).asend()
            fetched_files.append(_desserialize(response, models.OpenAiFileSpec))
        except Exception as ex:
            logging.error(f"Error in get_files: {ex}")

    return fetched_files


async def upload_files(
    openai_key: str, files: list[SessionFile]
) -> list[models.OpenAiFileSpec]:
    path: str = "/files"
    body = {"purpose": "assistants"}

    async with httpx.AsyncClient() as file_client:
        upload_files: list[models.OpenAiFileSpec] = []
        for file in files:
            try:
                async with file_client.stream(
                    "GET", str(file.url), timeout=30
                ) as stream:
                    async with aiofile.async_open(file.file_name, "wb") as f:
                        async for chunk in stream.aiter_bytes():
                            await f.write(chunk)
            except Exception as ex:
                logging.error(f"Error downloading file: {ex}")
                continue

            try:
                response: httpx.Response = await _client.request(
                    HTTPMethod.POST,
                    path,
                    headers=_get_auth_headers(openai_key),
                    data=body,
                    files={"file": open(file.file_name, "rb")},
                ).asend()
                upload_files.append(_desserialize(response, models.OpenAiFileSpec))
            except Exception as ex:
                logging.error(f"Error in upload_files: {ex}")

            os.remove(file.file_name)

        return upload_files
