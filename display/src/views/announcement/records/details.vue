<script setup lang="ts">
import {
  BiddingAnnouncementType,
  BiddingAnnouncementVO,
  formatTimestamp,
  joinStrings,
  noData,
  emptyData
} from "@/views/announcement/records/utils";
import { onMounted } from "vue";
import ReCol from "@/components/ReCol";
import BidItemsDetails from "@/views/announcement/records/bidItemsDetails.vue";

defineOptions({
  name: "AnnouncementDetails"
});

const props = defineProps({
  announcement: {
    type: Object as PropType<BiddingAnnouncementVO>,
    required: true
  }
});


onMounted(() => {
  console.log(props.announcement);
});
</script>

<template>
  <el-row>
    <re-col>
      <!-- 成交公告信息 -->
      <el-descriptions :column="2" border>
        <!--   公共属性   -->
        <template>
          <el-descriptions-item>
            <template #label>
              <div class="cell-item">采购人</div>
            </template>
            {{ noData(announcement.purchaser) }}
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label>
              <div class="cell-item">采购代理机构</div>
            </template>
            {{ noData(announcement.purchasingAgency) }}
          </el-descriptions-item>
          <el-descriptions-item label="采购方式">
            {{ noData(announcement.procurementMethod) }}
          </el-descriptions-item>
          <el-descriptions-item label="采购代表">
            {{
              emptyData(joinStrings(",", announcement.purchaseRepresentatives))
            }}
          </el-descriptions-item>
          <el-descriptions-item label="评审专家">
            {{ emptyData(joinStrings(",", announcement.reviewExperts)) }}
          </el-descriptions-item>
          <el-descriptions-item label="采购种类">
            {{ emptyData(announcement.catalog) }}
          </el-descriptions-item>
          <el-descriptions-item label="总预算">
            {{
              announcement.totalBudget <= 0
                ? "暂无数据"
                : announcement.totalBudget
            }}
          </el-descriptions-item>
        </template>

        <template v-if="announcement.type == BiddingAnnouncementType.success">
          <el-descriptions-item label="开标时间">
            {{ formatTimestamp(announcement.bidOpeningTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="总成交金额">
            {{ noData(announcement.totalAmount) }}
          </el-descriptions-item>
        </template>

        <template
          v-if="announcement.type == BiddingAnnouncementType.termination"
        >
          <el-descriptions-item label="终止原因">
            {{ announcement.terminationReason }}
          </el-descriptions-item>
        </template>
      </el-descriptions>
      <BidItemsDetails :bid-items="announcement.bidItems" :announcement-type="announcement.type"/>
    </re-col>
  </el-row>
</template>

<style scoped lang="css">
:deep(.el-descriptions) {
  margin: 24px 32px;
}
</style>
