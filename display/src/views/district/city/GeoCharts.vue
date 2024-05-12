<script setup lang="ts">
import { mapJson } from "@/views/district/city/utils";
import { useDark, useECharts, UtilsEChartsOption } from "@pureadmin/utils";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { formatAmount } from "@/views/home/tabs/scale/utils";
import _ from "lodash";
import ReSegmented from "@/components/ReSegmented/src";
import { OptionsType } from "@/components/ReSegmented";
import {
  fetchTransactionVolumeByDistrictCode,
  TransactionVolumeDistrictYear
} from "@/api/transaction";
import { message } from "@/utils/message";

defineOptions({
  name: "GeoCharts"
});

const props = defineProps({
  districtCode: {
    type: Number,
    require: true,
    default: 450000
  },
  mapName: {
    type: String,
    require: true,
    default: "GuangXi"
  },
  districtName: {
    type: String,
    require: true,
    default: ""
  }
});

const { isDark } = useDark();
const theme = computed(() => (isDark.value ? "dark" : "light"));

const geoChartRef = ref();
const { echarts, setOptions, getInstance } = useECharts(geoChartRef, { theme });

const curSegmentOptions = ref(0);
const segmentOptions: Array<OptionsType> = [
  { label: "2022年" },
  { label: "2023年" },
  { label: "2024年" },
  { label: "总计" }
];
const curSwitchSegmentOptions = ref(0);
const switchSegmentOptions: Array<OptionsType> = [
  { label: "地图" },
  { label: "柱状" }
];

const loading = ref(false);
const chartData = ref<Array<TransactionVolumeDistrictYear>>(null);

const fetchChartData = (code: number) => {
  loading.value = true;
  fetchTransactionVolumeByDistrictCode(code)
    .then(res => {
      console.log("fetchChartData", res);
      if (res.code == 200) {
        chartData.value = res.data;
      } else {
        message("获取数据出错！", { type: "error" });
      }
    })
    .catch(err => {
      console.log("GeoCharts.vue-fetchChartData-catch", err);
      message("网络错误，清重试！", { type: "error" });
    })
    .finally(() => {
      loading.value = false;
    });
};

watch(
  () => props,
  () => {
    if (props.districtCode == null) {
      return;
    }
    fetchChartData(props.districtCode);
  },
  {
    immediate: true,
    deep: true
  }
);

type ChartItem = {
  name: string;
  value: number;
};

const transformedChartData = computed<Map<number, Array<ChartItem>>>(() => {
  if (!chartData.value || chartData.value.length == 0) {
    return null;
  }
  const result = new Map<number, Array<ChartItem>>();
  chartData.value
    .sort((a, b) => {
      return a.year - b.year;
    })
    .forEach((item, index) => {
      const d = item.data.map(item1 => {
        return {
          name: item1.districtName,
          value: item1.volume
        };
      });
      result.set(index, d);
    });
  return result;
});

// 第一次加载新的数据，而不是切换series
const firstLoadChart = ref(true);

watch(
  () => curSegmentOptions,
  () => {
    firstLoadChart.value = true;
  }
);

