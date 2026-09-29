"""数据中心核心逻辑：服务器、冷却、负载均衡、任务和电力。"""

import json

DEFAULT_RACKS = ("R1", "R2")
RACK_CAPACITY = 100
MENU = "命令: deploy/cooling/load/canadd/migrate/task/cancel/heat/save/restore/quit"


def new_game():
    return {
        "servers": {},
        "racks": {r: {"capacity": RACK_CAPACITY, "servers": []} for r in DEFAULT_RACKS},
        "cooling": True,
        "power": True,
        "tasks": [],
        "lifespan": 100,
        "tick": 0,
    }


def save_state(state):
    return json.dumps(state, ensure_ascii=False)


def load_state(text):
    """读档：容忍空数据/缺字段，不改动任务队列。"""
    data = json.loads(text) if text and text.strip() else {}
    if not isinstance(data, dict):
        raise ValueError("存档必须是 JSON 对象")
    state = new_game()
    for key in state:
        if key in data:
            state[key] = data[key]
    for rack in state["racks"].values():
        rack.setdefault("capacity", RACK_CAPACITY)
        rack.setdefault("servers", [])
    return state


def rack_load(state, rack):
    return sum(state["servers"][s]["power"] for s in state["racks"][rack]["servers"])


def can_add(state, rack, power_draw):
    """按功耗校验机柜容量（含临界值）。"""
    if rack not in state["racks"] or power_draw <= 0:
        return False
    return rack_load(state, rack) + power_draw <= state["racks"][rack]["capacity"]


def deploy(state, server_id, rack, power_draw):
    if server_id in state["servers"]:
        return False
    if not can_add(state, rack, power_draw):
        return False
    state["racks"][rack]["servers"].append(server_id)
    state["servers"][server_id] = {"rack": rack, "power": power_draw}
    return True


def cancel_deploy(state, server_id):
    server = state["servers"].pop(server_id, None)
    if server is None:
        return False
    rack = state["racks"].get(server["rack"])
    if rack and server_id in rack["servers"]:
        rack["servers"].remove(server_id)
    return True


def set_cooling(state, on):
    state["cooling"] = bool(on)
    return True


def total_load(state):
    if not state["cooling"]:
        return 0
    return sum(s["power"] for s in state["servers"].values())


def migrate(state, server_id, new_rack):
    server = state["servers"].get(server_id)
    if server is None or new_rack not in state["racks"]:
        return False
    old_rack = server["rack"]
    if new_rack == old_rack:
        return False
    if not can_add(state, new_rack, server["power"]):
        return False
    state["racks"][old_rack]["servers"].remove(server_id)
    state["racks"][new_rack]["servers"].append(server_id)
    server["rack"] = new_rack
    return True


def accept_task(state, task):
    if not state["power"]:
        return False
    if task in state["tasks"]:
        return False
    state["tasks"].append(task)
    return True


def heat_event(state):
    state["lifespan"] -= 1
    return state["lifespan"]


def handle_command(state, line):
    """解析并执行一条命令，返回输出文本；每个命令只提交一次状态变化。"""
    parts = line.split()
    if not parts:
        return "空命令"
    cmd, args = parts[0], parts[1:]

    if cmd == "deploy" and len(args) == 3:
        server_id, rack = args[0], args[1]
        try:
            power_draw = int(args[2])
        except ValueError:
            return "错误: 功耗必须是整数"
        ok = deploy(state, server_id, rack, power_draw)
    elif cmd == "cooling" and len(args) == 1 and args[0] in ("on", "off"):
        ok = set_cooling(state, args[0] == "on")
    elif cmd == "load" and not args:
        return "load=%d" % total_load(state)
    elif cmd == "canadd" and len(args) == 2:
        try:
            power_draw = int(args[1])
        except ValueError:
            return "错误: 功耗必须是整数"
        return "canadd=%s" % can_add(state, args[0], power_draw)
    elif cmd == "migrate" and len(args) == 2:
        ok = migrate(state, args[0], args[1])
    elif cmd == "task" and len(args) == 1:
        ok = accept_task(state, args[0])
    elif cmd == "cancel" and len(args) == 1:
        ok = cancel_deploy(state, args[0])
    elif cmd == "heat" and not args:
        ok = True
        heat_event(state)
    elif cmd == "save" and len(args) == 1:
        with open(args[0], "w", encoding="utf-8") as fh:
            fh.write(save_state(state))
        return "已保存"
    elif cmd == "restore" and len(args) == 1:
        try:
            with open(args[0], encoding="utf-8") as fh:
                loaded = load_state(fh.read())
        except (OSError, ValueError) as exc:
            return "错误: %s" % exc
        state.clear()
        state.update(loaded)
        return "已读档"
    else:
        return "非法命令"

    state["tick"] += 1
    return "ok" if ok else "失败"


def main():
    state = new_game()
    print("数据中心 - " + MENU)
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        if raw == "quit":
            break
        print(handle_command(state, raw))


if __name__ == "__main__":
    main()
