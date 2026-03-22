import json

from py2neo import Graph
from py2neo import Node, Relationship
from llm import get_agent_nopic

from config import config  

graph_config = config.get("graph", {})

def get_graph():
    # 连接到Neo4j数据库
    graph = Graph(graph_config.get("neo4j_url","neo4j://localhost:7475"), auth=(graph_config.get("username","neo4j"), graph_config.get("password")))
    
    # 创建唯一性约束确保数据一致性
    constraints = [
        "CREATE CONSTRAINT Person IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT Position IF NOT EXISTS FOR (po:Position) REQUIRE po.name IS UNIQUE",
        "CREATE CONSTRAINT Organization IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
        "CREATE CONSTRAINT Item IF NOT EXISTS FOR (i:Item) REQUIRE i.name IS UNIQUE",
        "CREATE CONSTRAINT Concept IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT Time IF NOT EXISTS FOR (t:Time) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT Event IF NOT EXISTS FOR (e:Event) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT Activity IF NOT EXISTS FOR (a:Activity) REQUIRE a.name IS UNIQUE"
    ]

    for constraint in constraints:
        graph.run(constraint)
    
    return graph

def extract_quintuples(text:str):
    """使用结构化输出的五元组提取"""
    system_prompt = f"""
    从以下中文文本中抽取有价值的五元组（主语-主语类型-谓语-宾语-宾语类型）关系，以 JSON 数组格式返回。

    ## 提取规则
    1. 只提取**事实性**信息，包括：
    - 具体的行为和动作
    - 明确的实体关系
    - 实际存在的状态和属性
    - 用户表达的具体需求、偏好、计划
    

    2. 严格过滤以下内容：
    - 比喻、拟人、夸张等修辞手法
    - 时间的陈述（如“现在是14点”）
    - 虚拟、假设、想象的内容
    - 纯粹的情感表达（如"我很开心"、"你真棒"）
    - 赞美、讽刺、调侃等主观评价
    - 闲聊中的无关信息
    - 重复或冗余的关系

    3. 类型包括但不限于：人物、地点、组织、物品、概念、时间、事件、活动等。

    ## 示例
    输入：小明在公园里踢足球。
    输出：[["小明", "人物", "踢", "足球", "物品"], ["小明", "人物", "在", "公园", "地点"]]

    输入：你像小太阳一样温暖。
    输出：[] （比喻句，不提取）

    输入：我喜欢吃苹果和香蕉。
    输出：[["我", "人物", "喜欢吃", "苹果", "物品"], ["我", "人物", "喜欢吃", "香蕉", "物品"]]

    输入：如果我是鸟，我会飞到月球。
    输出：[] （假设内容，不提取）

    请从文本中提取有价值的事实性五元组：
    {text}

    除了JSON数据，请不要输出任何其他数据，例如：```、```json、以下是我提取的数据：。
    """

    msgs = []
    msgs.append({
        "role": "system",
        "content": system_prompt
    })
    msgs.append({
        "role": "user",
        "content": text
    })

    res = get_agent_nopic().invoke({
        "messages":msgs
    })

    latest_message = res["messages"][-1]
    if latest_message.content:
        res=latest_message.content.strip()
    
    quintuples = json.loads(res)
    print(f"提取到 {len(quintuples)} 个五元组")
    print([tuple(t) for t in quintuples if len(t) == 5])
    return [tuple(t) for t in quintuples if len(t) == 5]

def store_quintuples(quintuples:tuple):
    graph = get_graph()
    if len(quintuples)==0: 
        return False
    print("存储开始：")
    for subject, subject_type, relation, object_, object_type in quintuples:
        print(f"主语: {subject} (类型: {subject_type})")
        print(f"谓语: {relation}")
        print(f"宾语: {object_} (类型: {object_type})")
        print("---") 
        h_label = subject_type
        t_label = object_type
        h_node = Node(h_label, name=subject, entity_type=subject_type)
        t_node = Node(t_label, name=object_, entity_type=object_type)

        # 合并时使用对应标签和唯一键 "name"
        graph.merge(h_node, h_label, "name")
        graph.merge(t_node, t_label, "name")

        r = Relationship(h_node, relation, t_node, head_type=subject_type, tail_type=object_type)
        graph.merge(r)
    return True

def search_quintuples(keyword:str):
    """此处keyword为Tool调用时提取的keyword"""
    graph = get_graph()
    query = """
    MATCH (e1)-[r]->(e2)
    WHERE e1.name CONTAINS $kw OR e2.name CONTAINS $kw
    OR e1.entity_type CONTAINS $kw OR e2.entity_type CONTAINS $kw
    OR type(r) CONTAINS $kw
    RETURN e1.name, e1.entity_type, type(r), e2.name, e2.entity_type LIMIT 5
    """

    results = graph.run(query, kw=keyword).data()
    print("关键词搜索结果:"+str(results))
    return results