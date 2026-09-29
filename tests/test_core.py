import unittest

import core


class TestCore(unittest.TestCase):
    def test_01_no_duplicate_deploy(self):
        state = core.new_game()
        self.assertTrue(core.deploy(state, "S1", "R1", 20))
        self.assertFalse(core.deploy(state, "S1", "R1", 20))

    def test_02_cooling_off_throttles_load(self):
        state = core.new_game()
        core.deploy(state, "S1", "R1", 30)
        core.set_cooling(state, False)
        self.assertEqual(core.total_load(state), 0)

    def test_03_rack_capacity_by_power(self):
        state = core.new_game()
        core.deploy(state, "S1", "R1", 90)
        result = core.can_add(state, "R1", 20)
        self.assertFalse(result)

    def test_04_migrate_frees_old_rack(self):
        state = core.new_game()
        core.deploy(state, "S1", "R1", 20)
        core.migrate(state, "S1", "R2")
        self.assertNotIn("S1", state["racks"]["R1"]["servers"])

    def test_05_no_task_without_power(self):
        state = core.new_game()
        state["power"] = False
        result = core.accept_task(state, "T1")
        self.assertFalse(result)

    def test_06_cancel_releases_server(self):
        state = core.new_game()
        core.deploy(state, "S1", "R1", 20)
        core.cancel_deploy(state, "S1")
        self.assertNotIn("S1", state["servers"])

    def test_07_heat_event_deducts_once(self):
        state = core.new_game()
        core.heat_event(state)
        self.assertEqual(state["lifespan"], 99)

    def test_08_load_preserves_queue(self):
        state = core.new_game()
        state["tasks"] = ["A", "B"]
        loaded = core.load_state(core.save_state(state))
        self.assertEqual(loaded["tasks"], ["A", "B"])

    def test_09_illegal_command_rejected(self):
        state = core.new_game()
        self.assertEqual(core.handle_command(state, "bogus x"), "非法命令")
        self.assertEqual(core.handle_command(state, "deploy S1 R1"), "非法命令")
        self.assertEqual(state["tick"], 0)
        self.assertEqual(state["servers"], {})

    def test_10_empty_data_loads_defaults(self):
        loaded = core.load_state("")
        self.assertEqual(loaded["tasks"], [])
        loaded = core.load_state("{}")
        self.assertEqual(loaded["lifespan"], 100)
        self.assertIn("R1", loaded["racks"])

    def test_11_capacity_boundary(self):
        state = core.new_game()
        core.deploy(state, "S1", "R1", 90)
        self.assertTrue(core.can_add(state, "R1", 10))
        self.assertFalse(core.can_add(state, "R1", 11))
        self.assertFalse(core.deploy(state, "S2", "R1", 11))
        self.assertTrue(core.deploy(state, "S2", "R1", 10))
        self.assertFalse(core.can_add(state, "R1", 1))

    def test_12_duplicate_inputs_rejected(self):
        state = core.new_game()
        self.assertTrue(core.accept_task(state, "T1"))
        self.assertFalse(core.accept_task(state, "T1"))
        self.assertEqual(state["tasks"], ["T1"])
        self.assertFalse(core.cancel_deploy(state, "S9"))
        self.assertFalse(core.migrate(state, "S9", "R2"))

    def test_13_command_commits_single_change(self):
        state = core.new_game()
        core.handle_command(state, "heat")
        self.assertEqual(state["lifespan"], 99)
        self.assertEqual(state["tick"], 1)
        core.handle_command(state, "deploy S1 R1 20")
        self.assertEqual(state["tick"], 2)


if __name__ == "__main__":
    unittest.main()
