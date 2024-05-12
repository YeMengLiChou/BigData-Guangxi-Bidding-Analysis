<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { ChartLine } from "./components";
import ReCol from "@/components/ReCol";
import { ReNormalCountTo } from "@/components/ReCountTo";
import { fetchBaseInfo, fetchScaleData, ScaleData } from "@/api/base";
import { BaseInfoVO } from "@/views/home/utils/types";
import { transformBaseInfoVO } from "@/views/home/utils/fetch";
import { message } from "@/utils/message";
import { useDark } from "@pureadmin/utils";
import {
  fetchProcurementMethodData,
  ProcurementMethodYearData
} from "@/api/procurement";
import {
  BiddingCountItem,
  BiddingDistrictStats,
  fetchBiddingCount,
  fetchBiddingDistrictStats
} from "@/api/bidding";
import ProcurementMethod from "@/views/home/tabs/procurement/ProcurementMethod.vue";
import PurchaseScale from "@/views/home/tabs/scale/PurchaseScale.vue";
import DistrictLevel from "@/views/home/tabs/district-level/DistrictLevel.vue";
import DistrictScale from "@/views/home/tabs/district-scale/DistrictScale.vue";
import {
  fetchTransactionVolumeWithAllDistrict,
  TransactionVolumeDistrictYear
} from "@/api/transaction";
import TotalBiddingCount from "@/views/home/tabs/count/TotalBiddingCount.vue";

defineOptions({
  name: "HomeIndex"
});

const { isDark } = useDark();

const statsData = ref<Array<BaseInfoVO>>([]);
const statsLoading = ref(false);

// 获取上方的基本信息
const fetchBaseInfoVO = () => {
  statsLoading.value = true;
  fetchBaseInfo()
    .then(res => {
      console.log("fetchBaseInfo", res);
      if (res.code == 200) {
        statsData.value = transformBaseInfoVO(res.data);
      } else {
        // TODO: raise err
        message("获取失败！", {
          type: "error"
        });
      }
      statsLoading.value = false;
    })
    .catch(err => {
      console.log("fetchBaseInfoVO error", err);
      message("网络错误，请稍后重试！", {
        type: "error"
      });
      statsLoading.value = false;
    });
};

// 双向绑定 el-tabs 的当前激活的 tabs-pane 迷你改成
const tabsActiveName = ref("");

onMounted(() => {
  // 设置为 0，触发 watch 的监听，进而获取图标数据
  tabsActiveName.value = "0";
  fetchBaseInfoVO();
});

// 图表1：采购规模的数据
const scaleChatsData = ref<ScaleData>(null);
// 获取数据
const fetchScaleChartData = () => {
  fetchScaleData()
    .then(res => {
      console.log("scaleChartData", res);
      if (res.code == 200) {
        scaleChatsData.value = res.data;
      } else {
        message("获取图表数据失败", { type: "error" });
      }
    })
    .catch(err => {
      console.log("fetchScaleChartData", err);
      message("网络错误！请重试!", { type: "error" });
    });
};

// 图表2：采购方式对比
const procurementMethodChartData = ref<ProcurementMethodYearData[]>();
const fetchProcurementMethodChartData = () => {
  fetchProcurementMethodData()
    .then(res => {
      console.log("procurementChartData", res);
      if (res.code == 200) {
        procurementMethodChartData.value = res.data;
      } else {
        message("获取图表数据失败", { type: "error" });
      }
    })
    .catch(err => {
      console.log("procurementChartData", err);
      message("网络错误！请重试!", { type: "error" });
    });
};

// 地区政府
const biddingDistrictChartData = ref<BiddingDistrictStats>(null);
const fetchBiddingDistrictChartData = () => {
  fetchBiddingDistrictStats()
    .then(res => {
      console.log("fetchBiddingDistrictStats", res);
      if (res.code == 200) {
        biddingDistrictChartData.value = res.data;
      } else {
        message("获取图表数据失败", { type: "error" });
      }
    })
    .catch(err => {
      console.log("fetchBiddingDistrictStats", err);
      message("网络错误！请重试!", { type: "error" });
    });
};

const recentBiddingAnnouncementData = ref<BiddingCountItem[]>(null);
const fetchRecentBiddingAnnouncementData = () => {
  fetchBiddingCount()
    .then(res => {
      console.log("fetchRecentBiddingAnnouncementData", res);
      if (res.code == 200) {
        recentBiddingAnnouncementData.value = res.data;
      } else {
        message("获取图表数据失败", { type: "error" });
      }
    })
    .catch(err => {
      console.log("fetchRecentBiddingAnnouncementData", err);
      message("网络错误！请重试!", { type: "error" });
    });
};

const districtTransactionVolumeData =
  ref<Array<TransactionVolumeDistrictYear>>(null);
