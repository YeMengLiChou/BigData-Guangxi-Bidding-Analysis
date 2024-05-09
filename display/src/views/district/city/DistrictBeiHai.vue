<script setup lang="ts">
import GeoCharts from "@/views/district/city/GeoCharts.vue";

defineOptions({
  name: "DistrictLiuZhou"
});


</script>

<template>
  <div class="chart-container w-full h-full">
    <GeoCharts :name="'bei_hai'" :district-code="450500" :district-name="'北海市'"/>
  </div>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
