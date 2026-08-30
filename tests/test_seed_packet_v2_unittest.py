import unittest

from iboga_experiment.seed_packet_v2 import audit_packets, build_qualification_packet, build_seed_packet


class SeedPacketV2Tests(unittest.TestCase):
    def test_balanced_packet_is_pending_review(self) -> None:
        seed_public, seed_private = build_seed_packet()
        qualification_public, qualification_private = build_qualification_packet()
        report = audit_packets(seed_public, seed_private, qualification_public, qualification_private)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["release_status"], "pending_human_adjudication")
        self.assertEqual(report["seed_groups"], 108)
        self.assertEqual(report["qualification_cases"], 120)


if __name__ == "__main__":
    unittest.main()
