from django.db import models

from .constants import ResultStatus


class Course(models.Model):
    """比赛线路：规定到点顺序由 position 升序的 Checkpoint 决定。"""

    name = models.CharField("线路名称", max_length=120, unique=True)
    is_active = models.BooleanField("当前生效线路", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "线路"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    @property
    def checkpoint_codes(self):
        return list(self.checkpoints.order_by("position").values_list("code", flat=True))


class Checkpoint(models.Model):
    """线路打卡点（CP 点），position 从 1 开始表示规定到点顺序。"""

    course = models.ForeignKey(
        Course,
        verbose_name="所属线路",
        related_name="checkpoints",
        on_delete=models.CASCADE,
    )
    code = models.CharField("点位编码", max_length=32)
    name = models.CharField("点位名称", max_length=120, blank=True, default="")
    position = models.PositiveIntegerField("规定顺序")

    class Meta:
        verbose_name = "打卡点"
        verbose_name_plural = verbose_name
        ordering = ["course", "position"]
        unique_together = ("course", "position")

    def __str__(self):
        return f"{self.code}({self.position})"


class TeamResult(models.Model):
    """队伍成绩记录。

    状态流转：
    pending --队长提交结算--> finished / incomplete
    finished / incomplete --裁判撤销(仅一次)--> revoked，同时队伍回到 pending
    （pending 由活跃的可结算记录表示；撤销前的原始结果以 revoked 记录留痕）
    """

    team_name = models.CharField("队名", max_length=80)
    course = models.ForeignKey(
        Course,
        verbose_name="线路",
        related_name="results",
        on_delete=models.PROTECT,
    )
    checkpoint_sequence = models.JSONField("提交的到点顺序", default=list)
    total_seconds = models.PositiveIntegerField("总用时（秒）", null=True, blank=True)
    status = models.CharField(
        "成绩状态",
        max_length=16,
        choices=[
            (ResultStatus.PENDING, "待结算"),
            (ResultStatus.FINISHED, "完赛"),
            (ResultStatus.INCOMPLETE, "未完赛"),
            (ResultStatus.REVOKED, "已撤销"),
        ],
        default=ResultStatus.PENDING,
    )
    issue_reason = models.CharField("未完成/撤销原因", max_length=200, blank=True, default="")
    rank = models.PositiveIntegerField("名次", null=True, blank=True)
    revoke_count = models.PositiveIntegerField("撤销次数", default=0)
    submitted_at = models.DateTimeField("提交时间", auto_now_add=True)
    settled_at = models.DateTimeField("结算时间", null=True, blank=True)
    revoked_at = models.DateTimeField("撤销时间", null=True, blank=True)

    class Meta:
        verbose_name = "队伍成绩"
        verbose_name_plural = verbose_name
        ordering = ["-submitted_at"]
        indexes = [models.Index(fields=["team_name", "status"])]

    def __str__(self):
        return f"{self.team_name}-{self.status}"
