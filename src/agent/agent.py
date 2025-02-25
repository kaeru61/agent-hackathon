from typing import Any, Dict, Union

from langgraph.checkpoint.memory import MemorySaver

from agent.graph import GraphBuilder
from agent.node import Node
from agent.state import State


class Agent:
    def __init__(
        self,
    ) -> None:
        # ================
        # constructor
        # ================
        graph_builder = GraphBuilder(State)
        self.node = Node()

        # ================
        # Build Graph
        # ================
        # Add nodes
        graph_builder.add_node(self.node.judge_question)
        graph_builder.add_node(self.node.select_role)
        graph_builder.add_node(self.node.select_task)
        graph_builder.add_node(self.node.execute_task)
        graph_builder.add_node(self.node.generate_message)
        graph_builder.add_node(self.node.end)

        # Add edges
        graph_builder.add_conditional_edges(
            self.node.judge_question,
            lambda state: state["is_question"],
            {
                False: self.node.select_role.name,
                True: self.node.generate_message.name,
            },
        )
        graph_builder.add_edge(self.node.select_role, self.node.select_task)
        graph_builder.add_edge(self.node.select_task, self.node.execute_task)
        graph_builder.add_edge(self.node.execute_task, self.node.end)
        
        # Set entry and finish point
        graph_builder.set_entry_point(self.node.judge_question)
        graph_builder.set_finish_point(self.node.end)

        # Set up memory
        self.memory = MemorySaver()

        self.graph = graph_builder.work_flow.compile(
            checkpointer=self.memory,
        )

        # ================
        # write mermaid
        # ================
        with open("graph.md", "w") as file:
            file.write(f"```mermaid\n{self.graph.get_graph().draw_mermaid()}```")

    # ================
    # Helper
    # ================
    def is_start_node(self, thread: dict) -> bool:
        return self.graph.get_state(thread).created_at is None

    def is_end_node(self, thread: dict) -> bool:
        return self.get_state_value(thread, "is_finished")

    def get_next_node(self, thread: dict) -> tuple[str, ...]:
        return self.graph.get_state(thread).next

    def get_state_value(
        self, thread: dict, name: str
    ) -> Union[dict[str, Any], Any, None]:
        print("Thread: ", thread)
        print("Name: ", name)
        state = self.graph.get_state(thread)
        if state and name in state.values:
            return state.values.get(name)
        return None
