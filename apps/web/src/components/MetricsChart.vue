<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch } from "vue";
import { BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

const props = defineProps<{
  rows: Array<{
    regionCode: string;
    activePlans: number | null;
    taskCompletionRate: number | null;
    openAlerts: number | null;
    suppressed: boolean;
  }>;
}>();

let chart: echarts.ECharts | null = null;
let observer: ResizeObserver | null = null;
const elementId = `metrics-chart-${crypto.randomUUID()}`;

function render() {
  if (!chart) return;
  chart.setOption({
    animationDuration: 450,
    grid: { left: 24, right: 24, top: 30, bottom: 28, containLabel: true },
    tooltip: {
      trigger: "axis",
      formatter: (items: unknown) => {
        const list = items as Array<{ name: string; value: number }>;
        const item = list[0];
        return item ? `${item.name}<br/>活跃计划：${item.value}` : "";
      },
    },
    xAxis: {
      type: "category",
      data: props.rows.map((row) => row.regionCode),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#d8e4e1" } },
      axisLabel: { color: "#617477" },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#edf3f1" } },
      axisLabel: { color: "#617477" },
    },
    series: [
      {
        type: "bar",
        data: props.rows.map((row) => row.activePlans ?? 0),
        barMaxWidth: 46,
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: "#0d5c63",
        },
        label: {
          show: true,
          position: "top",
          formatter: ({ value }: { value: number }) => (value === 0 ? "抑制" : value),
          color: "#617477",
        },
      },
    ],
  });
}

onMounted(() => {
  const element = document.getElementById(elementId);
  if (!element) return;
  chart = echarts.init(element);
  render();
  observer = new ResizeObserver(() => chart?.resize());
  observer.observe(element);
});

watch(() => props.rows, render, { deep: true });

onBeforeUnmount(() => {
  observer?.disconnect();
  chart?.dispose();
});
</script>

<template>
  <div :id="elementId" class="chart" role="img" aria-label="各区域活跃计划数柱状图"></div>
</template>

<style scoped>
.chart {
  width: 100%;
  min-height: 260px;
}
</style>
