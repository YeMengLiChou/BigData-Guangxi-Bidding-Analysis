<script setup lang="ts">
import { computed, ref } from "vue";
import { ScaleData } from "@/api/base";
import Segmented, { type OptionsType } from "@/components/ReSegmented";
import { transformToChartData } from "@/views/home/tabs/scale/utils";
import ScaleLineChart from "@/views/home/tabs/scale/ScaleLineChart.vue";
import { LineChartData } from "@/views/home/utils/types";
import TotalScaleBarChart from "@/views/home/tabs/scale/TotalScaleBarChart.vue";

defineOptions({
  name: "PurchaseScale"
});

const props = defineProps({
  data: {
    type: Object as PropType<ScaleData>,
    require: true,
    default: () => {}
  }
});

// 2022、2023、2024
const segmentYearOptions: Array<OptionsType> = [
  { label: "2022年" },
  { label: "2023年" },
  { label: "2024年" }
];
// 日、月、季度
const segmentTimespanOptions: Array<OptionsType> = [
  { label: "日" }, // 0
  { label: "月" }, // 1
  { label: "季度" } // 2
];
// 2024
const curYear = ref(2);
// 月
const curTimespan = ref(1);

// 所有数据
const allChartData = computed<Map<number, LineChartData[]>>(() => {
  if (!props.data) {
    return null;
  }
  return transformToChartData(props.data);
});
// 当前的数据
const curChartData = computed<LineChartData>(() => {
  if (!allChartData.value) {
    return null;
  }
  return allChartData.value.get(curYear.value)[curTimespan.value];
});


// 总金额数据
const totalChartData = computed<LineChartData>(() => {
  if (!allChartData.value) {
    return null;
  }
  const totalResult = new Map<number, number>();
  // 将每年的所有月数据相加起来
  for (const [key, value] of allChartData.value) {
    let total = 0;
    const monthsData = value[1].yAxisData
    for (const i of monthsData) {
      total += i;
    }
    totalResult.set(key + 2022, total);
  }
  const result = {
    xAxisData: [],
    yAxisData: []
  } as LineChartData;
  for (let i = 2022; i <= 2024; i ++) {
    result.xAxisData.push(`${i}年`);
    result.yAxisData.push(totalResult.get(i));
  }
  console.log(result)
  return result
})

</script>

<template>
  <div class="container">
    <el-row class="row" :gutter="4">
      <el-col :span="8" class="flex">
        <TotalScaleBarChart class="h-full w-9/12" :data="totalChartData"/>
      </el-col>
      <el-col :span="16">
          <ScaleLineChart
            class="h-full w-full"
            :data="curChartData"
            :year="segmentYearOptions[curYear].label as string"
            :timespan="segmentTimespanOptions[curTimespan].label as string"
          />
        <div class="right-top-option" style="">
          <div>
            <div>
              <Segmented v-model="curYear" :options="segmentYearOptions" />
            </div>
            <div class="flex justify-end mt-4">
              <Segmented
                v-model="curTimespan"
                :options="segmentTimespanOptions"
              />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="css" scoped>
.container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.row {
  width: 100%;
  flex-grow: 1;
}

/*分割线*/
:deep(.el-divider) {
  height: 100%;
}

.right-top-option {
  position: absolute;
  right: 0;
  top: 0;
}
</style>
