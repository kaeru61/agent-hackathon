from dataclasses import dataclass
from typing import Callable, Dict, Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from agent.state import State
from agent.constants.tasks import TASKS
from agent.constants.role import ROLES
from agent.constants.inputs import INPUTS
import json

@dataclass
class NodeType:
    name: str  # ノードの名前
    func: Callable  # ノードで実行する関数


class Node:
    def __init__(
        self,
    ) -> None:
        self.judge_question = NodeType("judge_question", self._judge_question)
        self.generate_message = NodeType("generate_message", self._generate_message)
        self.select_role = NodeType("select_role", self._select_role)
        self.select_task = NodeType("select_task", self._select_task)
        self.execute_task = NodeType("execute_task", self._execute_task)
        self.end = NodeType("end", self.dummy_end)

    def _judge_question(self, state: State) -> dict[str, str]:
        prompt_row = """
        あなたは農業関連のタスクを統括するエージェントです。
        以下のユーザーからの入力が、質問であるかを判断してください。
        質問であれば1を、質問でなければ0を出力してください。

        入力: {prompt}
        """

        prompt = ChatPromptTemplate.from_template(prompt_row)

        chain = prompt | state["model"].with_config(max_tokens=1) | StrOutputParser()

        is_question = chain.invoke({"prompt": state["prompt"]})
        
        if int(is_question) == 1:
            return { "is_question": True, "current_role": 4 }
        else:
            return { "is_question": False }

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
        タスクの中身を実行するのではなく、必ずタスク番号のみを返却してください
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

        task_names = {task_id: task_info["name"] for task_id, task_info in TASKS[state["current_role"]].items()}

        chain = prompt | state["model"].with_config(max_tokens=1) | StrOutputParser()

        current_task = chain.invoke({"prompt": state["prompt"], "task_list": task_names, "role": role})
        return { "current_task": int(current_task) }

    def _execute_task(self, state: State) -> dict[str, str]:
        prompt = """
        以下の情報を参考にタスクを実行してください。

        タスク: {task}
        ユーザー入力: {prompt}
        """

        try:
            prompt_template = ChatPromptTemplate.from_template(prompt)
            chain = prompt_template | state["model"] | StrOutputParser()
            task = TASKS[state["current_role"]][state["current_task"]]["description"]
            
            # LLMからの応答を取得
            raw_response = chain.invoke({
                "task": task,
                "prompt": state.get("prompt", "")
            })
            
            # JSON文字列の抽出
            json_str = raw_response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # JSONパース
            filter_params = json.loads(json_str)
            
            # タスク実行
            result = TASKS[state["current_role"]][state["current_task"]]["function"](json.dumps(filter_params))

            if state["current_task"] == 2:
                print(raw_response)
                state["messages"].append({
                    "role": "system",
                    "content": f"タスクを実行しました。実行したタスク:{TASKS[state['current_role']][state['current_task']]['name']}",
                })
                return {"messages": state["messages"], "execute_tasks": int(raw_response) == 1}
            
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            result = {"error": str(e)}
        except Exception as e:
            print(f"実行エラー: {e}")
            result = {"error": str(e)}

        state["messages"].append({
            "role": "system",
            "content": f"タスクを実行しました。実行したタスク:{TASKS[state['current_role']][state['current_task']]['name']}",
        })
        
        return {"messages": state["messages"]}

    def _generate_message(self, state: State) -> dict[str, str]:
        prompt = """
        あなたは農業関連のタスクを統括するエージェントです。
        以下のユーザーからの入力とタスクの一覧を元にをユーザーからの質問に答えてください
        入力は全てチャット形式で受け付けることを考慮してください
        また、タスク一覧に記載されていない事柄は答えられないことを考慮してください
        特に、タスクに必要な入力への返答をするようにしてください
        タスク一覧: {task_list}
        ユーザー入力: {prompt}
        """
        prompt = ChatPromptTemplate.from_template(prompt)

        task_list = INPUTS

        chain = prompt | state["model"]
        
        response = chain.invoke({"prompt": state["prompt"], "task_list": task_list})

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

    def should_generate(self, state: State) -> bool:
        return state["current_role"] != 1