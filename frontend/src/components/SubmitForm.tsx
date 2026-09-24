import { useMemo } from "react";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Tag,
  Typography,
} from "antd";
import { SendOutlined } from "@ant-design/icons";
import type { RouteInfo, SubmitResultPayload } from "../types";

const { Text } = Typography;

interface SubmitFormProps {
  routes: RouteInfo[];
  submitting: boolean;
  onSubmit: (payload: SubmitResultPayload) => void;
}

function toSeconds(hours: number, minutes: number, seconds: number): number {
  return hours * 3600 + minutes * 60 + seconds;
}

export function SubmitForm({ routes, submitting, onSubmit }: SubmitFormProps) {
  const [form] = Form.useForm();
  const selectedRouteId = Form.useWatch("routeId", form) as number | undefined;

  const selectedRoute = useMemo(
    () => routes.find((route) => route.id === selectedRouteId),
    [routes, selectedRouteId]
  );

  const handleFinish = (values: {
    routeId: number;
    teamName: string;
    sequenceText: string;
    hours: number;
    minutes: number;
    seconds: number;
  }) => {
    const submittedSequence = values.sequenceText
      .split(/[\s,，、;；]+/)
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean);

    onSubmit({
      routeId: values.routeId,
      teamName: values.teamName.trim(),
      submittedSequence,
      totalSeconds: toSeconds(values.hours ?? 0, values.minutes ?? 0, values.seconds ?? 0),
    });
  };

  return (
    <Card title="队长提交成绩" className="settle-card">
      {routes.length === 0 ? (
        <Alert type="warning" showIcon message="暂无可选线路，请联系管理员发布线路。" />
      ) : (
        <Form
          form={form}
          layout="vertical"
          requiredMark="optional"
          initialValues={{
            routeId: routes[0]?.id,
            hours: 1,
            minutes: 0,
            seconds: 0,
          }}
          onFinish={handleFinish}
        >
          <Form.Item
            name="routeId"
            label="比赛线路"
            rules={[{ required: true, message: "请选择线路" }]}
          >
            <Select
              options={routes.map((route) => ({
                value: route.id,
                label: `${route.name}（${route.checkpointCount} 个点）`,
              }))}
            />
          </Form.Item>

          <Form.Item
            name="teamName"
            label="队名"
            rules={[
              { required: true, message: "请输入队名" },
              { max: 120, message: "队名不能超过 120 个字符" },
            ]}
          >
            <Input placeholder="例如：疾风队" allowClear />
          </Form.Item>

          <Form.Item label="总用时" required>
            <Space wrap align="center">
              <Form.Item
                name="hours"
                noStyle
                rules={[{ required: true, message: "请填写小时" }]}
              >
                <InputNumber min={0} max={99} addonAfter="时" style={{ width: 110 }} />
              </Form.Item>
              <Form.Item
                name="minutes"
                noStyle
                rules={[{ required: true, message: "请填写分钟" }]}
              >
                <InputNumber min={0} max={59} addonAfter="分" style={{ width: 110 }} />
              </Form.Item>
              <Form.Item
                name="seconds"
                noStyle
                rules={[{ required: true, message: "请填写秒" }]}
              >
                <InputNumber min={0} max={59} addonAfter="秒" style={{ width: 110 }} />
              </Form.Item>
            </Space>
          </Form.Item>

          <Form.Item
            name="sequenceText"
            label="到点顺序"
            extra="按实际打卡顺序填写点位编号，支持空格、逗号或顿号分隔。"
            rules={[{ required: true, message: "请填写到点顺序" }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="例如：CP1 CP2 CP3 CP4"
            />
          </Form.Item>

          {selectedRoute && (
            <div className="route-hint">
              <Text type="secondary">
                线路「{selectedRoute.name}」规定顺序（{selectedRoute.description}）：
              </Text>
              <div className="tag-row">
                {selectedRoute.checkpointSequence.map((code, index) => (
                  <Tag color="blue" key={code}>
                    {index + 1}. {code}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SendOutlined />}
              loading={submitting}
              block
            >
              提交并校验
            </Button>
          </Form.Item>
        </Form>
      )}
    </Card>
  );
}
