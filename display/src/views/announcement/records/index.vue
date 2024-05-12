<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import ReCol from "@/components/ReCol";
import { getBiddingAnnouncements } from "@/api/bidding";
import { ElMessage } from "element-plus";
import { useDark, useResizeObserver } from "@pureadmin/utils";
import {
  BiddingAnnouncementType,
  BiddingAnnouncementVO,
  mapBiddingAnnouncement,
  getAnnouncementTypeName,
  getAnnouncementTagType, formatTimestamp
} from "@/views/announcement/records/utils";
import AnnouncementDetails from "./details.vue";

defineOptions({
  name: "AnnouncementRecords"
});

const { isDark } = useDark();

// 加载状态
const loading = ref(false);
// 当前页面变化
const currentPageNo = ref(1);
const totalCount = ref(0);
const currentPageSize = ref(25);
const currentData = ref<Array<BiddingAnnouncementVO>>([]);
const paginationDisabled = computed(
  () =>
    loading.value ||
    (currentData.value !== undefined && currentData.value.length === 0)
);

// 获取数据
function getDataByPagination() {
  loading.value = true;
  // 根据当前的分页获取到数据
  getBiddingAnnouncements({
    pageSize: currentPageSize.value,
    pageNo: currentPageNo.value,
    districtCode: 0,
    year: 0,
    month: 0,
    day: 0,
    quarter: 0
  })
    .then(res => {
      console.log(res.data);
      // 更新数据
      currentData.value = mapBiddingAnnouncement(res.data.data);
      // 更新数据总数
      totalCount.value = res.data.total;
      loading.value = false;
    })
    .catch(err => {
      loading.value = false;
      ElMessage.error(err);
    });
}

// 总容器以及分页元素，计算表的大小
const container = ref<HTMLDivElement | null>(null);
const pagination = ref<HTMLDivElement | null>(null);
const tableMaxHeight = ref(0);

// 挂载时获取数据
onMounted(() => {
  // 计算表格最大高度
  useResizeObserver(container, entries => {
    const { height } = entries[0].contentRect;
    tableMaxHeight.value = height - (pagination.value?.clientHeight || 80) - 20;
  });

  // 初始获取数据
  getDataByPagination();
});

// 表格日期列的格式化回调
const dateformat = (row: BiddingAnnouncementVO): string => {
  return formatTimestamp(row.scrapeTimestamp);
};


// 返回表头的格式
const tableHeaderStyle = computed(() => {
  if (isDark.value) {
    return {}
  }
  return {
    'background-color': '#fefefe',
    'color': 'black'
  };
});

// =============== 分页逻辑 =====================

// 当分页大小发生改变时调用
const handleSizeChange = (_: number) => {
  // 将页码调整到1
  currentPageNo.value = 1;
  getDataByPagination();
};
// 页码发生变化
const handleCurrentPageNoChange = (_: number) => {
  getDataByPagination();
};


</script>

<template>
  <el-row ref="container">
    <re-col :span="24" class="flex-col container">
      <el-table
        :data="currentData"
        style="width: 100%"
        :max-height="tableMaxHeight"
        highlight-current-row
        border
        row-key="id"
        empty-text="/"
        :header-cell-style="tableHeaderStyle"
      >
        <el-table-column
          fixed
          prop="scrapeTimestamp"
          label="日期"
          sortable
          align="center"
          :formatter="dateformat"
          width="150"
        />
        <el-table-column
          prop="districtName"
          label="地区"
          align="center"
          with="100"
        />
        <el-table-column prop="title" label="公告标题" align="center" />
        <el-table-column
          prop="type"
          label="公告类型"
          align="center"
          width="100"
        >
          <template #default="scope">
            <el-popover
              :effect="'light'"
              trigger="hover"
              placement="top"
              width="auto"
            >
              <template
                v-if="scope.row.type == BiddingAnnouncementType.success"
                #default
              >
                <div>
                  预算金额:
                  {{
                    scope.row.totalBudget > 0
                      ? scope.row.totalBudget
                      : "未能解析/不存在"
                  }}
                </div>
                <div>成交金额: {{ scope.row.totalAmount }}元</div>
              </template>
              <template
                v-else-if="scope.row.type == BiddingAnnouncementType.failure"
                #default
              >
                <div>废标理由请看详情</div>
              </template>
              <template v-else #default>
                <div>终止理由: {{ scope.row.terminationReason }}</div>
              </template>
              <template #reference>
                <el-tag
                  :type="getAnnouncementTagType(scope.row.type)"
                  size="large"
                >
                  {{ getAnnouncementTypeName(scope.row.type) }}
                </el-tag>
              </template>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="projectName" label="项目名称" align="center" />
        <el-table-column prop="projectCode" label="项目编号" align="center" />
        <el-table-column prop="author" label="发布者" align="center" />
        <el-table-column label="详情" type="expand" align="center" width="80">
          <template #default="props">
            <AnnouncementDetails :announcement="props.row"/>
          </template>
        </el-table-column>
      </el-table>
      <!-- 分页 -->
      <div ref="pagination" class="pagination-block">
        <el-pagination
          v-model:current-page="currentPageNo"
          v-model:page-size="currentPageSize"
          :pager-count="5"
          :loading="loading"
          :page-sizes="[10, 25, 50, 100]"
          :disabled="paginationDisabled"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
          @size-change="handleSizeChange"
          @current-change="handleCurrentPageNoChange"
        />
      </div>
    </re-col>
  </el-row>
</template>

<style lang="css" scoped>
.main-content {
  margin: 20px 20px 0 !important;
  height: 95%;
}

.container {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.pagination-block {
  display: flex;
  justify-content: flex-end;
  padding: 24px 8px;
  background-color: transparent;
}
</style>
