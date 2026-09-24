-- 定向越野成绩结算表结构（与 Django 迁移 domain/0001_initial.py 保持一致，供 DBA 查阅）

CREATE TABLE IF NOT EXISTS route (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  description VARCHAR(255) NOT NULL DEFAULT '',
  checkpoint_sequence JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS team_result (
  id BIGSERIAL PRIMARY KEY,
  route_id BIGINT NOT NULL REFERENCES route(id),
  team_name VARCHAR(120) NOT NULL,
  submitted_sequence JSONB NOT NULL DEFAULT '[]'::jsonb,
  total_seconds INTEGER NOT NULL CHECK (total_seconds > 0),
  status VARCHAR(16) NOT NULL DEFAULT 'incomplete'
    CHECK (status IN ('completed', 'incomplete', 'revoked')),
  issues JSONB NOT NULL DEFAULT '[]'::jsonb,
  result_note VARCHAR(255) NOT NULL DEFAULT '',
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  revoked_at TIMESTAMPTZ NULL,
  revoke_reason VARCHAR(255) NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_team_result_route_status ON team_result (route_id, status);
CREATE INDEX IF NOT EXISTS idx_team_result_route_team ON team_result (route_id, team_name);

-- 同一队伍同一线路仅允许一份非撤销记录：重复提交被拒绝，裁判撤销后队伍回到待结算
CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_result_per_team_route
  ON team_result (route_id, team_name)
  WHERE status <> 'revoked';
