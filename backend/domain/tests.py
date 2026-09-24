import json

from django.test import TestCase

from .models import Route, TeamResult
from .services import (
    evaluate_sequence,
    get_referee_overview,
    revoke_result,
    submit_result,
)


def make_route(name="测试线", sequence=None):
    return Route.objects.create(
        name=name,
        description="测试线路",
        checkpoint_sequence=sequence or ["CP1", "CP2", "CP3"],
    )


class SequenceEvaluationTests(TestCase):
    def setUp(self):
        self.required = ["CP1", "CP2", "CP3", "CP4"]

    def test_exact_match_passes(self):
        issues, _ = evaluate_sequence(self.required, ["CP1", "CP2", "CP3", "CP4"])
        self.assertEqual(issues, [])

    def test_missing_point_detected(self):
        issues, detail = evaluate_sequence(self.required, ["CP1", "CP2", "CP4"])
        self.assertEqual(issues, ["missing"])
        self.assertEqual(detail["missing"], ["CP3"])

    def test_wrong_order_detected(self):
        issues, _ = evaluate_sequence(self.required, ["CP1", "CP3", "CP2", "CP4"])
        self.assertEqual(issues, ["wrong_order"])

    def test_missing_and_wrong_order_reported_together(self):
        issues, detail = evaluate_sequence(self.required, ["CP4", "CP2", "CP1"])
        self.assertEqual(set(issues), {"missing", "wrong_order"})
        self.assertEqual(detail["missing"], ["CP3"])

    def test_unexpected_and_duplicate_points_are_order_errors(self):
        issues, detail = evaluate_sequence(self.required, ["CP1", "CP2", "CP2", "CP9"])
        self.assertEqual(issues, ["missing", "wrong_order"])
        self.assertTrue(detail["duplicated"])
        self.assertEqual(detail["unexpected"], ["CP9"])


class SubmitResultServiceTests(TestCase):
    def setUp(self):
        self.route = make_route()

    def test_completed_submission(self):
        result = submit_result(self.route.id, "疾风队", ["CP1", "CP2", "CP3"], 3661)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["rank"], 1)
        self.assertEqual(result["duration"], "01:01:01")
        self.assertIn("齐全", result["resultNote"])

    def test_incomplete_submission_is_kept_with_reason(self):
        result = submit_result(self.route.id, "慢羊羊队", ["CP3", "CP1"], 1200)
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["rank"])
        self.assertIn("漏点", result["resultNote"])
        self.assertIn("顺序错误", result["issueLabels"])

    def test_duplicate_submit_keeps_first_only(self):
        first = submit_result(self.route.id, "疾风队", ["CP1", "CP2", "CP3"], 1000)
        with self.assertRaises(Exception) as ctx:
            submit_result(self.route.id, "疾风队", ["CP1", "CP2", "CP3"], 900)
        self.assertEqual(ctx.exception.status_code, 409)
        record = TeamResult.objects.get(team_name="疾风队")
        self.assertEqual(record.id, first["id"])
        self.assertEqual(record.total_seconds, 1000)

    def test_invalid_payload_rejected(self):
        with self.assertRaises(Exception):
            submit_result(self.route.id, "  ", ["CP1"], 10)
        with self.assertRaises(Exception):
            submit_result(self.route.id, "队", [], 10)
        with self.assertRaises(Exception):
            submit_result(self.route.id, "队", ["CP1"], 0)
        with self.assertRaises(Exception):
            submit_result(self.route.id, "队", ["CP1"], "60")

    def test_team_name_trimmed_for_dedup(self):
        submit_result(self.route.id, " 疾风队 ", ["CP1", "CP2", "CP3"], 1000)
        with self.assertRaises(Exception):
            submit_result(self.route.id, "疾风队", ["CP1", "CP2", "CP3"], 1200)


