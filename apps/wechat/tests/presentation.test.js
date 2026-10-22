const assert = require("node:assert/strict");
const test = require("node:test");

const {
  completionRate,
  formatDateTime,
  taskStateLabel,
} = require("../utils/presentation.js");

test("small-program task labels handle overdue and completed", () => {
  assert.equal(
    taskStateLabel({ status: "PENDING", isOverdue: true }),
    "已逾期",
  );
  assert.equal(
    taskStateLabel({ status: "COMPLETED", isOverdue: false }),
    "已完成",
  );
});

test("small-program completion rate handles empty list", () => {
  assert.equal(completionRate([]), 0);
  assert.equal(completionRate([{ status: "COMPLETED" }, { status: "PENDING" }]), 50);
});

test("small-program date formatter preserves invalid source values", () => {
  assert.equal(formatDateTime("not-a-date"), "not-a-date");
  assert.match(formatDateTime("2026-10-22T08:00:00Z"), /\d{2}:\d{2}/);
});
