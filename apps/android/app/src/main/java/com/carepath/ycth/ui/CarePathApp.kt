package com.carepath.ycth.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Medication
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.carepath.ycth.data.AlertDto
import com.carepath.ycth.data.MobileSummaryDto
import com.carepath.ycth.data.PatientDashboardDto
import com.carepath.ycth.data.SessionSnapshot
import com.carepath.ycth.data.TaskDto
import com.carepath.ycth.logic.completionRate
import com.carepath.ycth.logic.formatTaskState
import com.carepath.ycth.reminder.ReminderWorker
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

private data class DemoAccount(val username: String, val password: String, val label: String)

private data class DemoRole(val title: String, val accounts: List<DemoAccount>)

private val demoRoles = listOf(
    DemoRole("医院", listOf(
        DemoAccount("doctor", "Do2026!care", "医生"),
        DemoAccount("hospital", "Ho2026!care", "院务"),
    )),
    DemoRole("社区与志愿", listOf(
        DemoAccount("community", "Co2026!care", "社区"),
        DemoAccount("volunteer", "Vo2026!care", "志愿者"),
    )),
    DemoRole("药企", listOf(DemoAccount("pharma", "Ph2026!care", "药企"))),
    DemoRole("政府", listOf(DemoAccount("regulator", "Re2026!care", "政府"))),
    DemoRole("用户 / 居民", listOf(DemoAccount("patient", "Pa2026!care", "居民"))),
)

@Composable
fun CarePathApp(
    state: CarePathUiState,
    onLogin: (String, String) -> Unit,
    onCompleteTask: (String) -> Unit,
    onLogout: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background,
    ) {
        if (state.session == null) {
            LoginScreen(
                loading = state.loading,
                error = state.error,
                onLogin = onLogin,
            )
        } else {
            val isUser = state.session?.role == "PATIENT" || state.session?.role == "CAREGIVER"
            if (!isUser) {
                ManagementScreen(
                    state = state,
                    onLogout = onLogout,
                )
            } else {
                PatientHomeScreen(
                    state = state,
                    session = state.session,
                    onCompleteTask = onCompleteTask,
                    onLogout = onLogout,
                )
            }
        }
    }
}

