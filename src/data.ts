import { District, SalesStatus, NewHouse } from './types';

export const SHANGHAI_HOUSES: NewHouse[] = [
  {
    id: 'h1',
    name: '中环名邸',
    district: District.Pudong,
    address: '浦东新区锦绣路与杨高南路交汇处',
    averagePrice: 105000,
    totalPriceRange: [1200, 2500],
    developer: '上海地产集团',
    salesStatus: SalesStatus.OnSale,
    launchDate: '2024-03-15',
    restrictionRules: '五年限售，积分触发率预计75分以上',
    schoolInfo: '对口建平实验小学（具体以当年公示为准）',
    tags: ['地铁房', '学区房', '高品质'],
    unitTypes: [
      { name: '3室2厅', area: 115, priceLabel: '约1200万' },
      { name: '4室2厅', area: 145, priceLabel: '约1500万' }
    ],
    coverImage: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&q=80&w=1000',
    description: '位于浦东内中环核心位置，配套完善，高端改善型社区。'
  },
  {
    id: 'h2',
    name: '徐汇滨江壹号',
    district: District.Xuhui,
    address: '徐汇区云锦路88号',
    averagePrice: 142000,
    totalPriceRange: [2800, 6000],
    developer: '香港置地',
    salesStatus: SalesStatus.OnSale,
    launchDate: '2024-05-20',
    restrictionRules: '严禁代持，五年限售，首套积分优先级高',
    schoolInfo: '周边配套有上海中学东校区',
    tags: ['一线江景', '豪宅', '艺术西岸'],
    unitTypes: [
      { name: '3室2厅', area: 180, priceLabel: '约2800万' },
      { name: '4室3厅', area: 260, priceLabel: '约4500万' }
    ],
    coverImage: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&q=80&w=1000',
    description: '徐汇滨江地标级资产，坐拥黄浦江一线美景。'
  },
  {
    id: 'h3',
    name: '静安天际',
    district: District.Jingan,
    address: '静安区宝源路与其汇路口',
    averagePrice: 128000,
    totalPriceRange: [1300, 3000],
    developer: '万科集团',
    salesStatus: SalesStatus.PreSale,
    launchDate: '2024-06-10',
    restrictionRules: '参考静安区最新积分政策',
    schoolInfo: '周边教育资源丰富',
    tags: ['内环内', 'TOD项目', '万科物业'],
    unitTypes: [
      { name: '2室2厅', area: 95, priceLabel: '待定' },
      { name: '3室2厅', area: 125, priceLabel: '待定' }
    ],
    coverImage: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=1000',
    description: '静安核心区域罕见TOD住宅，交通极其便利。'
  },
  {
    id: 'h4',
    name: '黄浦新天地里',
    district: District.Huangpu,
    address: '黄浦区复兴路888号',
    averagePrice: 165000,
    totalPriceRange: [3500, 8000],
    developer: '瑞安房地产',
    salesStatus: SalesStatus.OnSale,
    launchDate: '2024-04-01',
    restrictionRules: '严格执行一房一价，五年限售，严控高积分客户。',
    schoolInfo: '对口卢湾一中心小学（名额有限，具体以公示为准）',
    tags: ['市中心', '新天地', '顶级豪宅'],
    unitTypes: [
      { name: '3室2厅', area: 170, priceLabel: '约3500万' },
      { name: '5室3厅', area: 320, priceLabel: '约7500万' }
    ],
    coverImage: 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&q=80&w=1000',
    description: '在上海的心脏，复刻海派弄堂文化与现代奢华的交响。'
  },
  {
    id: 'h5',
    name: '闵行紫竹园',
    district: District.Minhang,
    address: '闵行区紫竹高新区二路',
    averagePrice: 78000,
    totalPriceRange: [600, 1500],
    developer: '紫竹开发',
    salesStatus: SalesStatus.OnSale,
    launchDate: '2024-02-10',
    restrictionRules: '面向园区人才有优先认购权',
    schoolInfo: '对口华师大附属紫竹小学/中学',
    tags: ['学区房', '高新园区', '地铁5号线'],
    unitTypes: [
      { name: '2室1厅', area: 89, priceLabel: '约680万' },
      { name: '3室2厅', area: 118, priceLabel: '约920万' }
    ],
    coverImage: 'https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&q=80&w=1000',
    description: '紧邻紫竹高新区，环境优美，教育资源极其强大。'
  },
  {
    id: 'h6',
    name: '青浦蟠龙里',
    district: District.Qingpu,
    address: '青浦区徐泾镇蟠龙路',
    averagePrice: 62000,
    totalPriceRange: [550, 1200],
    developer: '瑞安房地产',
    salesStatus: SalesStatus.SoldOut,
    launchDate: '2023-11-15',
    restrictionRules: '五年限售，积分竞争激烈（入围分80+）',
    schoolInfo: '周边有青浦平和等国际化教育资源',
    tags: ['大虹桥', '古镇生活', '高积分'],
    unitTypes: [
      { name: '3室2厅', area: 95, priceLabel: '约600万' },
      { name: '4室2厅', area: 130, priceLabel: '约820万' }
    ],
    coverImage: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&q=80&w=1000',
    description: '大虹桥核心区，网红古镇盘，生活氛围极佳。'
  }
];

