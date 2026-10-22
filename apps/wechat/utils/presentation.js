function completionRate(tasks) {
  if (!tasks.length) return 0;
  return Math.round(
    (tasks.filter((task) => task.status === "COMPLETED").length * 100) / tasks.length,
  );
}

function taskStateLabel(task) {
  if (task.status === "COMPLETED") return "已完成";
  if (task.isOverdue) return "已逾期";
  if (task.status === "IN_PROGRESS") return "进行中";
  if (task.status === "SKIPPED") return "已跳过";
  return "待完成";
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const pad = (number) => String(number).padStart(2, "0");
  return `${pad(date.getMonth() + 1)}月${pad(date.getDate())}日 ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

module.exports = {
  completionRate,
  taskStateLabel,
  formatDateTime,
};
