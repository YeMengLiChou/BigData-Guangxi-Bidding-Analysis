<script setup lang="ts">
import { useDark, useECharts } from "@pureadmin/utils";
import { type PropType, ref, computed, watch, nextTick } from "vue";
import { LineChartData } from "@/views/home/utils/types";
import { formatAmount } from "@/views/home/tabs/scale/utils";
defineOptions({
  name: "ScaleLineChart"
});

const props = defineProps({
  data: {
    type: Object as PropType<LineChartData>,
    default: () => {},
    required: true,
  },
  year: {
    type: String,
    default: "",
    required: true,
  },
  timespan: {
    type: String,
    default: "",
    required: true
  }
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
        text: `广西政府${props.timespan}采购规模(${props.year})`,
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
        right: "5%",
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
        top: '20%'
      },
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          start: 0,
          end: 100
        },
        {
          show: props.data?.xAxisData?.length > 50,
          xAxisIndex: 0,
          type: 'slider',
          top: '80%',
          start: 80,
          end: 100
        }
      ],
      xAxis: [
        {
          type: "category",
          name: `时间\n/${props.timespan}`,
          nameTextStyle: {
            fontSize: 15,

          },
          data: props.data?.xAxisData,
          axisLabel: {
            fontSize: "0.875rem"
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
          type: "log",
          name: '成交总金额/亿元',
          nameTextStyle: {
            fontSize: 15,

          },
          axisLabel: {
            fontSize: "0.875rem",
            formatter(value, _) {
                return formatAmount(value, 0)
            },
          },
        }
      ],
      series: [
        {
          name: "总交易量",
          type: "line",
          itemStyle: {
            color: "#41b6ff",
          },
          smooth: true,
          label: {
            show: true,
            formatter: function(param) {
              return formatAmount(param.value as number);
            },
            position: 'top',
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
