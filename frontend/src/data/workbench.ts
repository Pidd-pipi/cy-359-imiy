import type { FeatureItem, KpiItem, OperationRecord } from "../types";

export const localFeatures: FeatureItem[] = [
  {
    "id": 1,
    "title": "活动线路设计与发布",
    "description": "管理员在地图上标记起点、终点和打卡点（CP点），设置各点线索和任务，发布活动时注明难度（亲子/成人/专业）、时长和装备要求。",
    "status": "已上线",
    "metric": "88%"
  },
  {
    "id": 2,
    "title": "线索打卡点（GPS/二维码）",
    "description": "参与者到达打卡点附近（GPS定位）或扫描二维码完成打卡，系统记录到达时间，打卡点可设置答题或拍照任务增加趣味性。",
    "status": "排期中",
    "metric": "31 单"
  },
  {
    "id": 3,
    "title": "团队报名与排名",
    "description": "用户以个人或团队形式报名，活动开始后系统记录各团队完成所有打卡点的总用时，按用时排名生成实时 leaderboard。",
    "status": "巡检中",
    "metric": "10 项"
  },
  {
    "id": 4,
    "title": "积分兑换商城",
    "description": "参与活动获得积分，积分可在商城兑换户外装备、活动优惠券或虚拟勋章，激励用户持续参与。",
    "status": "优化中",
    "metric": "4 级"
  },
  {
    "id": 5,
    "title": "历史线路收藏",
    "description": "用户可收藏感兴趣的已结束活动线路，查看其他参与者的成绩和路线轨迹，为下次报名提供参考。",
    "status": "可导出",
    "metric": "28 条"
  }
];

export const localKpis: KpiItem[] = [
  {
    "label": "今日处理",
    "value": "132",
    "trend": "+12%",
    "tone": "primary"
  },
  {
    "label": "预约/订单",
    "value": "82",
    "trend": "+8%",
    "tone": "warm"
  },
  {
    "label": "履约率",
    "value": "90%",
    "trend": "+3%",
    "tone": "cool"
  },
  {
    "label": "待处理",
    "value": "5",
    "trend": "需跟进",
    "tone": "neutral"
  }
];

export const operationRecords: OperationRecord[] = [
  {
    "key": "lporienteering-1",
    "name": "活动线路设计与发布",
    "owner": "运营组",
    "status": "已上线",
    "metric": "88%",
    "priority": "高"
  },
  {
    "key": "lporienteering-2",
    "name": "线索打卡点（GPS/二维码）",
    "owner": "管理员",
    "status": "排期中",
    "metric": "31 单",
    "priority": "中"
  },
  {
    "key": "lporienteering-3",
    "name": "团队报名与排名",
    "owner": "服务台",
    "status": "巡检中",
    "metric": "10 项",
    "priority": "低"
  },
  {
    "key": "lporienteering-4",
    "name": "积分兑换商城",
    "owner": "财务组",
    "status": "优化中",
    "metric": "4 级",
    "priority": "高"
  },
  {
    "key": "lporienteering-5",
    "name": "历史线路收藏",
    "owner": "审核组",
    "status": "可导出",
    "metric": "28 条",
    "priority": "中"
  }
];
