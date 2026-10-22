export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "已抑制";
  return `${Math.round(value * 100)}%`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "未设置";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "长期";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

export const taskStatusLabels: Record<string, string> = {
  PENDING: "待完成",
  IN_PROGRESS: "进行中",
  COMPLETED: "已完成",
  SKIPPED: "已跳过",
};

export const alertStatusLabels: Record<string, string> = {
  OPEN: "待处理",
  ACKNOWLEDGED: "已确认",
  RESOLVED: "已解决",
  PENDING: "待审核",
  APPROVED: "已通过",
  REJECTED: "已驳回",
};
