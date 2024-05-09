<script setup lang="ts">
import GeoCharts from "@/views/district/city/GeoCharts.vue";

defineOptions({
  name: "DistrictYuLin"
});


</script>

<template>
  <div class="chart-container w-full h-full">
    <GeoCharts :name="'yu_lin'" :district-code="450900" :district-name="'玉林市'"/>
  </div>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
