<script setup lang="ts">
import GeoCharts from "@/views/district/city/GeoCharts.vue";

defineOptions({
  name: "DistrictLaiBin"
});


</script>

<template>
  <div class="chart-container w-full h-full">
    <GeoCharts :name="'lai_bin'" :district-code="451300" :district-name="'来宾市'"/>
  </div>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
