"""成绩结算领域服务：提交校验、排名、裁判撤销。"""

from collections import OrderedDict

from django.db import IntegrityError, transaction
from django.utils import timezone

from .constants import (
    ISSUE_MISSING,
    ISSUE_WRONG_ORDER,
    RESULT_COMPLETED,
    RESULT_INCOMPLETE,
    RESULT_REVOKED,
    RESULT_STATUS_LABELS,
)
from .errors import ConflictError, NotFoundError, ValidationError
from .models import Route, TeamResult

ISSUE_LABELS = {
    ISSUE_MISSING: "漏点",
    ISSUE_WRONG_ORDER: "顺序错误",
}

TEAM_NAME_MAX = 120
REASON_MAX = 255


def format_duration(total_seconds):
    """秒 -> HH:MM:SS。"""
    total_seconds = int(total_seconds or 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _unique_preserve_order(items):
    return list(OrderedDict((item, None) for item in items).keys())


def _normalize_team_name(raw):
    if not isinstance(raw, str):
        raise ValidationError("队名必须为字符串")
    team_name = raw.strip()
    if not team_name:
        raise ValidationError("队名不能为空")
    if len(team_name) > TEAM_NAME_MAX:
        raise ValidationError(f"队名不能超过 {TEAM_NAME_MAX} 个字符")
    return team_name


def _normalize_sequence(raw):
    if not isinstance(raw, list) or not raw:
        raise ValidationError("到点顺序必须为非空数组")
    sequence = []
    for point in raw:
        if not isinstance(point, str):
            raise ValidationError("到点顺序中的每个点位必须为字符串")
        code = point.strip()
        if not code:
            raise ValidationError("到点顺序中不能包含空点位")
        sequence.append(code)
    return sequence


def _normalize_seconds(raw):
    if isinstance(raw, bool) or not isinstance(raw, int) or raw <= 0:
        raise ValidationError("总用时必须为正整数秒")
    return raw


def evaluate_sequence(required_sequence, submitted_sequence):
    """按线路校验点位是否齐全、顺序是否一致。

    返回 (issues, detail)：
    - missing：提交序列去重后缺少的规定点位；
    - wrong_order：规定点位在提交序列中的出现顺序与线路不一致，
      或存在线路外点位 / 重复打卡。
    """
    required = list(required_sequence)
    submitted = list(submitted_sequence)
    submitted_dedup = _unique_preserve_order(submitted)

    missing = [code for code in required if code not in submitted_dedup]

    required_in_submission = [code for code in submitted_dedup if code in required]
    required_order_index = {code: index for index, code in enumerate(required)}
    expected = [
        code for code in sorted(required_in_submission, key=required_order_index.get)
    ]
    unexpected = [code for code in submitted_dedup if code not in required]
    duplicated = len(submitted) != len(submitted_dedup)

    order_wrong = required_in_submission != expected or bool(unexpected) or duplicated

    issues = []
    if missing:
        issues.append(ISSUE_MISSING)
    if order_wrong:
        issues.append(ISSUE_WRONG_ORDER)
    return issues, {
        "missing": missing,
        "unexpected": unexpected,
        "duplicated": duplicated,
    }


def _build_result_note(required_count, issues, detail):
    if not issues:
        return f"全部 {required_count} 个打卡点齐全，顺序一致，成绩有效。"

    parts = []
    if ISSUE_MISSING in issues:
        missing_text = "、".join(detail["missing"])
        parts.append(f"漏点 {len(detail['missing'])} 个（{missing_text}）")
    if ISSUE_WRONG_ORDER in issues:
        reason = "到点顺序与线路不一致"
        if detail["unexpected"]:
            reason += "，含线路外点位 " + "、".join(detail["unexpected"])
        if detail["duplicated"]:
            reason += "，存在重复打卡"
        parts.append(reason)
    return "未完成：" + "；".join(parts) + "。"


def submit_result(route_id, team_name, submitted_sequence, total_seconds):
    """队长提交成绩：校验点位齐全性与顺序，保留比赛记录。

    同一队伍（同线路）同时/重复提交时只保留先完成的一份。
    """
    team_name = _normalize_team_name(team_name)
    submitted_sequence = _normalize_sequence(submitted_sequence)
    total_seconds = _normalize_seconds(total_seconds)

    with transaction.atomic():
        # 锁定线路行，保证同线路并发提交串行化
        try:
            route = Route.objects.select_for_update().get(pk=route_id)
        except Route.DoesNotExist:
            raise NotFoundError("线路不存在")

        if TeamResult.objects.filter(
            route=route, team_name=team_name
        ).exclude(status=RESULT_REVOKED).exists():
            raise ConflictError("该队伍已完成提交，只保留先完成的一份成绩。")

        issues, detail = evaluate_sequence(
            route.checkpoint_sequence, submitted_sequence
        )
        status = RESULT_COMPLETED if not issues else RESULT_INCOMPLETE
        note = _build_result_note(
            route.checkpoint_count, issues, detail
        )

        try:
            result = TeamResult.objects.create(
                route=route,
                team_name=team_name,
                submitted_sequence=submitted_sequence,
                total_seconds=total_seconds,
                status=status,
                issues=issues,
                result_note=note,
            )
        except IntegrityError:
            # 并发下唯一约束兜底：同一队伍只保留先完成的一份
            raise ConflictError("该队伍已完成提交，只保留先完成的一份成绩。")

    return serialize_result(result, rank=_rank_of(result))


def revoke_result(result_id, reason=""):
    """裁判撤销一次录错成绩：队伍回到待结算，原成绩不再参与排名。"""
    reason = (reason or "").strip()
    if len(reason) > REASON_MAX:
        raise ValidationError(f"撤销原因不能超过 {REASON_MAX} 个字符")

    with transaction.atomic():
        try:
            result = TeamResult.objects.select_for_update().get(pk=result_id)
        except TeamResult.DoesNotExist:
            raise NotFoundError("成绩记录不存在")

        if result.status == RESULT_REVOKED:
            raise ValidationError("该成绩已撤销，不能重复撤销。")

        result.status = RESULT_REVOKED
        result.revoked_at = timezone.now()
        result.revoke_reason = reason
        result.save(update_fields=["status", "revoked_at", "revoke_reason"])

    return serialize_result(result)


def _rank_of(result):
    """有效成绩按总用时升序排名；未完成/已撤销不参与排名。"""
    if result.status != RESULT_COMPLETED:
        return None
    faster = TeamResult.objects.filter(
        route_id=result.route_id,
        status=RESULT_COMPLETED,
        total_seconds__lt=result.total_seconds,
    ).count()
    return faster + 1


def serialize_route(route):
    return {
        "id": route.id,
        "name": route.name,
        "description": route.description,
        "checkpointSequence": list(route.checkpoint_sequence or []),
        "checkpointCount": route.checkpoint_count,
    }


def serialize_result(result, rank=None):
    payload = {
        "id": result.id,
        "routeId": result.route_id,
        "teamName": result.team_name,
        "submittedSequence": list(result.submitted_sequence or []),
        "totalSeconds": result.total_seconds,
        "duration": format_duration(result.total_seconds),
        "status": result.status,
        "statusLabel": RESULT_STATUS_LABELS[result.status],
        "issues": list(result.issues or []),
        "issueLabels": [ISSUE_LABELS.get(code, code) for code in (result.issues or [])],
        "resultNote": result.result_note,
        "completedAt": result.completed_at.isoformat() if result.completed_at else None,
        "revokedAt": result.revoked_at.isoformat() if result.revoked_at else None,
        "revokeReason": result.revoke_reason,
        "rank": rank,
    }
    if result.status == RESULT_REVOKED:
        payload["previousStatus"] = (
            RESULT_COMPLETED if not result.issues else RESULT_INCOMPLETE
        )
        payload["previousStatusLabel"] = RESULT_STATUS_LABELS[payload["previousStatus"]]
    return payload


def list_routes():
    return [serialize_route(route) for route in Route.objects.all()]


def _build_route_overview(route):
    active_results = list(
        TeamResult.objects.filter(route=route).exclude(status=RESULT_REVOKED)
    )
    completed = [r for r in active_results if r.status == RESULT_COMPLETED]
    incomplete = [r for r in active_results if r.status == RESULT_INCOMPLETE]
    revoked = list(
        TeamResult.objects.filter(route=route, status=RESULT_REVOKED).order_by(
            "-revoked_at"
        )
    )

    completed.sort(key=lambda item: (item.total_seconds, item.completed_at))
    records = []
    for index, result in enumerate(completed, start=1):
        records.append(serialize_result(result, rank=index))
    for result in sorted(incomplete, key=lambda item: item.completed_at):
        records.append(serialize_result(result, rank=None))

    # 曾有记录（含已撤销）但当前无有效记录的队伍视为待结算
    settled = {result.team_name for result in active_results}
    ever_submitted = set(
        TeamResult.objects.filter(route=route).values_list("team_name", flat=True)
    )
    pending_teams = sorted(ever_submitted - settled)

    return {
        "route": serialize_route(route),
        "records": records,
        "pendingTeams": pending_teams,
        "revokedRecords": [serialize_result(result) for result in revoked],
        "summary": {
            "settledCount": len(active_results),
            "completedCount": len(completed),
            "incompleteCount": len(incomplete),
            "pendingCount": len(pending_teams),
            "revokedCount": len(revoked),
        },
    }


def get_referee_overview(route_id=None):
    """裁判总览：各队耗时、问题、待结算与撤销历史。"""
    routes = list(Route.objects.all())
    if route_id is not None:
        routes = [route for route in routes if route.id == route_id]
        if not routes:
            raise NotFoundError("线路不存在")

    route_overviews = [_build_route_overview(route) for route in routes]

    totals = {
        "teamCount": sum(item["summary"]["settledCount"] for item in route_overviews)
        + sum(item["summary"]["pendingCount"] for item in route_overviews),
        "settledCount": sum(item["summary"]["settledCount"] for item in route_overviews),
        "completedCount": sum(
            item["summary"]["completedCount"] for item in route_overviews
        ),
        "incompleteCount": sum(
            item["summary"]["incompleteCount"] for item in route_overviews
        ),
        "pendingCount": sum(item["summary"]["pendingCount"] for item in route_overviews),
        "revokedCount": sum(item["summary"]["revokedCount"] for item in route_overviews),
    }
    return {"routes": route_overviews, "totals": totals}
