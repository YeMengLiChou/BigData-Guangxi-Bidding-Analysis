<script setup lang="ts">
import { useDark } from "@pureadmin/utils";
import Segmented, { type OptionsType } from "@/components/ReSegmented";
import { computed, ref } from "vue";
import ProcurementRoundChart from "@/views/home/tabs/procurement/ProcurementPieChart.vue";
import {
  ProcurementMethodItem,
  ProcurementMethodYearData
} from "@/api/procurement";
import { PieChartData } from "@/views/home/utils/types";
import _ from 'lodash';
import ProcurementPieChart from "@/views/home/tabs/procurement/ProcurementPieChart.vue";
import { ProcurementMethodChartData, transformToPieChartData } from "@/views/home/tabs/procurement/utils";

defineOptions({
  name: "ProcurementMethod"
});

const props = defineProps({
  data: {
    type: Array as PropType<Array<ProcurementMethodYearData>>,
    required: true,
    default: () => {}
  }
});

// 兼容Dark主题
const { isDark } = useDark();

// 2022、2023、2024
const segmentYearOptions: Array<OptionsType> = [
  { label: "2022年" }, // 0
  { label: "2023年" }, // 1
  { label: "2024年" }, // 2
  { label: "总计" } // 3
];

const curYear = ref(2);



const totalChartData = computed<Array<ProcurementMethodChartData>>(() => {
  if (!props.data) {
    return [];
  }
  // 深拷贝，否则会造成递归
  const data: Array<ProcurementMethodYearData> = _.cloneDeep(props.data);
  return transformToPieChartData(data);
});
</script>

<template>
  <div class="chart-container">
    <div class="flex justify-between">
      <span class="text-md font-medium"></span>
      <div>
        <Segmented v-model="curYear" :options="segmentYearOptions" />
      </div>
    </div>
    <div class="chart-bar">
      <ProcurementPieChart
        :count-data="totalChartData[curYear]?.count"
        :transaction-data="totalChartData[curYear]?.transaction"
        :year="segmentYearOptions[curYear].label as string"
      />
    </div>
  </div>
</template>

<style scoped lang="css">
.chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.chart-bar {
  width: 100% !important;
  flex-grow: 1;
}
</style>
