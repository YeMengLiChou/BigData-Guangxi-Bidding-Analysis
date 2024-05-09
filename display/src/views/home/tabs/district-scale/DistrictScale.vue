<script setup lang="ts">
import Segmented, { OptionsType } from "@/components/ReSegmented";
import { computed, ref } from "vue";
import DistrictScaleGeoChart from "@/views/home/tabs/district-scale/DistrictScaleGeoChart.vue";
import { TransactionVolumeDistrictYear } from "@/api/transaction";
import { transformToGeoChartData } from "@/views/home/tabs/district-scale/utils";

defineOptions({
  name: 'DistrictScale'
});

const props = defineProps({
  data: {
    type: Array as PropType<Array<TransactionVolumeDistrictYear>>,
    require: true,
    default: () => [],
  }
});

// 2022、2023、2024
const segmentYearOptions: Array<OptionsType> = [
  { label: "2022年" },
  { label: "2023年" },
  { label: "2024年" },
  { label: '总计' }
];

// 2024
const curYear = ref(2);

const allData = computed(() => {
  if (!props.data) {
    return[];
  }
  return transformToGeoChartData(props.data);
})


</script>

<template>
  <div class="chart-container">
    <div class="flex justify-between">
      <span class="text-md font-medium"></span>
      <div class="absolute top-0 right-0 z-50">
          <Segmented v-model="curYear" :options="segmentYearOptions" />
      </div>
    </div>
    <div class="chart-bar">
      <DistrictScaleGeoChart :data="allData[curYear]" :year="segmentYearOptions[curYear].label as string"/>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-bar {
  width: 100%;
  flex-grow: 1;
}
</style>
