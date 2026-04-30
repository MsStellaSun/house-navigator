/**
 * 上海新房数据模型定义
 */

export enum District {
  Pudong = '浦东新区',
  Xuhui = '徐汇区',
  Jingan = '静安区',
  Huangpu = '黄浦区',
  Changning = '长宁区',
  Putuo = '普陀区',
  Hongkou = '虹口区',
  Yangpu = '杨浦区',
  Minhang = '闵行区',
  Baoshan = '宝山区',
  Jiading = '嘉定区',
  Jinshan = '金山区',
  Songjiang = '松江区',
  Qingpu = '青浦区',
  Fengxian = '奉贤区',
  Chongming = '崇明区',
}

export enum SalesStatus {
  OnSale = '在售',
  PreSale = '待售',
  SoldOut = '售罄',
}

export interface UnitType {
  name: string; // 如：3室2厅2卫
  area: number; // 面积 (平米)
  priceLabel?: string; // 参考总价
  image?: string; // 户型图
}

export interface NewHouse {
  id: string;
  name: string; // 楼盘名称
  district: District; // 行政区
  address: string; // 详细地址
  averagePrice: number; // 均价 (元/平米)
  totalPriceRange: [number, number]; // 总价范围 (万元)
  developer: string; // 开发商
  salesStatus: SalesStatus;
  launchDate: string; // 发售时间
  restrictionRules: string; // 限售规则 (如：5年限售，积分入围等)
  schoolInfo: string; // 相关学区/教育配套
  tags: string[]; // 标签 (如：地铁房, 滨江)
  unitTypes: UnitType[];
  coverImage: string;
  description: string;
  sourceUrl?: string;
  permitNumber?: string;
}
