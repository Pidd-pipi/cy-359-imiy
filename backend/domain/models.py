from django.db import models

from .constants import RESULT_COMPLETED, RESULT_INCOMPLETE, RESULT_REVOKED


class Route(models.Model):
    """比赛线路：点位顺序为该线路的权威打卡顺序。"""

    name = models.CharField("线路名称", max_length=120, unique=True)
    description = models.CharField("线路说明", max_length=255, blank=True, default="")
    # ["CP1", "CP2", ...]，顺序即规定到点顺序
    checkpoint_sequence = models.JSONField("规定点位顺序", default=list)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "route"
        verbose_name = "线路"
        verbose_name_plural = "线路"
        ordering = ["id"]

    def __str__(self):
        return self.name

    @property
    def checkpoint_count(self):
        return len(self.checkpoint_sequence or [])


class TeamResult(models.Model):
    """队伍比赛记录：保留所有提交，漏点/顺序错误同样保留。"""

    STATUS_CHOICES = [
        (RESULT_COMPLETED, "完成"),
        (RESULT_INCOMPLETE, "未完成"),
        (RESULT_REVOKED, "已撤销"),
    ]

    route = models.ForeignKey(
        Route, verbose_name="线路", on_delete=models.PROTECT, related_name="results"
    )
    team_name = models.CharField("队名", max_length=120)
    submitted_sequence = models.JSONField("提交到点顺序", default=list)
    total_seconds = models.PositiveIntegerField("总用时（秒）")
    status = models.CharField(
        "成绩状态", max_length=16, choices=STATUS_CHOICES, default=RESULT_INCOMPLETE
    )
    # 未完成原因：["missing", "wrong_order"]，完成为空列表
    issues = models.JSONField("未完成原因", default=list)
    # 成绩栏说明（完成说明或未完成原因的可读文本）
    result_note = models.CharField("成绩栏说明", max_length=255, blank=True, default="")
    completed_at = models.DateTimeField("提交完成时间", auto_now_add=True)
    revoked_at = models.DateTimeField("撤销时间", null=True, blank=True)
    revoke_reason = models.CharField("撤销原因", max_length=255, blank=True, default="")

    class Meta:
        db_table = "team_result"
        verbose_name = "队伍成绩"
        verbose_name_plural = "队伍成绩"
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["route", "status"]),
            models.Index(fields=["route", "team_name"]),
        ]
        constraints = [
            # 同一队伍同一线路只允许一份有效（非撤销）记录：
            # 先完成的一份保留，重复提交拒绝；裁判撤销后队伍回到待结算。
            models.UniqueConstraint(
                fields=["route", "team_name"],
                condition=~models.Q(status=RESULT_REVOKED),
                name="uniq_active_result_per_team_route",
            )
        ]

    def __str__(self):
        return f"{self.team_name} - {self.route.name}"
