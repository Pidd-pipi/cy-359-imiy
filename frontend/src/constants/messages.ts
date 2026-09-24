export const REQUEST_MESSAGES = {
  overviewFallback: "后端服务未联通，请确认后端已启动（docker compose up -d）。",
  healthPath: "/api/health",
  submitSuccess: "成绩已提交并完成校验",
  duplicateSubmit: "该队伍已有有效成绩，只保留先完成的一份",
  revokeConfirm: "确认撤销该成绩？撤销后队伍回到待结算，原成绩不再参与排名，且只能撤销一次。",
  revokeSuccess: "成绩已撤销，队伍回到待结算",
};
