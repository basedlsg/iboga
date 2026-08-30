from iboga_experiment.seed_packet_v2 import audit_packets, build_qualification_packet, build_seed_packet


def test_seed_packet_has_108_balanced_groups_and_blinded_public_fields():
    public, private = build_seed_packet()
    qualification_public, qualification_private = build_qualification_packet()
    report = audit_packets(public, private, qualification_public, qualification_private)
    assert report["ok"] is True, report["errors"]
    assert report["release_status"] == "pending_human_adjudication"
    assert len(public) == 108
    assert len(qualification_public) == 120
