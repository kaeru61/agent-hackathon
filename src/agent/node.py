from dataclasses import dataclass
from typing import Callable, Dict, Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from agent.state import State

@dataclass
class NodeType:
    name: str  # ノードの名前
    func: Callable  # ノードで実行する関数


class Node:
    def __init__(
        self,
    ) -> None:
        self.generate_message = NodeType("generate_message", self._generate_message)
        self.end = NodeType("end", self.dummy_end)

    def _generate_message(self, state: State) -> dict[str, str]:
        prompt_row = state["prompt"]
        prompt = ChatPromptTemplate.from_template(prompt_row)

        chain = prompt | state["model"]
        
        response = chain.invoke({})

        # responseのcontent部分のみを切り出す
        content = response.content if hasattr(response, 'content') else response

        state["messages"].append(
            {
                "role": "system",
                "content": content,
            }
        )

        return  {"messages": state["messages"]}


    def dummy_end(self, state: State) -> dict[str, str]:
        pass