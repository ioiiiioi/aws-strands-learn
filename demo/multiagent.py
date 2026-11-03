"""03 — multi-agent: Swarm (agent saling serah terima) vs Graph (alur tetap).

Jalan: uv run python -m demo.multiagent
"""

from strands import Agent
from strands.multiagent import GraphBuilder, Swarm

from demo.model import get_model


def buat(nama: str, prompt: str) -> Agent:
    return Agent(name=nama, model=get_model(), system_prompt=prompt)


peneliti = buat(
    "peneliti",
    "Kamu peneliti. Kumpulkan 3 fakta singkat, lalu serahkan ke penulis.",
)
penulis = buat(
    "penulis",
    "Kamu penulis. Kalau sudah dapat fakta, tulis ringkasan 3 kalimat. "
    "Kalau belum, serahkan balik ke peneliti.",
)


def demo_swarm() -> None:
    swarm = Swarm(nodes=[peneliti, penulis], entry_point=peneliti, max_handoffs=4)
    hasil = swarm("Jelaskan singkat kenapa kopi bikin melek.")
    print("=== SWARM ===")
    print(hasil)
    print("urutan node:", [h.node_id for h in hasil.node_history])


def demo_graph() -> None:
    riset = buat("riset", "Sebutkan 2 fakta tentang kopi.")
    tulis = buat("tulis", "Rapikan fakta dari agen riset jadi 2 kalimat.")

    builder = GraphBuilder()
    builder.add_node(riset, "riset")
    builder.add_node(tulis, "tulis")
    builder.add_edge("riset", "tulis")
    builder.set_entry_point("riset")
    graph = builder.build()

    hasil = graph("Topik: kopi dan produktivitas.")
    print("\n=== GRAPH ===")
    print(hasil)
    print("execution_order:", [n.node_id for n in hasil.execution_order])


if __name__ == "__main__":
    demo_graph()