const curOptions = computed<UtilsEChartsOption>(() => {
  if (transformedChartData.value == null) {
    return null;
  }
  echarts.registerMap(props.mapName, mapJson.get(props.districtCode));
  // 获取当前年份的数据
  const data = _.cloneDeep(
    transformedChartData.value.get(curSegmentOptions.value)
  ).sort((a, b) => {
    return a.value - b.value;
  });

  const commonOptions = {
    title: {
      text: `广西${props.districtName}各地区政府采购规模(${segmentOptions[curSegmentOptions.value].label})`,
      left: "center",
      textStyle: {
        fontSize: 20
      }
    },
    grid: {
      left: "5%",
      right: "10%",
      bottom: "0",
      containLabel: true
    },
    tooltip: {
      trigger: "item",
      valueFormatter(value, _) {
        return formatAmount(value as number);
      }
    }
  } satisfies UtilsEChartsOption;

  // 地图 Options
  if (curSwitchSegmentOptions.value == 0) {
    const maxValue = data[data.length - 1].value;
    const minValue = data[0].value;
    return {
      ...commonOptions,
      visualMap: {
        type: "continuous",
        text: [`${formatAmount(minValue)}`, `${formatAmount(maxValue)}`],
        showLabel: true,
        seriesIndex: [0],
        min: minValue,
        max: maxValue,
        inRange: {
          color: ["#edfbfb", "#b7d6f3", "#40a9ed", "#3598c1", "#215096"]
        },
        formatter: function (value) {
          return formatAmount(value as number);
        },
        textStyle: {
          color: "#000"
        },

        right: "5%",
        top: "70%"
      },
      series: [
        // 地图
        {
          id: "scale",
          type: "map",
          roam: true,
          name: "采购规模",
          map: props.mapName,
          layoutCenter: ["50%", "60%"],
          layoutSize: "80%",
          label: {
            show: true, // 显示标注文本
            fontSize: 16
          },
          zoom: 1.25,
          emphasis: {
            label: {
              formatter: function (params) {
                return `${params.name}: ${formatAmount(params.value as number)}`;
              }
            },
            itemStyle: {
              areaColor: "#ffdb5c",
              shadowColor: "rgb(0,0,0,0.25)",
              shadowBlur: 10,
              shadowOffsetY: 4,
              shadowOffsetX: 4
            }
          },
          data: data,
          animationDurationUpdate: 1000,
          universalTransition: true
        }
      ]
    } satisfies UtilsEChartsOption;
  } else {
    return {
      ...commonOptions,
      yAxis: {
        name: "地区",
        type: "category",
        data: data.map(item => item.name),
        nameLocation: "middle",
        animationDurationUpdate: 1000,
        axisLabel: {
          fontSize: 16
        }
      },
      xAxis: {
        type: "value",
        axisLabel: {
          fontSize: 16,
          formatter(value, _) {
            console.log(value);
            return formatAmount(value as number, 0);
          }
        }
      },
      animationDurationUpdate: 1000,
      series: [
        {
          id: "scale",
          type: "bar",
          label: {
            show: true, // 显示标注文本
            position: "right",
            fontSize: 16,
            formatter(param) {
              return formatAmount(param.value as number);
            }
          },
          universalTransition: true,
          emphasis: {
            label: {
              formatter: function (params) {
                return `${params.name}: ${formatAmount(params.value as number)}`;
              }
            },
            itemStyle: {
              shadowColor: "rgb(0,0,0,0.25)",
              shadowBlur: 10,
              shadowOffsetY: 4,
              shadowOffsetX: 4
            }
          },
          data: data
        }
      ]
    } satisfies UtilsEChartsOption;
  }
});

watch(
  () => curOptions,
  async () => {
    if (curOptions.value == null) {
      return;
    }
    await nextTick();
    if (firstLoadChart.value) {
      getInstance().clear();
      setOptions(curOptions.value);
      firstLoadChart.value = false;
    } else {
      // 切换的时候
      getInstance().setOption(curOptions.value, true);
    }
  },
  {
    immediate: true,
    deep: true
  }
);

onMounted(() => {
  fetchChartData(props.districtCode);
});
</script>

<template>
  <div class="w-full h-full">
    <div class="absolute top-4 right-4 mt-6 mr-6 z-50">
      <ReSegmented :options="segmentOptions" v-model="curSegmentOptions" />
      <div class="flex justify-end">
        <ReSegmented
          :options="switchSegmentOptions"
          v-model="curSwitchSegmentOptions"
        />
      </div>
    </div>
    <div ref="geoChartRef" class="p-4 w-full h-full"></div>
  </div>
</template>

<style scoped lang="css"></style>
