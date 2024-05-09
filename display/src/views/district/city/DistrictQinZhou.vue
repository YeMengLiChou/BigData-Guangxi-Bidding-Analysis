<script setup lang="ts">
import GeoCharts from "@/views/district/city/GeoCharts.vue";

defineOptions({
  name: "DistrictQinZhou"
});


</script>

<template>
  <div class="chart-container w-full h-full">
    <GeoCharts :name="'qin_zhou'" :district-code="450700" :district-name="'钦州市'"/>
  </div>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
