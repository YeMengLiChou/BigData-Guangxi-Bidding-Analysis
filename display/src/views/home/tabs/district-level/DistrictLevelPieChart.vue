<script setup lang="ts">
import { PieChartData } from "@/views/home/utils/types";
import { computed, nextTick, ref, watch } from "vue";
import { formatAmount } from "@/views/home/tabs/scale/utils";
import { useDark, useECharts } from "@pureadmin/utils";
import { DistrictLevelPieChartData } from "@/views/home/tabs/district-level/utils";

defineOptions({
  name: "DistrictLevelPieChart"
});

const props = defineProps({
  data: {
    type: Array as PropType<Array<DistrictLevelPieChartData>>,
    require: true,
    default: () => {},
  }
});

const { isDark } = useDark();

const theme = computed(() => (isDark.value ? "dark" : "light"));

const pieChartRef = ref();
const { setOptions } = useECharts(pieChartRef, {
  theme
});

const computedPercent = (data: Array<DistrictLevelPieChartData>) => {
  const percents = new Map<string, number>();
  const result = new Map<string, number>();
  let totalCount = 0;
  let totalAmount = 0;

  data.forEach(item => {
    percents.set(item.name, item.value);
    result.set(item.name, item.value);
    totalCount += item.count;
    totalAmount += item.value;
  })

  for (let k of percents.keys()) {
    percents.set(k, Number((percents.get(k) / totalAmount * 100).toFixed(4)));
  }
  return [percents, result];
}

watch(() => props, async () => {
    if (!props.data) {
      return;
    }
    const [ percents, result ] = computedPercent(props.data)
    await nextTick();
    setOptions({
      title: {
        text: `广西政府采购政府级别分布图(2022~2024年)`,
        left: "center",
        textStyle: {
          fontSize: 20,
        }
      },
      grid: {
        left: "5%",
        right: "5%",
        bottom: "5%",
        containLabel: true
      },
      legend: {
        left: "auto",
        top: "bottom",
        right: "15%",
        orient: "vertical",
        itemGap: 20,
        textStyle: {
          fontStyle: 'normal',
          fontWeight: 'normal',
          fontSize: 18,
          fontFamily: 'Microsoft YaHei'
        },
        formatter(name) {
          return `${name}: ${formatAmount(result.get(name))}  (${percents.get(name)}%)`;
        },
      },
      tooltip: {
        trigger: "item",
        formatter: (params) => {
          return `${params.marker} ${params.name}: ${formatAmount(params.value)}<br/>`
            + `${params.marker} ${params.name}: ${params.data.count}项<br/>`
            + `${params.marker} 百分比: ${params.percent}%`;
        }
      },
      series: [
        {
          type: "pie",
          selectedOffset: 24,
          radius: "70%",
          minAngle: 3,
          center: ["50%", "50%"],
          data: props.data,
          animationType: "scale",
          animationEasing: "elasticOut",
          animationDelay: function(idx) {
            return idx * 50;
          },
          percentPrecision: 8,
          label: {
            show: true,
            position: "outer",
            formatter: "{b}: {d}%",
            fontSize: 18,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowOffsetY: 6,
              shadowColor: 'rgb(0, 0, 0, 0.25)',
            },
          }
        },
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

<style scoped lang="scss"></style>
