<script setup lang="ts">
import GeoCharts from "@/views/district/city/GeoCharts.vue";

defineOptions({
  name: "DistrictNanNing"
});


</script>

<template>
  <div class="chart-container w-full h-full">
    <GeoCharts :name="'nanning'" :district-code="450100" :district-name="'南宁市'"/>
  </div>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
