from dataclasses import dataclass
from typing import Callable, Dict, Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from agent.state import State
from agent.constants.tasks import TASKS
from agent.constants.role import ROLES
import json

@dataclass
class NodeType:
    name: str  # ノードの名前
    func: Callable  # ノードで実行する関数


class Node:
    def __init__(
        self,
    ) -> None:
        self.generate_message = NodeType("generate_message", self._generate_message)
        self.select_role = NodeType("select_role", self._select_role)
        self.select_task = NodeType("select_task", self._select_task)
        self.execute_task = NodeType("execute_task", self._execute_task)
        self.end = NodeType("end", self.dummy_end)

    def _select_role(self, state: State) -> dict[str, str]:
        prompt = """
        あなたは農業関連のタスクを統括するエージェントです。
        以下のユーザーからの指示をもとに、まずは求められた役割を選択してください。
        役割の番号のみを出力素てください。
        

        指示: {prompt}
        役割一覧: {role_list}

        """

        prompt = ChatPromptTemplate.from_template(prompt)
        role_list = ROLES

        chain = prompt | state["model"].with_config(max_tokens=1) | StrOutputParser()

        current_role = chain.invoke({"prompt": state["prompt"], "role_list": role_list})

        return { "current_role": int(current_role) }

    def _select_task(self, state: State) -> dict[str, str]:
        prompt = """
        あなたは{role}の役割のエージェントです
        以下の指示から、まずは求められたタスクを選択してください。
        タスクの番号のみを出力してください。
        タスク一覧: {task_list}

        指示: {prompt}

        """

        prompt = ChatPromptTemplate.from_template(prompt)
        role = ""
        try:
            role_index = int(state.get("current_role", 1))  # デフォルト値として1を設定
            if role_index not in ROLES:
                print(f"Warning: Invalid role index {role_index}, falling back to role 1")
                role_index = 1
            role = ROLES[role_index]
        except ValueError:
            print(f"Warning: Invalid role value {state.get('current_role')}, falling back to role 1")
            role = ROLES[1]

        task_list = TASKS[state["current_role"]]

        chain = prompt | state["model"].with_config(max_tokens=1) | StrOutputParser()

        current_task = chain.invoke({"prompt": state["prompt"], "task_list": task_list, "role": role})

        return { "current_task": int(current_task) }

    def _execute_task(self, state: State) -> dict[str, str]:
        prompt = """
        以下のタスクを実行し、結果をJSON形式で返してください。
        JSONの形式は以下の通りです:

        タスク: {task}
        ユーザー入力: {prompt}
        """

        prompt = ChatPromptTemplate.from_template(prompt)
        chain = prompt | state["model"] | StrOutputParser()
        task = TASKS[state["current_role"]][state["current_task"]]["description"]
        
        response = chain.invoke({"task": task, "prompt": state["prompt"]})
        
        try:
            # LLMからの応答を取得
            response = chain.invoke({"task": task, "prompt": state["prompt"]})
            
            # JSON文字列の抽出（コードブロックの中からJSONを取り出す）
            json_match = response.strip()
            if "```json" in json_match:
                json_match = json_match.split("```json")[1].split("```")[0].strip()
            elif "```" in json_match:
                json_match = json_match.split("```")[1].strip()
                
            # JSON文字列をパース
            content_json = json.loads(json_match)
            
            # タスク実行
            result = TASKS[state["current_role"]][state["current_task"]]["function"](json.dumps(content_json))
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            content_json = {"error": f"Invalid JSON format: {e}"}
        except Exception as e:
            print(f"Error processing response: {e}")
            content_json = {"error": str(e)}
        
        state["messages"].append({
            "role": "system",
            "content": response
        })
            
        return {"messages": state["messages"]}

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
        print(state)
        pass

    def should_generate(self, state: State) -> bool:
        return state["current_role"] != 1