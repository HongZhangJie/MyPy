import pydot
from IPython.display import Image, display

# 创建一个新的有向图
graph = pydot.Dot(graph_type='digraph', fontname="SimHei", charset="utf8")

# 添加节点
nodes = {
    "Start": "开始",
    "A": "查询：根据id查询业务系统",
    "B": "查询：根据登录名查询用户",
    "C": "获取当前用户有权访问的资产信息集合",
    "D": "查询：根据登录条件查询用户最早访问",
    "E": "查询：不相符检索关键字search\n查询用户最早访问行为放宽表：allByUser",
    "F": "查询：查询用户所有访问行为放宽表：allByUser",
    "G": "查询：key为all_sess的系统参数到tbl_sysParam",
    "H": "查询：sysParamReposity.findAll()",
    "I": "查询：是否通过历史资产快速访问(fallByUser)",
    "J": "查询：用户历史访问资产记录",
    "K": "查询：用户最近访问资产记录\n用于设置三类标签",
    "L": "获取用户当前访问资产账号列表",
    "M": "查询：key为gui_sess的系统参数到tbl_sysParam",
    "N": "查询：sysParamReposity.findAll()",
    "O": "查询：是否通过历史资产账号信息",
    "P": "查询：是否存在符合条件的资产账号信息",
    "Q": "移除权限，特殊账号",
    "R": "获取最近一次低优变迁",
    "End": "结束"
}

for node, label in nodes.items():
    graph.add_node(pydot.Node(node, label=label, fontname="SimHei", charset="utf8"))

# 添加边
edges = [
    ("Start", "A"),
    ("A", "B"),
    ("B", "C"),
    ("C", "D"),
    ("D", "E", "是"),
    ("D", "F", "否"),
    ("E", "G"),
    ("F", "G"),
    ("G", "H"),
    ("I", "J", "是"),
    ("I", "K", "否"),
    ("K", "L"),
    ("L", "M"),
    ("M", "N"),
    ("N", "O"),
    ("O", "End", "是"),
    ("O", "P", "否"),
    ("P", "Q", "是"),
    ("Q", "R"),
    ("R", "K"),
    ("P", "K", "否")
]

for edge in edges:
    if len(edge) == 2:
        graph.add_edge(pydot.Edge(edge[0], edge[1]))
    else:
        graph.add_edge(pydot.Edge(edge[0], edge[1], label=edge[2], fontname="SimHei", charset="utf8"))

# 保存和展示流程图
graph.write_png('./flowchart.png')
display(Image(filename='flowchart.png'))
