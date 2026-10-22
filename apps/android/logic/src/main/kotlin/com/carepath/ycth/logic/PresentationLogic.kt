package com.carepath.ycth.logic

fun completionRate(statuses: List<String>): Int {
    if (statuses.isEmpty()) return 0
    return (statuses.count { it == "COMPLETED" } * 100) / statuses.size
}

fun formatTaskState(status: String, isOverdue: Boolean): String = when {
    status == "COMPLETED" -> "已完成"
    isOverdue -> "已逾期"
    status == "IN_PROGRESS" -> "进行中"
    status == "SKIPPED" -> "已跳过"
    else -> "待完成"
}
