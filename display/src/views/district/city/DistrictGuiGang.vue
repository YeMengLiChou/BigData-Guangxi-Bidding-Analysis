<script setup lang="ts">
import GeoCharts from "@/views/district/city/GeoCharts.vue";

defineOptions({
  name: "DistrictGuiGang"
});


</script>

<template>
  <div class="chart-container w-full h-full">
    <GeoCharts :name="'gui_gang'" :district-code="450800" :district-name="'贵港市'"/>
  </div>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
