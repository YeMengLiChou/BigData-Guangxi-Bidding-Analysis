<script setup lang="ts">
import GeoCharts from "@/views/district/city/GeoCharts.vue";

defineOptions({
  name: "DistrictFangChengGang"
});


</script>

<template>
  <div class="chart-container w-full h-full">
    <GeoCharts :name="'fang_cheng_gang'" :district-code="450600" :district-name="'防城港市'"/>
  </div>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
