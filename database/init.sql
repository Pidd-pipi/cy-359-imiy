-- 城市定向越野平台 —— 赛后成绩结算参考表结构
--
-- 说明：Django 启动时会通过 entrypoint.sh 自动执行 migrations，
-- 实际表结构以 backend/domain/migrations/ 为准；
-- 本脚本仅作为数据库层的说明与外部系统对接参考，可手动执行。

CREATE TABLE IF NOT EXISTS domain_course (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS domain_checkpoint (
  id BIGSERIAL PRIMARY KEY,
  course_id BIGINT NOT NULL REFERENCES domain_course(id) ON DELETE CASCADE,
  code VARCHAR(32) NOT NULL,
  name VARCHAR(120) NOT NULL DEFAULT '',
  position INTEGER NOT NULL CHECK (position > 0),
  UNIQUE (course_id, position)
);

CREATE TABLE IF NOT EXISTS domain_teamresult (
  id BIGSERIAL PRIMARY KEY,
  team_name VARCHAR(80) NOT NULL,
  course_id BIGINT NOT NULL REFERENCES domain_course(id),
  checkpoint_sequence JSONB NOT NULL DEFAULT '[]',
  total_seconds INTEGER CHECK (total_seconds IS NULL OR total_seconds > 0),
  status VARCHAR(16) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'finished', 'incomplete', 'revoked')),
  issue_reason VARCHAR(200) NOT NULL DEFAULT '',
  rank INTEGER,
  revoke_count INTEGER NOT NULL DEFAULT 0,
  submitted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  settled_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS domain_teamresult_team_status_idx
  ON domain_teamresult (team_name, status);

-- 默认线路与 Django 数据迁移 0002 保持一致
INSERT INTO domain_course (name, is_active)
VALUES ('城市公园标准线', TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO domain_checkpoint (course_id, code, name, position)
SELECT c.id, cp.code, '打卡点 ' || cp.code, cp.position
FROM domain_course c
CROSS JOIN (VALUES ('CP1', 1), ('CP2', 2), ('CP3', 3), ('CP4', 4), ('CP5', 5)) AS cp(code, position)
WHERE NOT EXISTS (SELECT 1 FROM domain_checkpoint WHERE course_id = c.id);
