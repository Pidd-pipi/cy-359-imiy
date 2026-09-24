APP_NAME = "城市定向越野活动平台"
APP_CODE = "lporienteering"

# 队伍名单：队长提交时从中选择队名
TEAM_NAMES = ["疾风队", "穿山甲队", "北斗队", "指南针队", "绿野队"]

# 默认线路的规定到点顺序（CP 点编码）
DEFAULT_COURSE_NAME = "城市公园标准线"
DEFAULT_COURSE_CHECKPOINTS = ["CP1", "CP2", "CP3", "CP4", "CP5"]


# 成绩状态
class ResultStatus:
    PENDING = "pending"  # 待结算（初始 / 被裁判撤销后）
    FINISHED = "finished"  # 完赛
    INCOMPLETE = "incomplete"  # 未完赛（漏点或顺序错误，记录保留但不参与排名）
    REVOKED = "revoked"  # 已撤销（原成绩留痕，不参与排名）


RESULT_STATUS_LABELS = {
    ResultStatus.PENDING: "待结算",
    ResultStatus.FINISHED: "完赛",
    ResultStatus.INCOMPLETE: "未完赛",
    ResultStatus.REVOKED: "已撤销",
}

# 未完赛原因
ISSUE_MISSING = "漏点"
ISSUE_ORDER = "顺序错误"
ISSUE_EXTRA = "存在线路外打卡点"
