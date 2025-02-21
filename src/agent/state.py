from typing import Annotated
from pydantic import Field
from langchain_core.language_models import BaseLanguageModel

from typing_extensions import TypedDict

class State(TypedDict):
    model: BaseLanguageModel
    question: str = Field(description="質問")

    trace_id: str = Field(
        description="トレースの識別子",
    )

    is_finished: bool = Field(
        description="会話が終了したかどうか",
    )

    prompt: str = Field(
        description="プロンプト",
    )

    messages: Annotated[list, "会話履歴のリスト"]
