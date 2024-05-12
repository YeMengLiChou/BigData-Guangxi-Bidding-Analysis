<script setup lang="ts">
import { useDark, useECharts } from "@pureadmin/utils";
import { computed, nextTick, type PropType, ref, watch } from "vue";
import { formatAmount } from "@/views/home/tabs/scale/utils";
import { LineChartData } from "@/views/home/utils/types";
import { BiddingCountItem } from "@/api/bidding";
import _ from "lodash";

defineOptions({
  name: "TotalBiddingCountBarChart"
});

const props = defineProps({
  data: {
    type: Object as PropType<Array<BiddingCountItem>>,
    default: () => {},
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
    // transform
    if (!props.data) return;

    const data: Array<BiddingCountItem> = _.cloneDeep(props.data).sort(
      (a, b) => {
        return a.year - b.year;
      }
    );
    await nextTick(); // 确保DOM更新完成后再执行
    setOptions({
      title: {
        text: `广西政府采购公告数量(2022~2024年)`,
        left: "center",
        textStyle: {
          fontSize: 22,
        }
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "shadow"
        },
        enterable: true,
      },
      grid: {
        top: "10%",
        left: "5%",
        right: "7%",
        bottom: "5%",
        containLabel: true
      },

      xAxis: [
        {
          name: '公告数量/项',
          nameTextStyle: {
            color: '#000',
            fontSize: 14,
          },
          type: "value",
          axisLabel: {
            fontSize: "0.875rem"
          },
          axisPointer: {
            type: "shadow"
          },
          axisTick: {
            length: 6,
            lineStyle: {
              type: "dashed"
            }
          }
        }
      ],
      yAxis: [
        {
          type: "category",
          axisLabel: {
            fontSize: "0.875rem"
          },
          data: data.map(item => `${item.year}年`)
        }
      ],
      legend: {
        top: 'top',
        left: 'right'
      },
      series: [
        {
          name: "成交公告数量",
          type: "bar",
          stack: "total",
          emphasis: {
            focus: "series",
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowOffsetY: 4,
              shadowColor: 'rgb(0, 0, 0, 0.25)',
            },
          },
          label: {
            show: true,
            color: '#fff',
            fontSize: 18,
          },
          itemStyle: {
            color: '#748ede'
          },
          data: data.map(item => item.winCount)
        },
        {
          name: "废标公告数量",
          type: "bar",
          stack: "total",
          emphasis: {
            focus: "series",
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowOffsetY: 4,
              shadowColor: 'rgb(0, 0, 0, 0.25)',
            },
          },
          label: {
            show: true,
            color: '#f2a800',
            fontSize: 18,
            position: 'top'
          },
          itemStyle: {
            color: '#f2cc76',
          },
          data: data.map(item => item.loseCount)
        },
        {
          name: "终止公告数量",
          type: "bar",
          stack: "total",
          emphasis: {
            focus: "series",
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowOffsetY: 4,
              shadowColor: 'rgb(0, 0, 0, 0.25)',
            },
          },
          label: {
            show: true,
            overflow: "truncate",
            color: '#f60009',
            fontSize: 18,
            position: 'bottom'
          },
          itemStyle: {
            color: '#f6868a',
          },
          data: data.map(item => item.terminateCount)
        },
        {
          name: '总公告数量',
          type: 'line',
          data: data.map(item => item.terminateCount + item.loseCount + item.winCount),
          label: {
            show: true,
            color: '#333',
            fontSize: 20,
            position: 'right',
            align: 'left',
            fontWeight: 'normal'
          },
        }
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

<style scoped lang="scss"></style>
