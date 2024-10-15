from datetime import datetime
from enum import Enum
from typing import TypeAlias
from pydantic import BaseModel, HttpUrl

Metadata: TypeAlias = dict[str, str]


class FileSearchTool(BaseModel):
    class FileSearchRankingOptions(BaseModel):
        ranker: str
        score_threshold: int

    max_num_results: int | None = None
    ranking_options: FileSearchRankingOptions | None = None


class FunctionTool(BaseModel):
    class FunctionToolParameters(BaseModel):
        type: str = "object"
        properties: dict[str,dict]
        additionalProperties: bool | None = None
        required: list[str] | None = None
    
    description: str
    name: str
    parameters: FunctionToolParameters | None = None
    strict: bool | None = None


class OpenAiAssistantToolType(str, Enum):
    FILE_SEARCH = "file_search"
    FUNCTION = "function"
    CODE_INTERPRETER = "code_interpreter"


class OpenAiAssistantToolSpec(BaseModel):
    type: OpenAiAssistantToolType
    file_search: FileSearchTool | None = None
    function: FunctionTool | None = None


class ToolResources(BaseModel):
    class CodeInterpreterResources(BaseModel):
        file_ids: list[str]

    class FileSearchResources(BaseModel):
        vector_store_ids: list[str]

    code_interpreter: CodeInterpreterResources | None = None
    file_search: FileSearchResources | None = None


class OpenAiAssistantSpec(BaseModel):
    id: str | None = None
    object: str = "assistant"
    model: str
    created_at: datetime | None = None
    name: str | None = None
    description: str | None = None
    instructions: str | None = None
    tools: list[OpenAiAssistantToolSpec] | None = None
    tool_resources: ToolResources | None = None
    metadata: Metadata | None = None
    top_p: float | None = None
    temperature: float | None = None
    response_format: str | dict = "auto"


class ContentAnnotation(BaseModel):
    class ContentAnnotationFile(BaseModel):
        file_id: str | None = None

    type: str
    text: str
    file_citation: ContentAnnotationFile | None = None
    file_path: ContentAnnotationFile | None = None
    start_index: int
    end_index: int


class ThreadMessageRole(Enum):
    ASSISTANT = "assistant"
    USER = "user"


class ThreadMessage(BaseModel):
    class FileAttachment(BaseModel):
        file_id: str | None = None
        tools: list[OpenAiAssistantToolSpec]

    class ThreadMessageContent(BaseModel):
        class ImageFile(BaseModel):
            file_id: str | None = None
            detail: str

        class ImageUrl(BaseModel):
            url: HttpUrl
            detail: str

        class Text(BaseModel):
            value: str
            annotations: list[ContentAnnotation] | None = None

        type: str
        image_file: ImageFile | None = None
        image_url: ImageUrl | None = None
        refusal: str | None = None
        text: Text | None = None
        annotations: list[ContentAnnotation] | None = None

    id: str | None = None
    object: str = "thread.message"
    created_at: datetime | None = None
    completed_at: datetime | None = None
    incomplete_at: datetime | None = None
    thread_id: str | None = None
    status: str | None = None
    incomplete_details: dict | None = None
    role: ThreadMessageRole
    content: str | list[ThreadMessageContent]
    assistant_id: str | None = None
    run_id: str | None = None
    attachments: list[FileAttachment] | None = None
    metadata: Metadata | None = None


class OpenAiThreadSpec(BaseModel):
    id: str | None = None
    object: str = "thread"
    created_at: datetime | None = None
    metadata: Metadata | None = None
    tool_resources: ToolResources | None = None
    messages: list[ThreadMessage] | None = None


class OpenAiToolCallSpec(BaseModel):
    class Function(BaseModel):
        name: str
        arguments: str

    id: str | None = None
    type: str = "function"
    function: Function


class ThreadToolChoice(BaseModel):
    class Function(BaseModel):
        name: str

    type: str
    function: Function


class LastError(BaseModel):
    code: str
    message: str


class RunUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAiThreadRun(BaseModel):
    class TruncationStrategy(BaseModel):
        type: str
        last_messages: int | None = None

    class IncompleteDetails(BaseModel):
        reason: str

    class RequiredAction(BaseModel):
        class SubmitToolOutputs(BaseModel):
            tool_calls: list[OpenAiToolCallSpec]

        type: str = "submit_tool_outputs"
        submit_tool_outputs: SubmitToolOutputs

    id: str | None = None
    object: str = "thread.run"
    created_at: datetime | None = None
    thread_id: str | None = None
    assistant_id: str
    status: str | None = None
    required_action: RequiredAction | None = None
    started_at: datetime | None = None
    expires_at: datetime | None = None
    cancelled_at: datetime | None = None
    failed_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: LastError | None = None
    model: str
    instructions: str | None = None
    tools: list[OpenAiAssistantToolSpec]
    metadata: Metadata | None = None
    incomplete_details: IncompleteDetails | None = None
    usage: RunUsage | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_prompt_tokens: int | None = None
    max_completion_tokens: int | None = None
    truncation_strategy: TruncationStrategy | None = None
    response_format: str | dict
    tool_choice: str | ThreadToolChoice
    parallel_tool_calls: bool


class VectorStore(BaseModel):
    class FileCounts(BaseModel):
        in_progress: int
        completed: int
        cancelled: int
        failed: int
        total: int

    class ExpiresAfter(BaseModel):
        anchor: str
        days: int

    id: str
    object: str = "vector_store"
    created_at: int
    usage_bytes: int
    last_active_at: int | None = None
    name: str
    status: str
    file_counts: FileCounts
    expires_after: ExpiresAfter
    expires_at: datetime | None = None
    last_used_at: int | None = None
    metadata: Metadata | None = None


class VectorStoreFile(BaseModel):
    class ChunkingStrategy(BaseModel):
        class Static(BaseModel):
            max_chunk_size_tokens: int
            chunk_overlap_tokens: int

        type: str
        static: Static | None = None

    id: str | None = None
    object: str = "vector_store.file"
    created_at: int
    usage_bytes: int
    vector_store_id: str | None = None
    status: str
    last_error: LastError | None = None
    chunking_strategy: ChunkingStrategy


class VectorStoreFileBatch(BaseModel):
    class FileCounts(BaseModel):
        in_progress: int
        completed: int
        cancelled: int
        failed: int
        total: int

    id: str | None = None
    object: str = "vector_store.files_batch"
    created_at: int
    usage_bytes: int
    vector_store_id: str | None = None
    status: str
    last_error: LastError | None = None
    file_counts: FileCounts


class OpenAiFileSpec(BaseModel):
    id: str
    object: str = "file"
    bytes: int
    created_at: int
    filename: str
    purpose: str


class ThreadRunStep(BaseModel):
    class StepDetails(BaseModel):
        class MessageCreation(BaseModel):
            message_id: str

        type: str
        message_creation: MessageCreation
        tool_calls: list[OpenAiToolCallSpec]

    id: str
    object: str = "thread.run.step"
    created_at: datetime
    run_id: str
    assistant_id: str
    thread_id: str
    type: str
    status: str
    cancelled_at: datetime | None = None
    completed_at: int
    expired_at: datetime | None = None
    failed_at: datetime | None = None
    last_error: LastError | None = None
    step_details: StepDetails
    usage: RunUsage
    metadata: Metadata | None = None