class RevokeAndOverviewTests(TestCase):
    def setUp(self):
        self.route = make_route(sequence=["CP1", "CP2"])
        submit_result(self.route.id, "甲队", ["CP1", "CP2"], 1200)
        submit_result(self.route.id, "乙队", ["CP1", "CP2"], 1000)
        submit_result(self.route.id, "丙队", ["CP2"], 900)

    def test_ranking_by_duration_excludes_incomplete(self):
        overview = get_referee_overview(self.route.id)
        block = overview["routes"][0]
        ranking = [(r["teamName"], r["rank"]) for r in block["records"] if r["rank"]]
        self.assertEqual(ranking, [("乙队", 1), ("甲队", 2)])
        self.assertEqual(block["summary"]["completedCount"], 2)
        self.assertEqual(block["summary"]["incompleteCount"], 1)

    def test_revoke_returns_team_to_pending_and_excludes_ranking(self):
        target = TeamResult.objects.get(team_name="乙队")
        revoked = revoke_result(target.id, reason="录错用时")
        self.assertEqual(revoked["status"], "revoked")
        self.assertEqual(revoked["previousStatus"], "completed")

        overview = get_referee_overview(self.route.id)
        block = overview["routes"][0]
        self.assertIn("乙队", block["pendingTeams"])
        top = next(r for r in block["records"] if r["status"] == "completed")
        self.assertEqual(top["teamName"], "甲队")
        self.assertEqual(top["rank"], 1)
        self.assertEqual(block["revokedRecords"][0]["revokeReason"], "录错用时")

    def test_resubmit_after_revoke_allowed_and_revocable_again(self):
        target = TeamResult.objects.get(team_name="乙队")
        revoke_result(target.id)
        new_result = submit_result(
            self.route.id, "乙队", ["CP1", "CP2"], 1100
        )
        self.assertEqual(new_result["status"], "completed")
        revoke_result(new_result["id"])
        self.assertEqual(
            TeamResult.objects.filter(team_name="乙队", status="revoked").count(), 2
        )

    def test_double_revoke_rejected(self):
        target = TeamResult.objects.get(team_name="甲队")
        revoke_result(target.id)
        with self.assertRaises(Exception) as ctx:
            revoke_result(target.id)
        self.assertEqual(ctx.exception.status_code, 400)


class ApiTests(TestCase):
    def setUp(self):
        self.route = make_route(name="接口测试线", sequence=["CP1", "CP2", "CP3"])

    def post(self, path, payload):
        return self.client.post(
            path, data=json.dumps(payload), content_type="application/json"
        )

    def test_full_flow_over_http(self):
        resp = self.client.get("/api/routes")
        self.assertEqual(resp.status_code, 200)
        route_id = next(
            item["id"]
            for item in resp.json()["routes"]
            if item["name"] == "接口测试线"
        )

        ok = self.post(
            "/api/results/submit",
            {
                "routeId": route_id,
                "teamName": "网络队",
                "submittedSequence": ["CP1", "CP2", "CP3"],
                "totalSeconds": 540,
            },
        )
        self.assertEqual(ok.status_code, 201)
        self.assertEqual(ok.json()["record"]["status"], "completed")

        dup = self.post(
            "/api/results/submit",
            {
                "routeId": route_id,
                "teamName": "网络队",
                "submittedSequence": ["CP1", "CP2", "CP3"],
                "totalSeconds": 100,
            },
        )
        self.assertEqual(dup.status_code, 409)

        record_id = TeamResult.objects.get(team_name="网络队").id
        revoked = self.client.post(
            f"/api/results/{record_id}/revoke",
            data=json.dumps({"reason": "测试撤销"}),
            content_type="application/json",
        )
        self.assertEqual(revoked.status_code, 200)
        self.assertEqual(revoked.json()["record"]["status"], "revoked")

        overview = self.client.get("/api/overview").json()
        self.assertEqual(overview["totals"]["pendingCount"], 1)

    def test_bad_json_returns_400(self):
        resp = self.client.post(
            "/api/results/submit", data="not-json", content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
