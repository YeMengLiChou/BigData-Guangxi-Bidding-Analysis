<script setup lang="ts">
import echarts from "@/plugins/echarts";
import { useTransition } from "@vueuse/core";
import { ChatLineRound, Male } from "@element-plus/icons-vue";
import { ref } from "vue";
import TotalScaleCharts from "./charts/total-scale.vue";
import RecentScaleCharts from './charts/recent-scale.vue';
import ProcurementMethodsCharts from "./charts/procurement-methods.vue";

import {
  ArrowRight,
  CaretBottom,
  CaretTop,
  Warning
} from "@element-plus/icons-vue";

defineOptions({
  name: "Home"
});

// 动态变化，接口返回数据时可以使用
const source = ref(0);
const outputValue = useTransition(source, {
  duration: 1500
});
source.value = 172000;




// 顶部 el-row 中每个 el-col 的宽度
const colSpanSize = ref(5);

// 双向绑定 el-tabs 的当前激活的 tabs-pane 迷你改成
const tabsActiveName = ref("0");

</script>

<template>
  <!-- 上方的统计列表 -->
  <el-row justify="space-evenly">
    <el-col :span="colSpanSize">
      <div class="statistic-card">
        <el-statistic :value="1">
          <template #title>
            <div style="display: inline-flex; align-items: center">
              <el-text>当前数据范围</el-text>
              <el-tooltip
                effect="dark"
                content="数据库中存储的公告数量"
                placement="top"
              >
                <el-icon style="margin-left: 4px" :size="12">
                  <Warning />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-statistic>
        <div class="statistic-footer">
          <div class="footer-item">
            <span>than yesterday</span>
            <span class="green">
              24%
              <el-icon>
                <CaretTop />
              </el-icon>
            </span>
          </div>
        </div>
      </div>
    </el-col>
    <el-col :span="colSpanSize">
      <div class="statistic-card">
        <el-statistic :value="98500">
          <template #title>
            <div style="display: inline-flex; align-items: center">
              <el-text>当前统计总公告数</el-text>
              <el-tooltip
                effect="dark"
                content="数据库中存储的公告数量"
                placement="top"
              >
                <el-icon style="margin-left: 4px" :size="12">
                  <Warning />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-statistic>
        <div class="statistic-footer">
          <div class="footer-item">
            <span>than yesterday</span>
            <span class="green">
              24%
              <el-icon>
                <CaretTop />
              </el-icon>
            </span>
          </div>
        </div>
      </div>
    </el-col>
    <el-col :span="colSpanSize">
      <div class="statistic-card">
        <el-statistic :value="693700">
          <template #title>
            <div style="display: inline-flex; align-items: center">
              <el-text>成交总金额</el-text>
              <el-tooltip
                effect="dark"
                content="当前数据库中成交公告统计的总金额"
                placement="top"
              >
                <el-icon style="margin-left: 4px" :size="12">
                  <Warning />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-statistic>
        <div class="statistic-footer">
          <div class="footer-item">
            <span>month on month</span>
            <span class="red">
              12%
              <el-icon>
                <CaretBottom />
              </el-icon>
            </span>
          </div>
        </div>
      </div>
    </el-col>
    <el-col :span="colSpanSize">
      <div class="statistic-card">
        <el-statistic :value="72000" title="New transactions today">
          <template #title>
            <div style="display: inline-flex; align-items: center">
              成交公告数量
            </div>
          </template>
        </el-statistic>
        <div class="statistic-footer">
          <div class="footer-item">
            <span>than yesterday</span>
            <span class="green">
              16%
              <el-icon>
                <CaretTop />
              </el-icon>
            </span>
          </div>
          <div class="footer-item">
            <el-icon :size="14">
              <ArrowRight />
            </el-icon>
          </div>
        </div>
      </div>
    </el-col>
  </el-row>

  <!-- 图表 -->
  <el-row class="charts-container" justify="space-evenly">
    <el-col :span="22" justify="space-evenly">
      <el-container>
        <el-main>
          <el-tabs type="card" v-model="tabsActiveName" selectable="false">
            <el-tab-pane label="采购总规模" name="0">
              <el-row class="charts-row">
                <el-col :span="12" class="charts-col">
                  <TotalScaleCharts v-if="tabsActiveName === '0'" />
                </el-col>
                <el-col :span="12" class="charts-col">
                  <RecentScaleCharts v-if="tabsActiveName === '0'" />
                </el-col>
              </el-row>
            </el-tab-pane>
            <el-tab-pane label="采购方式对比统计"> 
              <ProcurementMethodsCharts v-if="tabsActiveName === '1'"/>  
            </el-tab-pane>
            <el-tab-pane label="政府级次分布图"> 图表3 </el-tab-pane>
            <el-tab-pane label="近年度公告数对比"> 图表4 </el-tab-pane>
            <el-tab-pane label="地区采购规模对比"> 地图 </el-tab-pane>
          </el-tabs>
        </el-main>
      </el-container>
    </el-col>
  </el-row>
</template>

<style lang="css" scoped>
:global(h2#card-usage ~ .example .example-showcase) {
  background-color: var(--el-fill-color) !important;
}

.el-statistic {
  --el-statistic-content-font-size: 28px;
}

.statistic-card {
  height: 100%;
  padding: 20px;
  border-radius: 4px;
  background-color: var(--el-bg-color-overlay);
}

.statistic-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 16px;
}

.statistic-footer .footer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.statistic-footer .footer-item span:last-child {
  display: inline-flex;
  align-items: center;
  margin-left: 4px;
}

.green {
  color: var(--el-color-success);
}

.red {
  color: var(--el-color-error);
}

.el-row {
  margin-top: 24px;
}

 /* 设置背景以及大小 */
.el-container {
  height: 65vh;
  background-color: var(--el-bg-color-overlay);
  border-radius: 4px;
}


.el-main {
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.el-tabs {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  /* 将 tabs 的 content 部分撑满 */
  :deep .el-tabs__content {
    flex: 1;
    overflow: hidden;
  }
  /* 将 tab-pane 的内容撑满 */
  :deep .el-tab-pane {
    height: calc(100%);
  }
}

/* 一行两个表 */
.charts-row {
  height: calc(100%);
}


.charts-col {
  height: calc(100%);
}
</style>
