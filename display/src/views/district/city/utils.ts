import guang_xi_map from '@/assets/map/map.json';
import bai_se_map from '@/assets/map/bai_se.json';
import bei_hai_map from '@/assets/map/bei_hai.json';
import cong_zuo_map from '@/assets/map/cong_zuo.json';
import fang_cheng_gang_map from '@/assets/map/fang_cheng_gang.json';
import gui_gang_map from '@/assets/map/gui_gang.json';
import gui_lin_map from '@/assets/map/gui_lin.json';
import he_chi_map from '@/assets/map/he_chi.json';
import he_zhou_map from '@/assets/map/he_zhou.json';
import lai_bin_map from '@/assets/map/lai_bin.json';
import liu_zhou_map from '@/assets/map/liu_zhou.json';
import nan_ning_map from '@/assets/map/nan_ning.json';
import qin_zhou_map from '@/assets/map/qin_zhou.json';
import wu_zhou_map from '@/assets/map/wu_zhou.json';
import yu_lin_map from '@/assets/map/yu_lin.json';

export type GeoChartItem = {
  name: string,
  value: number;
};



export const mapJson = new Map<number, object>([
  [450000, guang_xi_map], // 广西
  [450100, nan_ning_map], // 南宁
  [450200, liu_zhou_map], // 柳州
  [450300, gui_lin_map], // 桂林
  [450400, wu_zhou_map], // 梧州
  [450500, bei_hai_map], // 北海
  [450600, fang_cheng_gang_map], // 防城港
  [450700, qin_zhou_map], // 钦州
  [450800, gui_gang_map], // 贵港
  [450900, yu_lin_map], // 玉林
  [451000, bai_se_map], // 白色
  [451100, he_zhou_map], // 贺州
  [451200, he_chi_map], // 河池
  [451300, lai_bin_map], // 来宾
  [451400, cong_zuo_map], // 崇左
]);
