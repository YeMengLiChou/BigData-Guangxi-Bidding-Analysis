<script setup lang="ts">
import { useDark, useECharts } from "@pureadmin/utils";
import { computed, nextTick, type PropType, ref, watch } from "vue";
import { formatAmount } from "@/views/home/tabs/scale/utils";
import { LineChartData } from "@/views/home/utils/types";

defineOptions({
  name: "TotalScaleBarChart"
});

const props = defineProps({
  data: {
    type: Object as PropType<LineChartData>,
    default: () => {},
    required: true,
  },
});

const { isDark } = useDark();

const theme = computed(() => (isDark.value ? "dark" : "light"));

const chartRef = ref();
const { setOptions } = useECharts(chartRef, {
  theme
});

watch(
  () => props,
  async () => {
    await nextTick(); // 确保DOM更新完成后再执行
    setOptions({
      title: {
        text: `广西政府采购总规模(2022~2024年)`,
        left: 'center',
        textStyle: {
          fontSize: 18,
        }
      },
      color: ["#41b6ff"],
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: 'shadow'
        },
        enterable: true,
        valueFormatter(value, _) {
          return formatAmount(value as number);
        },
      },
      grid: {
        top: "10%",
        left: "5%",
        right: "6%",
        bottom: '5%',
        containLabel: true
      },
      legend: {
        data: ["总交易量"],
        textStyle: {
          color: "#606266",
          fontSize: "0.875rem"
        },
        left: 'right',
        top: '5%'
      },
      xAxis: [
        {
          type: "log",
          axisLabel: {
            fontSize: "0.875rem",
            formatter(value, _) {
                return formatAmount(value, 0);
            },
          },
          axisPointer: {
            type: "shadow"
          },
          axisTick: {
            length: 6,
            lineStyle: {
              type: 'dashed'
            },
          }
        }
      ],
      yAxis: [
        {
          type: "category",
          axisLabel: {
            fontSize: "0.875rem"
          },
          data: props.data?.xAxisData,
        }
      ],
      series: [
        {
          name: "总交易量",
          type: "bar",
          itemStyle: {
            color: "#41b6ff",
          },
          labelLine: {
            show: true,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowOffsetY: 6,
              shadowColor: 'rgb(0, 0, 0, 0.25)',
            },
          },
          label: {
            show: true,
            position: 'top',
            fontSize: 16,
            formatter: function(param) {
              return formatAmount(param.value as number);
            }
          },
          data: props.data?.yAxisData
        },
      ]
    });
  },
  {
    deep: true,
    immediate: true
  }
);

</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 100%" />
</template>

<style scoped lang="scss">

</style>
