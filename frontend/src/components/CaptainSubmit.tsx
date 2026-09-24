import { useMemo } from "react";
import { Alert, Button, Card, Empty, Form, Input, Select, Space, Tag, Typography } from "antd";
import { ArrowRightOutlined, CheckCircleFilled } from "@ant-design/icons";
import type { CourseDetail, ResultsOverview, SubmitPayload } from "../types";

interface CaptainSubmitProps {
  course: CourseDetail;
  overview: ResultsOverview;
  submitting: boolean;
  onSubmit: (payload: SubmitPayload) => void;
}

interface FormValues {
  teamName: string;
  sequenceText: string;
  totalTime: string;
}

export function CaptainSubmit({ course, overview, submitting, onSubmit }: CaptainSubmitProps) {
  const [form] = Form.useForm<FormValues>();

  const statusByTeam = useMemo(() => {
    const map = new Map<string, (typeof overview.teamsResults)[number]>();
    overview.teamsResults.forEach((item) => map.set(item.teamName, item));
    return map;
  }, [overview]);

  const fillCourseOrder = () => {
    form.setFieldValue("sequenceText", course.checkpoints.join(", "));
  };

  const handleFinish = (values: FormValues) => {
    const sequence = values.sequenceText
      .split(/[,，\s]+/)
      .map((code) => code.trim())
      .filter(Boolean);
    onSubmit({ teamName: values.teamName, sequence, totalTime: values.totalTime.trim() });
  };

  return (
    <div className="settlement-grid">
      <Card title="队长提交成绩" className="settlement-card">
        <Alert
          type="info"
          message={`当前线路：${course.name}`}
          description={
            <span>
              规定到点顺序：
              {course.checkpoints.map((code, index) => (
                <Tag key={code} color="blue">
                  {index + 1}. {code}
                </Tag>
              ))}
            </span>
          }
          style={{ marginBottom: 16 }}
        />
        <Form<FormValues>
          form={form}
          layout="vertical"
          onFinish={handleFinish}
          initialValues={{ totalTime: "" }}
        >
          <Form.Item
            label="队名"
            name="teamName"
            rules={[{ required: true, message: "请选择参赛队伍" }]}
          >
            <Select placeholder="选择你的队伍" options={course.teams.map((name) => ({ label: name, value: name }))} />
          </Form.Item>
          <Form.Item
            label="到点顺序"
            name="sequenceText"
            extra={`按实际打卡顺序填写点位编码，用逗号或空格分隔（如 CP1, CP2…）。线路共 ${course.checkpoints.length} 个点。`}
            rules={[{ required: true, message: "请填写到点顺序" }]}
          >
            <Input.TextArea rows={3} placeholder="CP1, CP2, CP3, CP4, CP5" />
          </Form.Item>
          <Space style={{ marginBottom: 8 }}>
            <Button size="small" type="dashed" icon={<ArrowRightOutlined />} onClick={fillCourseOrder}>
              填入规定顺序
            </Button>
          </Space>
          <Form.Item
            label="总用时"
            name="totalTime"
            extra="支持 mm:ss / hh:mm:ss（如 42:30 或 1:05:20），也可直接填秒数。"
            rules={[{ required: true, message: "请填写总用时" }]}
          >
            <Input placeholder="42:30" style={{ maxWidth: 220 }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={submitting} size="large">
            提交并结算
          </Button>
        </Form>
      </Card>

      <Card title="本队当前状态" className="settlement-card">
        <Form.Item noStyle shouldUpdate>
          {() => {
            const teamName = Form.useWatch("teamName", form) as string | undefined;
            if (!teamName) {
              return <Empty description="选择队名后查看该队状态" />;
            }
            const result = statusByTeam.get(teamName);
            if (!result) {
              return <Empty description="暂无记录" />;
            }
            const tagColor =
              result.status === "finished"
                ? "success"
                : result.status === "incomplete"
                  ? "error"
                  : "default";
            return (
              <Space direction="vertical" size={10} style={{ width: "100%" }}>
                <Space>
                  <Typography.Text strong>{result.teamName}</Typography.Text>
                  <Tag color={tagColor}>{result.statusLabel}</Tag>
                  {result.rank ? <Tag color="gold">第 {result.rank} 名</Tag> : null}
                </Space>
                <div className="status-line">
                  总用时：<strong>{result.totalTime}</strong>
                </div>
                <div className="status-line">
                  提交顺序：
                  {result.sequence.length ? (
                    result.sequence.map((code, index) => (
                      <Tag key={`${code}-${index}`} color={course.checkpoints[index] === code ? "green" : "orange"}>
                        {code}
                      </Tag>
                    ))
                  ) : (
                    <Typography.Text type="secondary">尚未提交</Typography.Text>
                  )}
                </div>
                {result.issueReason ? (
                  <Alert type="warning" showIcon message={result.issueReason} />
                ) : result.status === "finished" ? (
                  <Alert type="success" icon={<CheckCircleFilled />} message="点位齐全且顺序一致，成绩有效并参与排名。" />
                ) : (
                  <Alert type="info" message="队伍待结算，请队长提交到点顺序与总用时。" />
                )}
              </Space>
            );
          }}
        </Form.Item>
      </Card>
    </div>
  );
}