const fetchDistrictTransactionVolumeData = () => {
  fetchTransactionVolumeWithAllDistrict()
    .then(res => {
      console.log("fetchDistrictTransactionVolumeData", res);
      if (res.code == 200) {
        districtTransactionVolumeData.value = res.data;
      } else {
        message("获取图表数据失败", { type: "error" });
      }
    })
    .catch(err => {
      console.log("fetchBiddingDistrictStats", err);
      message("网络错误！请重试!", { type: "error" });
    });
};

watch(tabsActiveName, (value, _) => {
  if (value === "0") {
    if (!scaleChatsData.value) {
      fetchScaleChartData();
    }
  } else if (value === "1") {
    if (!procurementMethodChartData.value) {
      fetchProcurementMethodChartData();
    }
  } else if (value === "2") {
    if (!biddingDistrictChartData.value) {
      fetchBiddingDistrictChartData();
    }
  } else if (value === "3") {
    if (!recentBiddingAnnouncementData.value) {
      fetchRecentBiddingAnnouncementData();
    }
  } else if (value === "4") {
    if (!districtTransactionVolumeData.value) {
      fetchDistrictTransactionVolumeData();
    }
  }
});
</script>

<template>
  <el-row :gutter="24" justify="space-around">
    <!--  上面部分的简概  -->
    <re-col
      v-loading="statsLoading"
      class="mb-[18px]"
      v-for="(item, index) in statsData"
      :key="index"
      :value="6"
      :md="12"
      :sm="12"
      :xs="24"
      :initial="{ opacity: 0, y: 100 }"
      :enter="{ opacity: 1, y: 0, transition: { delay: 80 * (index + 1) } }"
    >
      <el-card>
        <div class="flex justify-between">
          <el-text class="text-md font-medium" size="large">
            {{ item.name }}
          </el-text>
          <div
            class="w-8 h-8 flex justify-center items-center rounded-md"
            :style="{
              backgroundColor: isDark ? 'transparent' : item.bgColor
            }"
          >
            <IconifyIconOffline
              :icon="item.icon"
              :color="item.color"
              width="18"
            />
          </div>
        </div>
        <div class="flex justify-between items-start mt-3">
          <div class="w-1/2">
            <ReNormalCountTo
              :duration="item.duration"
              :fontSize="'1.6em'"
              :startVal="0"
              :endVal="item.value"
            />
          </div>
          <ChartLine
            v-if="item.data.length > 1"
            class="!w-1/2"
            :color="item.color"
            :data="item.data"
          />
        </div>
      </el-card>
    </re-col>

    <!--  图表数据  -->
    <re-col
      class="mb-[18px] tab-charts-container"
      :value="24"
      :xs="24"
      :initial="{
        opacity: 0,
        y: 100
      }"
      :enter="{
        opacity: 1,
        y: 0,
        transition: {
          delay: 400
        }
      }"
    >
      <el-card class="bar-card" shadow="never">
        <span
          class="text-md font-medium mb-4 ml-2 block"
          style="font-size: large"
          >分析概览</span
        >
        <el-tabs type="card" v-model="tabsActiveName" selectable="false">
          <el-tab-pane label="采购总规模" name="0">
            <PurchaseScale
              v-if="tabsActiveName == '0' && scaleChatsData"
              :data="scaleChatsData"
            />
          </el-tab-pane>
          <el-tab-pane label="采购方式对比统计" name="1">
            <ProcurementMethod
              v-if="tabsActiveName == '1' && procurementMethodChartData"
              :data="procurementMethodChartData"
            />
          </el-tab-pane>
          <el-tab-pane label="政府级次分布图" name="2">
            <DistrictLevel
              v-if="tabsActiveName == '2' && biddingDistrictChartData"
              :data="biddingDistrictChartData"
            />
          </el-tab-pane>
          <el-tab-pane label="近年度公告数对比" name="3">
            <TotalBiddingCount
              v-if="tabsActiveName == '3'"
              :data="recentBiddingAnnouncementData"
            />
          </el-tab-pane>
          <el-tab-pane label="地区采购规模对比" name="4">
            <DistrictScale
              v-if="tabsActiveName == '4'"
              :data="districtTransactionVolumeData"
            />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </re-col>
  </el-row>
</template>

<style lang="css" scoped>
/* 主要页面设置外边距 */
.main-content {
  margin: 20px 20px 0 !important;
}

.tab-charts-container {
  height: 70vh;
}

:deep(.el-card) {
  height: 100%;
  --el-card-border-color: none;

  .el-card__body {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
}

:deep(.el-tabs) {
  width: 100%;
  display: flex;
  flex-direction: column;
  flex-grow: 1;

  /* 将 tabs 的 content 部分撑满 */

  .el-tabs__content {
    flex-grow: 1;
  }

  /* 将 tab-pane 的内容撑满 */

  .el-tab-pane {
    height: calc(100%);
  }
}
</style>
