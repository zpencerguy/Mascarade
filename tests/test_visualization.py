import tempfile
import unittest
from pathlib import Path

from mascarade_sim.visualization import record_game_trace, write_game_visualization


class VisualizationTests(unittest.TestCase):
    def test_record_game_trace_contains_frames(self):
        trace = record_game_trace(player_count=4, seed=1)

        self.assertEqual(trace["playerCount"], 4)
        self.assertGreater(len(trace["frames"]), 1)
        self.assertIn("players", trace["frames"][0])

    def test_write_game_visualization_outputs_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_game_visualization(Path(tmp) / "game.html", player_count=4, seed=1)

            html = path.read_text(encoding="utf-8")
            self.assertIn("Mascarade 4-player simulation", html)
            self.assertIn("const TRACE =", html)


if __name__ == "__main__":
    unittest.main()
