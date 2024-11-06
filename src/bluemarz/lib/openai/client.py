import os
import urllib.request

import requests

from bluemarz.core.models import SessionFile
from bluemarz.lib.openai import models
from bluemarz.utils.model_utils import desserialize_response as _desserialize
from bluemarz.utils.model_utils import to_dict as _to_dict


def _get_assistants_api_headers(openai_key: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer " + openai_key,
        "OpenAI-Beta": "assistants=v2",
    }


def retrieve_assistant(
    openai_key: str, id_assistant: str
) -> models.OpenAiAssistantSpec:
    api_url = f"https://api.openai.com/v1/assistants/{id_assistant}"
    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiAssistantSpec)
    else:
        print(resp.content)
        raise Exception("Error in retrieve_assistant")


def create_message(
    openai_key: str,
    thread_id: str,
    role: str,
    content: str,
    files: list[models.OpenAiFileSpec] = None,
) -> models.ThreadMessage:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
    body = {"role": role}

    if content:
        body["content"] = content

    if files:
        body["attachments"] = [
            {"file_id": file.id, "tools": [{"type": "file_search"}]} for file in files
        ]

    resp = requests.post(
        api_url, json=body, headers=_get_assistants_api_headers(openai_key)
    )
    if resp.status_code == 200:
        return _desserialize(resp, models.ThreadMessage)
    else:
        print(resp.content)
        raise Exception("Error in create_text_message")


def create_run(
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

    api_url = f"https://api.openai.com/v1/threads/{thread.id}/runs"
    body = {
        "assistant_id": assistant.id,
        "tools": [_to_dict(t) for t in tools],
    }

    resp = requests.post(
        api_url, json=body, headers=_get_assistants_api_headers(openai_key)
    )
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadRun)
    else:
        print(resp.content)
        raise Exception("Error creat_run")


def get_run(openai_key: str, thread_id: str, run_id: str) -> models.OpenAiThreadRun:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"

    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadRun)
    else:
        print(resp.content)
        raise Exception("Cannot get_run")


def cancel_run(openai_key: str, thread_id: str, run_id: str) -> models.OpenAiThreadRun:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/cancel"

    resp = requests.post(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadRun)
    else:
        print(resp.content)
        raise Exception("Cannot cancel_run")


def create_run_from_text_message(
    openai_key: str, assistant_id: str, input_msg: str
) -> models.OpenAiThreadRun:
    api_url = "https://api.openai.com/v1/threads/runs"
    body = {
        "assistant_id": assistant_id,
        "thread": {"messages": [{"role": "user", "content": input_msg}]},
    }
    resp = requests.post(
        api_url, json=body, headers=_get_assistants_api_headers(openai_key)
    )
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadRun)
    else:
        print(resp.content)
        raise Exception("Error in create_run_from_text_message")


def get_run_status(openai_key: str, thread_id: str, run_id: str) -> str:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
    resp = requests.post(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return resp.json()["status"]
    else:
        print(resp.content)
        raise Exception("Error in get_run_status")


def get_run_result(
    openai_key: str, thread_id: str, run_id: str
) -> models.OpenAiThreadRun:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
    resp = requests.post(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadRun)
    else:
        print(resp.content)
        raise Exception("Error in get_run_result")


def retrieve_message(
    openai_key: str, thread_id: str, message_id: str
) -> models.ThreadMessage:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/messages/{message_id}"
    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.ThreadMessage)
    else:
        print(resp.content)
        raise Exception("Error in retreive_message")


def submit_tool_output(
    openai_key: str, thread_id: str, run_id: str, outputs: list[dict[str, str]]
) -> models.OpenAiThreadRun:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/submit_tool_outputs"
    body = {"tool_outputs": outputs}
    resp = requests.post(
        api_url, json=body, headers=_get_assistants_api_headers(openai_key)
    )
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadRun)
    else:
        print(resp.content)
        raise Exception("Error in submit_tool_output")


def get_run_step(
    openai_key: str, thread_id: str, run_id: str, step_id: str
) -> models.ThreadRunStep:
    api_url = (
        f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/steps/{step_id}"
    )
    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.ThreadRunStep)
    else:
        print(resp.content)
        raise Exception("Error in get_run_step")


def get_steps(
    openai_key: str, thread_id: str, run_id: str
) -> list[models.ThreadRunStep]:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/steps"
    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        ret_data = resp.json()
        return [models.ThreadRunStep.model_validate(stp) for stp in ret_data["data"]]
    else:
        print(resp.content)
        raise Exception("Error in get_steps")


def create_session(openai_key: str) -> models.OpenAiThreadSpec:
    api_url = "https://api.openai.com/v1/threads"
    params = {"messages": "", "tool_resource": "", "metadata": ""}
    resp = requests.post(
        api_url, params=params, headers=_get_assistants_api_headers(openai_key)
    )
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadSpec)
    else:
        print(resp.content)
        raise Exception("Error in create_session")


def get_session(openai_key: str, thread_id: str) -> models.OpenAiThreadSpec:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}"
    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiThreadSpec)
    else:
        print(resp.content)
        raise Exception("Error in get_session")


def get_assistant(openai_key: str, assistant_id: str) -> models.OpenAiAssistantSpec:
    api_url = f"https://api.openai.com/v1/assistants/{assistant_id}"
    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        return _desserialize(resp, models.OpenAiAssistantSpec)
    else:
        print(resp.content)
        raise Exception("Error in get_assistant")


def get_thread_messages(openai_key: str, thread_id: str) -> list[models.ThreadMessage]:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
    resp = requests.get(api_url, headers=_get_assistants_api_headers(openai_key))
    if resp.status_code == 200:
        ret_data = resp.json()
        return [models.ThreadMessage.model_validate(stp) for stp in ret_data["data"]]
    else:
        print(resp.content)
        raise Exception("Error in get_thread_messages")


def delete_session(openai_key: str, thread_id: str) -> None:
    api_url = f"https://api.openai.com/v1/threads/{thread_id}"
    params = {}
    resp = requests.delete(
        api_url, params=params, headers=_get_assistants_api_headers(openai_key)
    )
    if resp.status_code != 200:
        print(resp.content)
        raise Exception("Error in delete_session")


def get_files(openai_key: str, file_ids: list[str]) -> list[models.OpenAiFileSpec]:
    api_url = "https://api.openai.com/v1/files"
    fetched_files: list[models.OpenAiFileSpec] = []
    for file_id in file_ids:
        resp = requests.get(
            api_url + "/" + file_id,
            headers=_get_assistants_api_headers(openai_key),
        )

        if resp.status_code != 200:
            print(resp.content)
        else:
            fetched_files.append(_desserialize(resp, models.OpenAiFileSpec))

    return fetched_files


def upload_files(
    openai_key: str, files: list[SessionFile]
) -> list[models.OpenAiFileSpec]:
    api_url = "https://api.openai.com/v1/files"

    upload_files: list[models.OpenAiFileSpec] = []
    for file in files:
        urllib.request.urlretrieve(str(file.url), file.file_name)

        resp = requests.post(
            api_url,
            headers=_get_assistants_api_headers(openai_key),
            data={"purpose": "assistants"},
            files={"file": open(file.file_name, "rb")},
        )

        if resp.status_code != 200:
            print(resp.content)
        else:
            upload_files.append(_desserialize(resp, models.OpenAiFileSpec))

        os.remove(file.file_name)

    return upload_files
