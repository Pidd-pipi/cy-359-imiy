import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .constants import (
    DEFAULT_COURSE_CHECKPOINTS,
    DEFAULT_COURSE_NAME,
    ISSUE_MISSING,
    ISSUE_ORDER,
    ISSUE_EXTRA,
    RESULT_STATUS_LABELS,
    TEAM_NAMES,
    ResultStatus,
)
from .models import Course, TeamResult

# ---------------------------------------------------------------------------
# 旧版运营总览（保持首页兼容）
# ---------------------------------------------------------------------------

OVERVIEW = {
    "appName": "城市定向越野活动平台",
    "appCode": "lporienteering",
    "description": "面向户外运动爱好者，提供定向越野线路设计、团队报名和积分排名的活动平台。",
    "features": [
        {
            "id": 1,
            "title": "活动线路设计与发布",
            "description": "管理员在地图上标记起点、终点和打卡点（CP点），设置各点线索和任务，发布活动时注明难度（亲子/成人/专业）、时长和装备要求。",
            "status": "已上线",
            "metric": "88%",
        },
        {
            "id": 2,
            "title": "线索打卡点（GPS/二维码）",
            "description": "参与者到达打卡点附近（GPS定位）或扫描二维码完成打卡，系统记录到达时间，打卡点可设置答题或拍照任务增加趣味性。",
            "status": "排期中",
            "metric": "31 单",
        },
        {
            "id": 3,
            "title": "赛后成绩结算",
            "description": "队长提交队名、到点顺序与总用时，系统按线路校验点位齐全与顺序，漏点/错序保留记录并说明原因，裁判可在总览撤销一次录错成绩。",
            "status": "已上线",
            "metric": "5 队",
        },
        {
            "id": 4,
            "title": "积分兑换商城",
            "description": "参与活动获得积分，积分可在商城兑换户外装备、活动优惠券或虚拟勋章，激励用户持续参与。",
            "status": "优化中",
            "metric": "4 级",
        },
        {
            "id": 5,
            "title": "历史线路收藏",
            "description": "用户可收藏感兴趣的已结束活动线路，查看其他参与者的成绩和路线轨迹，为下次报名提供参考。",
            "status": "可导出",
            "metric": "28 条",
        },
    ],
    "kpis": [
        {"label": "今日处理", "value": "132", "trend": "+12%", "tone": "primary"},
        {"label": "预约/订单", "value": "82", "trend": "+8%", "tone": "warm"},
        {"label": "履约率", "value": "90%", "trend": "+3%", "tone": "cool"},
        {"label": "待处理", "value": "5", "trend": "需跟进", "tone": "neutral"},
    ],
    "records": [
        {"key": "lporienteering-1", "name": "活动线路设计与发布", "owner": "运营组", "status": "已上线", "metric": "88%", "priority": "高"},
        {"key": "lporienteering-2", "name": "线索打卡点（GPS/二维码）", "owner": "管理员", "status": "排期中", "metric": "31 单", "priority": "中"},
        {"key": "lporienteering-3", "name": "赛后成绩结算", "owner": "裁判组", "status": "已上线", "metric": "5 队", "priority": "高"},
        {"key": "lporienteering-4", "name": "积分兑换商城", "owner": "财务组", "status": "优化中", "metric": "4 级", "priority": "高"},
        {"key": "lporienteering-5", "name": "历史线路收藏", "owner": "审核组", "status": "可导出", "metric": "28 条", "priority": "中"},
    ],
}


def get_overview():
    return OVERVIEW


# ---------------------------------------------------------------------------
# 成绩结算
# ---------------------------------------------------------------------------


