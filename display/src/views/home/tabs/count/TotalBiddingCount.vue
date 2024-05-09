<script setup lang="ts">
import { BiddingCountItem } from "@/api/bidding";
import TotalBiddingCountBarChart from "@/views/home/tabs/count/TotalBiddingCountBarChart.vue";
import { computed } from "vue";

defineOptions({
  name: "TotalBiddingCount"
});

const props = defineProps({
  data: {
    type: Array as PropType<Array<BiddingCountItem>>,
    require: true,
    default: () => [],
  }
});

const chartData = computed(() => {
  if (!props.data || props.data.length == 0) {
    return null;
  }
  return props.data;
});


</script>

<template>
<TotalBiddingCountBarChart :data="chartData"/>
</template>

<style scoped lang="scss">

</style>
