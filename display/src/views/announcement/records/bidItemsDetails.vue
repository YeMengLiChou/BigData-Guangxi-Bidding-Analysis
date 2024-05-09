<script setup lang="ts">


import { BidItem } from "@/api/types";
import { BiddingAnnouncementType, emptyData, noData } from "@/views/announcement/records/utils";

defineOptions({
  name: "BidItemsDetails"
});

const props = defineProps({
  bidItems: {
    type: Object as PropType<Array<BidItem>>,
    require: true,
  },
  announcementType: {
    type: Number,
    require: true,
  }
})
</script>

<template>
  <el-descriptions  border :column="5" v-for="(item, index) in bidItems" title="标项信息">
    <el-descriptions-item label="序号" width="100">
      {{ index + 1 }}
    </el-descriptions-item>
      <el-descriptions-item label="标项名称">
        <el-text truncated>
          {{ emptyData(item.name) }}
        </el-text>
      </el-descriptions-item>
      <el-descriptions-item label="预算">
      {{ noData(item.budget) }}
      </el-descriptions-item>

      <template v-if="item.is_win">

        <el-descriptions-item label="成交金额" v-if="item.is_win">
            {{ noData(item.amount) }}
        </el-descriptions-item>

        <el-descriptions-item label="供应商">
          {{ noData(item.supplier) }}
        </el-descriptions-item>
        <el-descriptions-item label="标项结果">
          <el-tag type="success">中标</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="供应商地址">
          {{ noData(item.supplier_address) }}
        </el-descriptions-item>

      </template>
      <template v-else-if="announcementType == BiddingAnnouncementType.termination">
        <el-descriptions-item label="标项结果">
          <el-tag type="danger">终止</el-tag>
        </el-descriptions-item>
      </template>
    <template v-else-if="announcementType == BiddingAnnouncementType.failure">
      <el-descriptions-item label="标项结果">
        <el-tag type="danger">废标</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="废标理由">
        {{ emptyData(item.reason) }}
      </el-descriptions-item>
    </template>



  </el-descriptions>
</template>

<style scoped lang="scss">

</style>
