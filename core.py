"""数据中心核心逻辑：服务器、冷却、负载均衡、任务和电力。"""

import json


def new_game():
    return {
        "servers": {},
        "racks": {
            "R1": {"capacity": 100, "servers": []},
            "R2": {"capacity": 100, "servers": []},
        },
        "cooling": True,
        "power": True,
        "tasks": [],
        "lifespan": 100,
    }


def save_state(state):
    return json.dumps(state, ensure_ascii=False)


def load_state(text):
    state = json.loads(text)
    return state


def deploy(state, server_id, rack, power_draw):
    if not server_id or rack not in state["racks"]:
        return False
    if server_id in state["servers"]:
        return False
    if not can_add(state, rack, power_draw):
        return False
    state["racks"][rack]["servers"].append(server_id)
    state["servers"][server_id] = {"rack": rack, "power": power_draw}
    return True


def set_cooling(state, on):
    state["cooling"] = on
    return True


def total_load(state):
    if not state["cooling"] or not state["power"]:
        return 0
    return sum(s["power"] for s in state["servers"].values())


def can_add(state, rack, power_draw):
    if rack not in state["racks"] or power_draw <= 0:
        return False
    entry = state["racks"][rack]
    used = sum(
        state["servers"][sid]["power"]
        for sid in entry["servers"]
        if sid in state["servers"]
    )
    return used + power_draw <= entry["capacity"]


def migrate(state, server_id, new_rack):
    if server_id not in state["servers"] or new_rack not in state["racks"]:
        return False
    old_rack = state["servers"][server_id]["rack"]
    if old_rack == new_rack:
        return False
    if not can_add(state, new_rack, state["servers"][server_id]["power"]):
        return False
    if server_id in state["racks"][old_rack]["servers"]:
        state["racks"][old_rack]["servers"].remove(server_id)
    state["racks"][new_rack]["servers"].append(server_id)
    state["servers"][server_id]["rack"] = new_rack
    return True


def accept_task(state, task):
    if not state["power"] or not task:
        return False
    if task in state["tasks"]:
        return False
    state["tasks"].append(task)
    return True


def cancel_deploy(state, server_id):
    if server_id not in state["servers"]:
        return False
    rack = state["servers"][server_id]["rack"]
    if server_id in state["racks"][rack]["servers"]:
        state["racks"][rack]["servers"].remove(server_id)
    del state["servers"][server_id]
    return True


def heat_event(state):
    state["lifespan"] -= 1
    return state["lifespan"]


COMMANDS = ("deploy", "cooling", "load", "canadd", "migrate", "task", "cancel", "heat", "quit")


def run_command(state, parts):
    if not parts:
        return "空命令"
    cmd, args = parts[0], parts[1:]
    if cmd not in COMMANDS:
        return "非法命令: %s" % cmd
    if cmd == "quit":
        return "quit"
    if cmd == "deploy" and len(args) == 3:
        try:
            power = int(args[2])
        except ValueError:
            return "功耗必须是整数"
        return "ok" if deploy(state, args[0], args[1], power) else "部署失败"
    if cmd == "cooling" and len(args) == 1 and args[0] in ("on", "off"):
        set_cooling(state, args[0] == "on")
        return "ok"
    if cmd == "load" and not args:
        return str(total_load(state))
    if cmd == "canadd" and len(args) == 2:
        try:
            power = int(args[1])
        except ValueError:
            return "功耗必须是整数"
        return "yes" if can_add(state, args[0], power) else "no"
    if cmd == "migrate" and len(args) == 2:
        return "ok" if migrate(state, args[0], args[1]) else "迁移失败"
    if cmd == "task" and len(args) == 1:
        return "ok" if accept_task(state, args[0]) else "任务被拒绝"
    if cmd == "cancel" and len(args) == 1:
        return "ok" if cancel_deploy(state, args[0]) else "取消失败"
    if cmd == "heat" and not args:
        return str(heat_event(state))
    return "参数错误"


def main():
    print("数据中心 - 命令: deploy/cooling/load/canadd/migrate/task/cancel/heat/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        result = run_command(state, raw.split())
        if result == "quit":
            break
        print(result)


if __name__ == "__main__":
    main()