@Composable
private fun LoginScreen(
    loading: Boolean,
    error: String?,
    onLogin: (String, String) -> Unit,
) {
    var roleIndex by rememberSaveable { mutableStateOf(0) }
    var accountIndex by rememberSaveable { mutableStateOf(0) }
    var username by rememberSaveable { mutableStateOf(demoRoles[0].accounts[0].username) }
    var password by rememberSaveable { mutableStateOf(demoRoles[0].accounts[0].password) }

    fun selectAccount(role: Int, account: Int) {
        roleIndex = role
        accountIndex = account
        username = demoRoles[role].accounts[account].username
        password = demoRoles[role].accounts[account].password
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    listOf(Color(0xFFF9FEFC), Color(0xFFEAF8F4)),
                ),
            ),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(24.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item {
            Spacer(Modifier.height(44.dp))
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .background(
                        Color(0xFFBCEBDD),
                        RoundedCornerShape(topStart = 20.dp, topEnd = 20.dp, bottomEnd = 20.dp),
                    ),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = "医",
                    style = MaterialTheme.typography.headlineLarge,
                    color = Color(0xFF2C5F53),
                )
            }
            Spacer(Modifier.height(24.dp))
            Text(
                text = "医疗健康保障协同平台",
                style = MaterialTheme.typography.headlineLarge,
                color = Color(0xFF173437),
            )
            Text(
                text = "医院、社区、药企、政府与居民在同一条照护路径上协作。",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 10.dp),
            )
        }
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(22.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
            ) {
                Column(
                    modifier = Modifier.padding(22.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Text("左右滑动选择角色", style = MaterialTheme.typography.titleLarge)
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        itemsIndexed(demoRoles) { index, role ->
                            Card(
                                modifier = Modifier
                                    .width(170.dp)
                                    .clickable { selectAccount(index, 0) },
                                colors = CardDefaults.cardColors(
                                    containerColor = if (roleIndex == index) {
                                        Color(0xFFEAF9F6)
                                    } else {
                                        Color(0xFFFBFEFD)
                                    },
                                ),
                                shape = RoundedCornerShape(18.dp),
                            ) {
                                Column(
                                    modifier = Modifier.padding(14.dp),
                                    verticalArrangement = Arrangement.spacedBy(6.dp),
                                ) {
                                    Text(role.title, fontWeight = FontWeight.SemiBold)
                                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                        role.accounts.forEachIndexed { accountIdx, account ->
                                            TextButton(
                                                onClick = { selectAccount(index, accountIdx) },
                                                contentPadding = androidx.compose.foundation.layout.PaddingValues(4.dp),
                                            ) {
                                                Text(
                                                    if (roleIndex == index && accountIndex == accountIdx) {
                                                        "● " + account.label
                                                    } else {
                                                        account.label
                                                    },
                                                    fontSize = 12.sp,
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    OutlinedTextField(
                        value = username,
                        onValueChange = { username = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("账号") },
                        singleLine = true,
                    )
                    OutlinedTextField(
                        value = password,
                        onValueChange = { password = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("密码") },
                        singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                    )
                    if (error != null) {
                        Text(
                            text = error,
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
                    Button(
                        onClick = { onLogin(username, password) },
                        enabled = !loading && username.isNotBlank() && password.isNotBlank(),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                    ) {
                        if (loading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(20.dp),
                                strokeWidth = 2.dp,
                                color = Color.White,
                            )
                        } else {
                            Text("进入平台")
                        }
                    }
                    Text(
                        text = "用户 / 居民为统一入口；家属账号 caregiver / Ca2026!care 可手动输入。",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
        item {
            Text(
                text = "当前为工程演示端，使用合成病例，不提供诊断、处方或真实监管结论。",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 4.dp),
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ManagementScreen(
    state: CarePathUiState,
    onLogout: () -> Unit,
) {
    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { Text("医疗健康保障协同平台") },
                actions = {
                    IconButton(onClick = onLogout) {
                        Icon(Icons.AutoMirrored.Outlined.Logout, contentDescription = "退出登录")
                    }
                },
            )
        },
    ) { padding ->
        val summary: MobileSummaryDto? = state.summary
        if (summary == null) {
            Box(
                Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding).padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                item {
                    Text(summary.heading, style = MaterialTheme.typography.headlineSmall)
                    Text(
                        summary.identityLabel + " · 仅限本组织数据",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                item {
                    Column {
                        summary.metrics.forEach { metric ->
                            Text(
                                metric.label + "：" + metric.value,
                                style = MaterialTheme.typography.titleMedium,
                            )
                        }
                    }
                }
                items(summary.items) { item ->
                    Column {
                        Text(item.title, style = MaterialTheme.typography.titleMedium)
                        Text(
                            item.detail,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PatientHomeScreen(
    state: CarePathUiState,
    session: SessionSnapshot,
    onCompleteTask: (String) -> Unit,
    onLogout: () -> Unit,
) {
    val context = LocalContext.current
    val dashboard = state.dashboard
    val nextTask = remember(dashboard) {
        dashboard?.tasks?.firstOrNull { it.status != "COMPLETED" }
    }

    LaunchedEffect(nextTask?.id, nextTask?.dueAt) {
        if (nextTask != null) {
            ReminderWorker.schedule(context, nextTask.title, nextTask.dueAt)
        }
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "医疗健康保障协同平台",
                            style = MaterialTheme.typography.titleLarge,
                        )
                        Text(
                            text = "${session.displayName} · ${if (session.role == "CAREGIVER") "家属" else "患者"}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
                actions = {
                    IconButton(onClick = onLogout) {
                        Icon(Icons.AutoMirrored.Outlined.Logout, contentDescription = "退出登录")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
    ) { innerPadding ->
        if (dashboard == null) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentAlignment = Alignment.Center,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    if (state.error != null) {
                        Text(
                            text = state.error,
                            modifier = Modifier.padding(top = 12.dp),
                            color = MaterialTheme.colorScheme.error,
                        )
                    }
                }
            }
        } else {
            PatientDashboard(
                dashboard = dashboard,
                loading = state.loading,
                syncWarning = state.error,
                onCompleteTask = onCompleteTask,
                modifier = Modifier.padding(innerPadding),
            )
        }
    }
}

@Composable
private fun PatientDashboard(
    dashboard: PatientDashboardDto,
    loading: Boolean,
    syncWarning: String?,
    onCompleteTask: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val statuses = dashboard.tasks.map { it.status }
    val progress = completionRate(statuses)

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Text(
                text = "${dashboard.patient.displayName}的治疗进度",
                style = MaterialTheme.typography.headlineMedium,
            )
            Text(
                text = dashboard.plan?.title ?: "暂无已发布计划",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 5.dp),
            )
        }
        if (loading) {
            item {
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            }
        }
        if (syncWarning != null) {
            item {
                Text(
                    text = syncWarning,
                    color = Color(0xFF8C5A1F),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFFFFF3DF), RoundedCornerShape(12.dp))
                        .padding(12.dp),
                )
            }
        }
        item {
            PlanHero(
                progress = progress,
                taskTitle = dashboard.tasks.firstOrNull { it.status != "COMPLETED" }?.title
                    ?: "当前任务全部完成",
                summary = dashboard.plan?.content?.summary ?: "按计划完成随访并记录变化。",
            )
        }
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                MetricCard("${dashboard.tasks.size}", "协同任务", Modifier.weight(1f))
                MetricCard("${dashboard.medications.size}", "用药安排", Modifier.weight(1f))
                MetricCard(
                    "${dashboard.alerts.count { it.status == "OPEN" }}",
                    "待处理",
                    Modifier.weight(1f),
                )
            }
        }
        item {
            SectionHeading("协同任务", "按截止时间排序")
        }
        items(dashboard.tasks, key = { it.id }) { task ->
            TaskCard(task = task, onComplete = { onCompleteTask(task.id) })
        }
        item {
            SectionHeading("用药安排", "仅作计划与服药记录")
        }
        items(dashboard.medications, key = { it.id }) { medication ->
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(16.dp),
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        Icons.Outlined.Medication,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                    )
                    Column {
                        Text(medication.drugName, fontWeight = FontWeight.SemiBold)
                        Text(
                            "${medication.doseText} · ${medication.frequencyText}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
        if (dashboard.alerts.isNotEmpty()) {
            item {
                SectionHeading("异常提醒", "系统不会自动调整方案")
            }
            items(dashboard.alerts, key = { it.id }) { alert ->
                AlertCard(alert)
            }
        }
        item {
            Text(
                text = "本应用仅用于工程演示，不提供诊疗建议。如有不适，请联系医疗机构。",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(vertical = 12.dp),
            )
        }
    }
}

@Composable
private fun PlanHero(
    progress: Int,
    taskTitle: String,
    summary: String,
) {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.linearGradient(
                        listOf(Color(0xFF0D5C63), Color(0xFF173F43)),
                    ),
                )
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "下一步",
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFFEFC47F),
                fontWeight = FontWeight.Bold,
            )
            Text(
                taskTitle,
                style = MaterialTheme.typography.headlineMedium,
                color = Color.White,
            )
            Text(
                summary,
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFFC5E1DC),
            )
            LinearProgressIndicator(
                progress = { progress / 100f },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp),
                color = Color(0xFFEFC47F),
                trackColor = Color(0x33FFFFFF),
            )
            Text(
                "$progress% 任务已完成",
                color = Color(0xFFC5E1DC),
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

@Composable
private fun MetricCard(value: String, label: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
    ) {
        Column(Modifier.padding(15.dp)) {
            Text(value, style = MaterialTheme.typography.headlineMedium)
            Text(
                label,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun SectionHeading(title: String, subtitle: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Bottom,
    ) {
        Text(title, style = MaterialTheme.typography.titleLarge)
        Text(
            subtitle,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun TaskCard(task: TaskDto, onComplete: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        shape = RoundedCornerShape(18.dp),
    ) {
        Column(
            modifier = Modifier.padding(17.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(task.title, fontWeight = FontWeight.SemiBold)
                    Text(
                        task.description,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                Text(
                    text = formatTaskState(task.status, task.isOverdue),
                    color = when {
                        task.status == "COMPLETED" -> Color(0xFF248265)
                        task.isOverdue -> MaterialTheme.colorScheme.error
                        else -> Color(0xFF8C5A1F)
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold,
                )
            }
            Text(
                formatDateTime(task.dueAt),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (task.status != "COMPLETED") {
                Button(
                    onClick = onComplete,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Icon(Icons.Outlined.CheckCircle, contentDescription = null)
                    Text("标记为已完成", modifier = Modifier.padding(start = 8.dp))
                }
            }
        }
    }
}

@Composable
private fun AlertCard(alert: AlertDto) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (alert.severity == "HIGH") {
                Color(0xFFFBECEA)
            } else {
                Color(0xFFFFF7E9)
            },
        ),
        shape = RoundedCornerShape(16.dp),
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Icon(
                Icons.Outlined.Notifications,
                contentDescription = null,
                tint = if (alert.severity == "HIGH") {
                    MaterialTheme.colorScheme.error
                } else {
                    Color(0xFF8C5A1F)
                },
            )
            Column {
                Text(alert.title, fontWeight = FontWeight.SemiBold)
                Text(
                    alert.detail,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

private fun formatDateTime(value: String): String = runCatching {
    Instant.parse(value)
        .atZone(ZoneId.systemDefault())
        .format(DateTimeFormatter.ofPattern("MM月dd日 HH:mm"))
}.getOrDefault(value)
