<script setup lang="ts">
import { useDark, useECharts } from "@pureadmin/utils";
import { computed, nextTick, ref, watch } from "vue";
import { PieChartData } from "@/views/home/utils/types";
import { formatAmount } from "@/views/home/tabs/scale/utils";

defineOptions({
  name: "ProcurementPieChart"
});

const props = defineProps({
  countData: {
    type: Array as PropType<Array<PieChartData>>,
    required: true,
    default: () => []
  },
  transactionData: {
    type: Array as PropType<Array<PieChartData>>,
    required: true,
    default: () => []
  },
  year: {
    type: String,
    required: true,
    default: ""
  }
});

const { isDark } = useDark();

const theme = computed(() => (isDark.value ? "dark" : "light"));

const pieChartRef = ref();
const { setOptions } = useECharts(pieChartRef, {
  theme
});
// 更新数据
watch(
  () => props,
  async () => {
    await nextTick();
    setOptions({
      title: [
        {
          text: `广西政府采购方式对比(${props.year})`,
          left: "center",
          textStyle: {
            fontSize: 22,
          }
        },
        {
          subtext: "采购方式公告数",
          left: "25%",
          top: "85%",
          textAlign: "center",
          subtextStyle: {
            fontStyle: 'normal',
            fontWeight: 'bold',
            fontSize: 16,
          }
        },
        {
          subtext: "采购方式成交量",
          left: "75%",
          top: "85%",
          textAlign: "center",
          subtextStyle: {
            fontStyle: 'normal',
            fontWeight: 'bold',
            fontSize: 16,
          }
        }
      ],
      grid: {
        left: "5%",
        right: "5%",
        bottom: "5%",
        containLabel: true
      },
      legend: {
        left: "center",
        top: "bottom"
      },
      tooltip: {
        trigger: "item",
        formatter: (params, _) => {
          if (params.seriesIndex == 1) {
            return `${params.marker} ${params.name}: ${formatAmount(params.value)}(${params.percent}%)`;
          } else if (params.seriesIndex == 0) {
            return `${params.marker} ${params.name}: ${params.value}项(${params.percent}%)`;
          }
        }
      },
      series: [
        {
          type: "pie",
          selectedOffset: 24,
          radius: "60%",
          minAngle: 3,
          center: ["25%", "50%"],
          data: props.countData,
          animationType: "scale",
          animationEasing: "elasticOut",
          animationDelay: function (idx) {
            return idx * 50;
          },
          percentPrecision: 6,
          label: {
            show: true,
            position: "outer",
            formatter: "{b}: {d}%",
            fontSize: 16,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.25)'
            }
          }
        },
        {
          type: "pie",
          selectedOffset: 24,
          radius: "60%",
          minAngle: 5,
          center: ["75%", "50%"],
          data: props.transactionData,
          animationType: "scale",
          animationEasing: "elasticOut",
          animationDelay: function (idx) {
            return idx * 50;
          },
          percentPrecision: 8,
          label: {
            show: true,
            position: "outer",
            formatter: "{b}: {d}%",
            fontSize: 16,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.25)'
            }
          }
        }
      ]
    });
  },
  {
    immediate: true,
    deep: true
  }
);
</script>

<template>
  <div ref="pieChartRef" style="width: 100%; height: 100%" />
</template>

<style scoped lang="css"></style>
