from typing import Dict, List
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dataclasses import dataclass
import os

os.environ["GEMINI"] = "path/to/your/credentials.json"

@dataclass
class VegetableAgent:
    name: str
    personality: str
    related_dishes: List[str]
    
    # 食材が含まれる料理データを内部に移動
    _INGREDIENT_TO_DISHES: Dict[str, List[str]] = {
        "トマト": ["スパゲッティ", "サラダ"],
        "にんじん": ["カレー", "シチュー"],
        "チーズ": ["ピザ", "グラタン"],
        "唐辛子": ["麻婆豆腐", "チリコンカン"],
        "豆腐": ["味噌汁", "麻婆豆腐"]
    }
    
    def get_state(self) -> Dict[str, any]:
        """
        エージェントの現在の状態を取得する

        Returns:
            Dict[str, any]: エージェントの状態を表す辞書
        """
        return {
            "name": self.name,
            "personality": self.personality,
            "related_dishes": self.related_dishes
        }

    @classmethod
    def create_vegetable_agents(cls, inputs: Dict[str, any]) -> 'VegetableAgent':
        """
        食材情報をもとにエージェントを生成する

        Args:
            inputs (Dict[str, any]): 生成に必要な入力情報
                - personality: エージェントの性格
                - dishes: 関連する料理のリスト

        Returns:
            VegetableAgent: 生成されたエージェントインスタンス
        """
        personality = inputs["personality"]
        dishes = inputs["dishes"]
        name = next((ingredient for ingredient, dish_list in cls._INGREDIENT_TO_DISHES.items() 
                    if any(d in dishes for d in dish_list)), "Unknown")
        
        return cls(
            name=name,
            personality=personality,
            related_dishes=dishes
        )

# LangGraphのノード定義
def ingredient_analysis(ingredients):
    """食材から基本性格を取得（LLMを使用）"""
    personality = {}
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    for i in ingredients:
        prompt = PromptTemplate(template="""
                                あなたは野菜の性格を想像するエージェントです。
                                その野菜の栄養素などをもとにして
                                {ingredient}の性格を形容してください。
                                """, input_variables=["ingredient"])
        personality[i] = llm(prompt.format(ingredient=i))
    return {"personality": personality}

def dish_analysis(ingredients):
    """食材に基づいて関連する料理を取得"""
    dishes = {i: VegetableAgent._INGREDIENT_TO_DISHES.get(i, []) for i in ingredients}
    return {"dishes": dishes}

# LangGraphのワークフロー定義
graph = langgraph.Graph()
graph.add_node("ingredient_analysis", ingredient_analysis)
graph.add_node("dish_analysis", dish_analysis)
graph.add_node("create_vegetable_agents", VegetableAgent.create_vegetable_agents)

graph.set_entry_point("ingredient_analysis")
graph.add_edge("ingredient_analysis", "dish_analysis")
graph.add_edge("dish_analysis", "create_vegetable_agents")

workflow = graph.compile()

# テスト実行
test_ingredients = ["トマト", "にんじん", "唐辛子"]
result = workflow.invoke(test_ingredients)

# 生成されたエージェントの情報を表示
for agent in result["agents"]:
    print(agent.get_state())
