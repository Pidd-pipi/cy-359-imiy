from django.test import TestCase

from .constants import ResultStatus
from .models import TeamResult
from .services import (
    SettlementError,
    ensure_default_course,
    get_referee_overview,
    normalize_sequence,
    revoke_result,
    submit_result,
    validate_sequence,
)

EXPECTED = ["CP1", "CP2", "CP3", "CP4", "CP5"]


class ValidateSequenceTests(TestCase):
    def test_exact_match_finishes(self):
        status, reason = validate_sequence(EXPECTED, EXPECTED)
        self.assertEqual(status, ResultStatus.FINISHED)
        self.assertEqual(reason, "")

    def test_case_and_whitespace_normalized(self):
        sequence = normalize_sequence([" cp1", "cp2", "CP3", "cp4", "CP5"])
        status, _ = validate_sequence(EXPECTED, sequence)
        self.assertEqual(status, ResultStatus.FINISHED)

    def test_missing_point_kept_as_incomplete(self):
        status, reason = validate_sequence(EXPECTED, ["CP1", "CP2", "CP4", "CP5"])
        self.assertEqual(status, ResultStatus.INCOMPLETE)
        self.assertIn("漏点", reason)
        self.assertIn("CP3", reason)

    def test_wrong_order_kept_as_incomplete(self):
        status, reason = validate_sequence(EXPECTED, ["CP1", "CP3", "CP2", "CP4", "CP5"])
        self.assertEqual(status, ResultStatus.INCOMPLETE)
        self.assertIn("顺序错误", reason)

    def test_extra_point_reported(self):
        status, reason = validate_sequence(EXPECTED, EXPECTED + ["CP9"])
        self.assertEqual(status, ResultStatus.INCOMPLETE)
        self.assertIn("线路外", reason)
        self.assertIn("CP9", reason)


class SettlementFlowTests(TestCase):
    def setUp(self):
        ensure_default_course()

    def test_submit_ranks_finished_by_time_and_excludes_incomplete(self):
        submit_result("疾风队", EXPECTED, "42:30")
        submit_result("穿山甲队", EXPECTED, 2290)  # 38:10，更快
        submit_result("北斗队", ["CP1", "CP2", "CP4", "CP5"], "35:00")  # 更快但漏点

        overview = get_referee_overview()
        ranking = overview["ranking"]
        self.assertEqual([t["teamName"] for t in ranking], ["穿山甲队", "疾风队"])
        self.assertEqual(ranking[0]["rank"], 1)
        self.assertTrue(all(t["status"] == ResultStatus.FINISHED for t in ranking))

        beidou = next(t for t in overview["teamsResults"] if t["teamName"] == "北斗队")
        self.assertEqual(beidou["status"], ResultStatus.INCOMPLETE)
        self.assertIn("漏点", beidou["issueReason"])

    def test_duplicate_submission_keeps_first_only(self):
        submit_result("疾风队", EXPECTED, "42:30")
        with self.assertRaises(SettlementError) as ctx:
            submit_result("疾风队", EXPECTED, "30:00")
        self.assertEqual(ctx.exception.code, "duplicate_submission")

        results = TeamResult.objects.filter(team_name="疾风队").exclude(status=ResultStatus.REVOKED)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().total_seconds, 42 * 60 + 30)

    def test_revoke_once_returns_team_to_pending_and_drops_ranking(self):
        submit_result("疾风队", EXPECTED, "42:30")
        original = TeamResult.objects.get(team_name="疾风队", status=ResultStatus.FINISHED)

        revoke_result(original.id, "录错")

        original.refresh_from_db()
        self.assertEqual(original.status, ResultStatus.REVOKED)
        self.assertIsNone(original.rank)
        self.assertEqual(original.revoke_count, 1)

        active = TeamResult.objects.filter(team_name="疾风队").exclude(status=ResultStatus.REVOKED).get()
        self.assertEqual(active.status, ResultStatus.PENDING)

        # 同一条成绩不能再撤销
        with self.assertRaises(SettlementError):
            revoke_result(original.id, "再撤一次")

    def test_resubmit_after_revoke_ranks_again_and_leaves_audit_trail(self):
        submit_result("疾风队", EXPECTED, "42:30")
        original = TeamResult.objects.get(team_name="疾风队", status=ResultStatus.FINISHED)
        revoke_result(original.id, "")

        new_result = submit_result("疾风队", EXPECTED, "36:00")
        self.assertEqual(new_result.status, ResultStatus.FINISHED)
        self.assertEqual(new_result.rank, 1)
        self.assertEqual(new_result.revoke_count, 0)

        overview = get_referee_overview()
        self.assertEqual(len(overview["revokedResults"]), 1)
        self.assertEqual(overview["revokedResults"][0]["totalTime"], "00:42:30")

    def test_unknown_team_rejected(self):
        with self.assertRaises(SettlementError):
            submit_result("路人队", EXPECTED, "10:00")

    def test_invalid_duration_rejected(self):
        with self.assertRaises(SettlementError):
            submit_result("绿野队", EXPECTED, "not-a-time")
