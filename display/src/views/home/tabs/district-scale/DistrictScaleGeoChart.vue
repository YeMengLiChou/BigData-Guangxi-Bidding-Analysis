<script setup lang="ts">
import { useDark, useECharts } from "@pureadmin/utils";
import { computed, nextTick, ref, watch } from "vue";
import { formatAmount } from "@/views/home/tabs/scale/utils";
import mapJson from "@/assets/map/map.json";
import _ from "lodash";
import { TransactionGeoChartItem } from "@/views/home/tabs/district-scale/utils";

defineOptions({
  name: "DistrictScaleGeoChart"
});

const props = defineProps({
  data: {
    type: Array as PropType<TransactionGeoChartItem>,
    require: true,
    default: () => []
  },
  year: {
    type: String,
    require: true,
    default: ""
  }
});

const { isDark } = useDark();

const theme = computed(() => (isDark.value ? "dark" : "light"));

const geoChartRef = ref();
const { echarts, setOptions, getInstance } = useECharts(geoChartRef, {
  theme
});
echarts.registerMap("Guangxi", { geoJSON: mapJson });

// 更新数据
watch(
  () => props,
  async () => {
    if (!props.data || props.data.length === 0) {
      return;
    }
    const data = _.cloneDeep<Array<TransactionGeoChartItem>>(props.data).sort(
      (a, b) => {
        return b.value - a.value;
      }
    );
    const maxValue = data[data.length - 1].value;
    const minValue = data[0].value;
    await nextTick();
    setOptions(
      {
        title: {
          text: `广西各地区采购规模(${props.year})`,
          left: "center",
          textStyle: {
            fontSize: 28,
          }
        },
        visualMap: {
          type: "continuous",
          text: [`${formatAmount(minValue)}`, `${formatAmount(maxValue)}`],
          showLabel: true,
          seriesIndex: [0],
          min: minValue,
          max: maxValue,
          // inRange: {
          //   color: ["#edfbfb", "#b7d6f3", "#40a9ed", "#3598c1", "#215096"],
          // },
          calculable: true,
          inRange: {
            color: [
              "#ffffff",
              "#E0DAFF",
              "#ADBFFF",
              "#9CB4FF",
              "#6A9DFF",
              "#3889FF"
            ]
          },
          formatter: function (value) {
            return formatAmount(value as number);
          },
          textStyle: {
            color: "#000",
            fontSize: 15
          },
          left: "right",
          top: "bottom"
        },
        grid: {
          left: "5%",
          right: "5%",
          bottom: "5%",
          containLabel: true
        },
        legend: [
          {
            name: "成交量占比",
            orient: "vertical",
            left: "left",
            top: "bottom",
            textStyle: {
              fontSize: 15
            }
          }
        ],
        tooltip: {
          trigger: "item",
          valueFormatter(value, dataIndex) {
            return formatAmount(value as number);
          }
        },
        series: [
          // 地图
          {
            name: "成交量",
            type: "map",
            roam: true,
            map: "Guangxi",
            layoutCenter: ["70%", "50%"],
            layoutSize: "70%",
            label: {
              show: true,
              fontSize: 14
            },
            zoom: 1.5,
            emphasis: {
              label: {
                formatter: function (params) {
                  return `${params.name}: ${formatAmount(params.value as number)}`;
                }
              },
              itemStyle: {
                areaColor: "#FAF04C",
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowOffsetY: 6,
                shadowColor: 'rgb(0, 0, 0, 0.25)',
              },
            },
            data: data
          },
          // 饼图
          {
            name: "成交量占比",
            type: "pie",
            radius: ["30%", "65%"],
            z: 20,
            data: data,
            center: ["30%", "50%"],
            label: {
              show: true,
              fontSize: 16,
              formatter: "{b}: {d}%"
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgb(0, 0, 0, 0.25)',
                shadowOffsetX: 0,
                shadowOffsetY: 6,
              },
            }
          }
        ]
      },
      {
        name: "mouseover",
        callback: event => {
          console.log(event);
          if (event.seriesType == "map") {
            getInstance().dispatchAction({
              type: "highlight",
              name: event.name
            });
          } else if (event.seriesType == "pie") {
            getInstance().dispatchAction({
              type: "highlight",
              name: event.name
            });
          }
        }
      },
      {
        name: 'mouseout',
        callback: event => {
          if (event.seriesType == "map") {
            getInstance().dispatchAction({
              type: "downplay",
              name: event.name
            });
          } else if (event.seriesType == "pie") {
            getInstance().dispatchAction({
              type: "downplay",
              name: event.name
            });
          }
        },
      }
    );
  },
  {
    immediate: true,
    deep: true
  }
);
</script>

<template>
  <div ref="geoChartRef" style="width: 100%; height: 100%" />
</template>

<style scoped lang="css"></style>
