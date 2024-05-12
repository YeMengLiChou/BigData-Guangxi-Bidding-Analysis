<script setup lang="ts">
import { BiddingDistrictStats } from "@/api/bidding";
import Segmented, { OptionsType } from "@/components/ReSegmented";
import ProcurementPieChart from "@/views/home/tabs/procurement/ProcurementPieChart.vue";
import { computed, ref } from "vue";
import { PieChartData } from "@/views/home/utils/types";
import DistrictLevelPieChart from "@/views/home/tabs/district-level/DistrictLevelPieChart.vue";
import { DistrictLevelPieChartData, transformToPieChartData } from "@/views/home/tabs/district-level/utils";

defineOptions({
  name: "DistrictLevel"
});

const props = defineProps({
  data: {
    type: Object as PropType<BiddingDistrictStats>,
    required: true,
    default: () => {},
  }
});

// 2022、2023、2024
// const segmentYearOptions: Array<OptionsType> = [
//   { label: "2022年" }, // 0
//   { label: "2023年" }, // 1
//   { label: "2024年" }, // 2
//   { label: "总计" } // 3
// ];


const totalChartData = computed<Array<DistrictLevelPieChartData>>(() => {
  if (!props.data) {
    return  [];
  }
  return transformToPieChartData(props.data as BiddingDistrictStats);
});


</script>

<template>
  <div class="chart-container">

    <div class="chart-bar">
      <DistrictLevelPieChart :data="totalChartData"/>
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