class SettlementError(Exception):
    """结算业务错误，message 可直接展示给用户。"""

    def __init__(self, message, code="bad_request", status=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


def normalize_sequence(raw):
    """规范化到点顺序：去空白、大写、去空项。"""
    if not isinstance(raw, list):
        raise SettlementError("到点顺序必须是点位编码数组，例如 ['CP1','CP2']。")
    sequence = []
    for item in raw:
        if not isinstance(item, str):
            raise SettlementError("到点顺序中每一项都必须是点位编码字符串。")
        code = item.strip().upper()
        if code:
            sequence.append(code)
    if not sequence:
        raise SettlementError("到点顺序不能为空。")
    return sequence


_DURATION_RE = re.compile(r"^\d{1,2}(:\d{1,2}){1,2}$")


def parse_total_seconds(value):
    """总用时支持正整数秒或 mm:ss / hh:mm:ss 文本。"""
    if isinstance(value, bool):
        raise SettlementError("总用时格式不正确，请输入秒数或 mm:ss。")
    if isinstance(value, (int, float)):
        seconds = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            seconds = int(text)
        elif _DURATION_RE.match(text):
            parts = [int(p) for p in text.split(":")]
            if len(parts) == 2:
                minutes, secs = parts
                hours = 0
            else:
                hours, minutes, secs = parts
            if minutes >= 60 or secs >= 60:
                raise SettlementError("总用时格式不正确：分、秒必须小于 60。")
            seconds = hours * 3600 + minutes * 60 + secs
        else:
            raise SettlementError("总用时格式不正确，请输入秒数或 mm:ss（如 42:30）。")
    else:
        raise SettlementError("总用时格式不正确，请输入秒数或 mm:ss。")
    if seconds <= 0:
        raise SettlementError("总用时必须大于 0。")
    return seconds


def format_duration(total_seconds):
    if total_seconds is None:
        return "—"
    text = str(timedelta(seconds=int(total_seconds)))
    # timedelta 输出 h:mm:ss，统一补零为 hh:mm:ss
    if len(text.split(":", 1)[0]) == 1:
        text = "0" + text
    return text


def validate_sequence(expected, submitted):
    """按线路校验点位是否齐全、顺序是否一致。

    返回 (status, issue_reason)：
    - 点位齐全且顺序与线路完全一致 -> finished
    - 其余情况一律保留记录（incomplete），并在成绩栏说明未完成原因
    """
    expected_set = set(expected)
    submitted_set = set(submitted)

    missing = [code for code in expected if code not in submitted_set]
    extras = [code for code in submitted if code not in expected_set]

    # 仅看线路内点位的相对先后
    on_course = [code for code in submitted if code in expected_set]
    expected_order = [code for code in expected if code in set(on_course)]
    order_wrong = on_course != expected_order

    if not missing and not extras and not order_wrong:
        return ResultStatus.FINISHED, ""

    reasons = []
    if missing:
        reasons.append(f"{ISSUE_MISSING}（{'、'.join(missing)}）")
    if order_wrong:
        reasons.append(ISSUE_ORDER)
    if extras:
        reasons.append(f"{ISSUE_EXTRA}（{'、'.join(extras)}）")
    return ResultStatus.INCOMPLETE, "；".join(reasons)


def get_active_course():
    course = Course.objects.filter(is_active=True).prefetch_related("checkpoints").order_by("id").first()
    if course is None:
        raise SettlementError("当前没有已发布的比赛线路，请联系管理员。", code="course_missing", status=409)
    return course


def _rebuild_ranking(course):
    """按总用时升序重算完赛名次；未完赛与已撤销不参与排名。"""
    TeamResult.objects.filter(course=course, status=ResultStatus.FINISHED).update(rank=None)
    finished = list(
        TeamResult.objects.filter(course=course, status=ResultStatus.FINISHED).order_by("total_seconds", "settled_at")
    )
    for index, result in enumerate(finished, start=1):
        result.rank = index
    TeamResult.objects.bulk_update(finished, ["rank"])


def submit_result(team_name, raw_sequence, raw_duration):
    """队长提交成绩：同一队伍已有已结算成绩时，只保留先完成的一份。"""
    team_name = (team_name or "").strip()
    if not team_name:
        raise SettlementError("请选择或填写队名。")
    if team_name not in TEAM_NAMES:
        raise SettlementError(f"队名不在参赛名单中：{team_name}")

    sequence = normalize_sequence(raw_sequence)
    total_seconds = parse_total_seconds(raw_duration)

    with transaction.atomic():
        course = get_active_course()
        existing = (
            TeamResult.objects.select_for_update()
            .filter(team_name=team_name)
            .exclude(status=ResultStatus.REVOKED)
            .order_by("-submitted_at")
            .first()
        )
        if existing is not None and existing.status in (ResultStatus.FINISHED, ResultStatus.INCOMPLETE):
            raise SettlementError(
                f"{team_name} 已提交过成绩，同一队伍只保留先完成的一份，请勿重复提交。",
                code="duplicate_submission",
                status=409,
            )

        status, issue_reason = validate_sequence(course.checkpoint_codes, sequence)

        if existing is not None and existing.status == ResultStatus.PENDING:
            # 正常路径：种子待结算记录被本次提交结算
            result = existing
            result.course = course
            result.checkpoint_sequence = sequence
            result.total_seconds = total_seconds
        else:
            result = TeamResult(
                team_name=team_name,
                course=course,
                checkpoint_sequence=sequence,
                total_seconds=total_seconds,
            )

        result.status = status
        result.issue_reason = issue_reason
        result.settled_at = timezone.now()
        result.save()
        _rebuild_ranking(course)
        result.refresh_from_db()
        return result


def revoke_result(result_id, reason=""):
    """裁判撤销一次录错的成绩：原成绩标记撤销留痕且不再参与排名，队伍回到待结算。"""
    reason = (reason or "").strip()
    with transaction.atomic():
        result = (
            TeamResult.objects.select_for_update()
            .filter(pk=result_id)
            .select_related("course")
            .first()
        )
        if result is None:
            raise SettlementError("未找到对应的成绩记录。", code="not_found", status=404)
        if result.status == ResultStatus.REVOKED:
            raise SettlementError("该成绩已经撤销过，不能重复撤销。", code="already_revoked", status=409)
        if result.status == ResultStatus.PENDING:
            raise SettlementError("待结算的成绩还没有生效，无需撤销。")
        if result.revoke_count > 0:
            raise SettlementError("每条成绩只允许撤销一次。", code="revoke_limit", status=409)

        course = result.course
        old_reason = result.issue_reason
        result.status = ResultStatus.REVOKED
        result.revoke_count = 1
        result.rank = None
        result.revoked_at = timezone.now()
        result.issue_reason = f"裁判撤销：{reason}" if reason else "裁判撤销（录错）"
        if old_reason and reason:
            result.issue_reason = f"裁判撤销：{reason}（原记录：{old_reason}）"
        result.save()

        TeamResult.objects.create(
            team_name=result.team_name,
            course=course,
            checkpoint_sequence=[],
            total_seconds=None,
            status=ResultStatus.PENDING,
        )
        _rebuild_ranking(course)
        return result


def _serialize_result(result):
    return {
        "id": result.id,
        "teamName": result.team_name,
        "courseName": result.course.name,
        "sequence": list(result.checkpoint_sequence or []),
        "totalSeconds": result.total_seconds,
        "totalTime": format_duration(result.total_seconds),
        "status": result.status,
        "statusLabel": RESULT_STATUS_LABELS.get(result.status, result.status),
        "issueReason": result.issue_reason,
        "rank": result.rank,
        "revokeCount": result.revoke_count,
        "revocable": result.status in (ResultStatus.FINISHED, ResultStatus.INCOMPLETE)
        and result.revoke_count == 0,
        "submittedAt": timezone.localtime(result.submitted_at).strftime("%Y-%m-%d %H:%M:%S"),
        "settledAt": timezone.localtime(result.settled_at).strftime("%Y-%m-%d %H:%M:%S") if result.settled_at else None,
        "revokedAt": timezone.localtime(result.revoked_at).strftime("%Y-%m-%d %H:%M:%S") if result.revoked_at else None,
    }


def get_course_detail():
    course = get_active_course()
    return {
        "name": course.name,
        "checkpoints": course.checkpoint_codes,
        "teams": TEAM_NAMES,
    }


def get_referee_overview():
    course = get_active_course()
    active_results = list(
        TeamResult.objects.filter(course=course)
        .exclude(status=ResultStatus.REVOKED)
        .select_related("course")
        .order_by("rank", "total_seconds", "submitted_at")
    )
    existing_teams = {r.team_name for r in active_results}

    # 尚未产生任何记录的队伍，按待结算展示
    pending_virtual = [
        {
            "id": None,
            "teamName": name,
            "courseName": course.name,
            "sequence": [],
            "totalSeconds": None,
            "totalTime": "—",
            "status": ResultStatus.PENDING,
            "statusLabel": RESULT_STATUS_LABELS[ResultStatus.PENDING],
            "issueReason": "",
            "rank": None,
            "revokeCount": 0,
            "revocable": False,
            "submittedAt": None,
            "settledAt": None,
            "revokedAt": None,
        }
        for name in TEAM_NAMES
        if name not in existing_teams
    ]

    teams = [_serialize_result(r) for r in active_results] + pending_virtual
    revoked = [
        _serialize_result(r)
        for r in TeamResult.objects.filter(course=course, status=ResultStatus.REVOKED)
        .select_related("course")
        .order_by("-revoked_at")
    ]
    ranking = [t for t in teams if t["status"] == ResultStatus.FINISHED]

    counts = {
        ResultStatus.PENDING: sum(1 for t in teams if t["status"] == ResultStatus.PENDING),
        ResultStatus.FINISHED: len(ranking),
        ResultStatus.INCOMPLETE: sum(1 for t in teams if t["status"] == ResultStatus.INCOMPLETE),
        ResultStatus.REVOKED: len(revoked),
    }

    return {
        "course": {"name": course.name, "checkpoints": course.checkpoint_codes},
        "teams": TEAM_NAMES,
        "stats": [
            {"key": ResultStatus.PENDING, "label": "待结算", "value": counts[ResultStatus.PENDING]},
            {"key": ResultStatus.FINISHED, "label": "完赛", "value": counts[ResultStatus.FINISHED]},
            {"key": ResultStatus.INCOMPLETE, "label": "未完赛", "value": counts[ResultStatus.INCOMPLETE]},
            {"key": ResultStatus.REVOKED, "label": "已撤销", "value": counts[ResultStatus.REVOKED]},
        ],
        "teamsResults": teams,
        "ranking": ranking,
        "revokedResults": revoked,
    }


def ensure_default_course():
    """幂等创建默认线路（供数据迁移与测试使用）。"""
    course, created = Course.objects.get_or_create(
        name=DEFAULT_COURSE_NAME,
        defaults={"is_active": True},
    )
    if created:
        from .models import Checkpoint

        Checkpoint.objects.bulk_create(
            [
                Checkpoint(course=course, code=code, name=f"打卡点 {code}", position=index)
                for index, code in enumerate(DEFAULT_COURSE_CHECKPOINTS, start=1)
            ]
        )
        TeamResult.objects.bulk_create(
            [TeamResult(team_name=name, course=course, status=ResultStatus.PENDING) for name in TEAM_NAMES]
        )
    return course
