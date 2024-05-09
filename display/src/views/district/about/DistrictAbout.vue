<script setup lang="ts">
import DistrictGrowthCharts from "@/views/district/about/DistrictGrowthCharts.vue";
import {
  DistrictTransactionGrowthItem,
  fetchAllCitiesTransactionGrowth
} from "@/api/transaction";
import { message } from "@/utils/message";
import { onMounted, Ref, ref } from "vue";

defineOptions({
  name: "DistrictAbout"
});
const loading = ref(false);
const chartData: Ref<DistrictTransactionGrowthItem[]> = ref();
const fetchGrowthData = () => {
  loading.value = true;
  fetchAllCitiesTransactionGrowth()
    .then(res => {
      console.log("fetchGrowthData", res);
      if (res.code == 200) {
        chartData.value = res.data;
      } else {
        message("网络出错！请重试", { type: "error" });
      }
    })
    .catch(err => {
      console.log("fetchGrowthData-catch", err);
      message("网络出错！请重试", { type: "error" });
    })
    .finally(() => {
      loading.value = false;
    });
};

onMounted(() => {
  fetchGrowthData();
});
</script>

<template>
  <el-row class="w-full h-full" v-loading="loading">
    <el-col :span="24" class="h-full">
      <DistrictGrowthCharts :data="chartData" />
    </el-col>
  </el-row>
</template>

<style scoped lang="css">
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
  background-color: #fff;
}
</style>
