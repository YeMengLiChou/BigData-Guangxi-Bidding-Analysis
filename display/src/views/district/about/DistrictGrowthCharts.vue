<script setup lang="ts">
import { LineChartData } from "@/views/home/utils/types";
import { computed, nextTick, ref, watch } from "vue";
import { useDark, useECharts } from "@pureadmin/utils";
import { DistrictTransactionGrowthItem } from "@/api/transaction";
import _ from "lodash";
import { formatAmount } from "@/views/home/tabs/scale/utils";
import { SeriesOption } from "echarts";

defineOptions({
  name: "DistrictGrowthCharts"
});

const props = defineProps({
  data: {
    type: Array as PropType<Array<DistrictTransactionGrowthItem>>,
    require: true,
    default: () => [],
  }
});

const { isDark } = useDark();
const theme = computed(() => (isDark.value ? "dark" : "light"));
const chartRef = ref();
const { setOptions } = useECharts(chartRef, { theme });

watch(
  () => props,
  async () => {
    if (!props.data || props.data.length == 0) return;
    const seriesList: echarts.SeriesOption[] = [];
    const data: Array<DistrictTransactionGrowthItem> = _.cloneDeep(props.data);
    console.log(data);

    for (const item of data) {
      const curData = item.data.sort((a, b) => {
        return a.timestamp - b.timestamp;
      }).map(item => {
        const date = new Date(item.timestamp);
        const str = `${date.getFullYear()}年${date.getMonth() + 1}月`
        return {
          name: str, value: item.value
        };
      }) as Array<Object>;
      seriesList.push({
        type: 'line',
        name: item.districtName,
        showSymbol: false,
        showAllSymbol: false,
        smooth: true,
        emphasis: {
          focus: 'series',
        },
        lineStyle:{
          width: 2.5,
        },
        endLabel: {
          show: true,
          fontSize: 16,
          valueAnimation: true,
          formatter: function (params: any) {
            return params.seriesName+ ': ' + formatAmount(params.value);
          }
        },
        labelLayout: {
          moveOverlap: 'shiftY'
        },
        data: curData,
      } as SeriesOption)
    }
    await nextTick();
    setOptions({
      animationDuration: 5000,
      title: [{
        text: '广西各市增长情况',
        left: 'center',
        top: '5%',
      }],
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 'center',
        textStyle: {
          fontSize: 16,
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        textStyle: {
          fontSize: 16,
        },
        valueFormatter(value, _) {
            return formatAmount(value as number);
        },
      },
      series: seriesList,
      xAxis: {
        type:'category',
        nameLocation: 'middle'
      },
      yAxis: {
        type: 'log',
        name: '采购规模',
        axisLabel: {
          formatter(value, _) {
              return formatAmount(value, 0);
          },
        }
      },
      grid: {
        right: '15%',
        top: '10%',
        left: '15%'
      },
    })

  },
  {
    immediate: true,
    deep: true
  }
);
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 100%"></div>
</template>

<style scoped lang="scss"></style>
