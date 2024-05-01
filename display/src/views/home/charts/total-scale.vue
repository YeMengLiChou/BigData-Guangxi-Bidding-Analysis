<script setup lang="ts">
import { computed, ref } from "vue";
import { useECharts, useDark } from "@pureadmin/utils";

defineOptions({
  name: "TotalScaleCharts"
});

// 加载动画
const loading = ref(true);
// 兼容Dark主题
const { isDark } = useDark();
let theme = computed(() => {
  return isDark.value ? "dark" : "default";
});

const chartRef = ref();
const { setOptions } = useECharts(chartRef, { theme });

function renderEChart() {
  console.log("renderEChart")
  loading.value = true;

  setOptions(
    {
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "shadow"
        }
      },
      xAxis: {
        type: "category",
        data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
      },
      yAxis: {
        type: "value"
      },
      series: [
        {
          data: [120, 200, 150, 80, 70, 110, 130],
          type: "line",
          symbol: "triangle",
          symbolSize: 20,
          lineStyle: {
            color: "#5470C6",
            width: 4,
            type: "dashed"
          },
          itemStyle: {
            borderWidth: 3,
            borderColor: "#EE6666",
            color: "yellow"
          }
        }
      ]
    },
    {
      // 渲染完成
      name: "rendered",
      callback: () => {
        // 隐藏加载动画
        loading.value = false;
      }
    }
  );
}

renderEChart();
</script>

<template>
    <div ref="chartRef" class="chart-container"></div>
</template>

<style lang="css" scoped>
.chart-container {
  width: calc(100%);
  height: calc(100%);
}
</style>
