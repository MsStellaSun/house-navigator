import { useState, useMemo, useEffect, useCallback } from 'react';
import { Search, MapPin, Filter, Home, Info, ChevronRight, GraduationCap, ShieldCheck, Calendar, Building2, LayoutGrid, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { SHANGHAI_HOUSES } from './data';
import { District, NewHouse, SalesStatus } from './types';

export default function App() {
  const [houses, setHouses] = useState<NewHouse[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState<District | 'All'>('All');
  const [selectedStatus, setSelectedStatus] = useState<SalesStatus | 'All'>('All');
  const [sortBy, setSortBy] = useState<'default' | 'price-asc' | 'price-desc'>('default');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedHouse, setSelectedHouse] = useState<NewHouse | null>(null);

  // Fetch data on mount
  useEffect(() => {
    fetchHouses();
  }, []);

  const fetchHouses = async () => {
    // 改为直接读取静态 JSON 文件
    try {
      const res = await fetch('./scraped_data.json');
      const data = await res.json();
      if (data.houses && data.houses.length > 0) {
        setHouses(data.houses);
        setLastUpdated(data.lastUpdated);
        if (!selectedHouse) setSelectedHouse(data.houses[0]);
      } else {
        setHouses(SHANGHAI_HOUSES);
      }
    } catch (error) {
      console.error("无法读取爬取数据，切换至备用数据:", error);
      setHouses(SHANGHAI_HOUSES);
    } finally {
      setLoading(false);
    }
  };

  const triggerRescrape = useCallback(async () => {
    if (syncing) return;
    setSyncing(true);
    try {
      // 调用 GitHub Actions workflow_dispatch 手动触发爬取
      const response = await fetch('https://api.github.com/repos/MsStellaSun/house-navigator/actions/workflows/main.yml/dispatches', {
        method: 'POST',
        headers: {
          'Accept': 'application/vnd.github+json',
          'Authorization': `Bearer ${import.meta.env.VITE_GITHUB_TOKEN || ''}`,
          'X-GitHub-Api-Version': '2022-11-28',
        },
        body: JSON.stringify({ ref: 'main' }),
      });
      if (response.status === 204 || response.status === 200) {
        alert('已触发重新爬取！GitHub Actions 运行中，约1-2分钟后自动更新。');
      } else {
        alert('触发失败，请检查网络或重新登录GitHub。');
      }
    } catch {
      // 即使API失败也不做处理，保留原数据
      console.log('触发重新爬取失败，保持现有数据不变。');
    } finally {
      setSyncing(false);
    }
  }, [syncing]);

  const filteredHouses = useMemo(() => {
    if (!houses || houses.length === 0) return [];
    let result = houses.filter(house => {
      const matchDistrict = selectedDistrict === 'All' || house.district === selectedDistrict;
      const matchStatus = selectedStatus === 'All' || house.salesStatus === selectedStatus;
      const matchSearch = house.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          house.address.toLowerCase().includes(searchQuery.toLowerCase());
      return matchDistrict && matchStatus && matchSearch;
    });

    if (sortBy === 'price-asc') {
      result = [...result].sort((a, b) => a.averagePrice - b.averagePrice);
    } else if (sortBy === 'price-desc') {
      result = [...result].sort((a, b) => b.averagePrice - a.averagePrice);
    }

    return result;
  }, [houses, selectedDistrict, selectedStatus, sortBy, searchQuery]);

  if (loading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-white">
        <div className="w-12 h-12 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-slate-400 text-sm font-medium animate-pulse uppercase tracking-widest">上海新房导航正在加载数据...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden font-sans">
      {/* 顶部标题栏 - Header */}
      <header className="h-16 px-8 border-b border-slate-200 bg-white flex items-center justify-between shrink-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center text-white font-bold text-xs">沪</div>
          <h1 className="text-lg font-bold tracking-tight text-slate-900">
            上海新房大数据导航 
            <span className="hidden sm:inline text-[10px] font-normal text-slate-400 ml-2 uppercase tracking-widest">Shanghai Real Estate Navigator</span>
          </h1>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center bg-slate-100 rounded-full px-4 py-1.5 border border-slate-200/50">
            <Search className="w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="搜索楼盘或板块..." 
              className="bg-transparent border-none text-sm focus:ring-0 w-48 ml-2 placeholder:text-slate-400 outline-none"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">2024.Q2 Release</div>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden relative">
        {/* 左侧筛选栏 - Sidebar */}
        <aside className="hidden lg:flex w-56 border-r border-slate-200 bg-white p-6 flex-col gap-4 overflow-y-auto">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4 px-1">行政区划 · DISTRICTS</div>
            <div className="space-y-1">
              <button 
                onClick={() => setSelectedDistrict('All')}
                className={`sidebar-btn ${selectedDistrict === 'All' ? 'bg-slate-900 text-white font-medium' : 'text-slate-600 hover:bg-slate-100'}`}
              >
                全部区域
              </button>
              {Object.values(District).map(district => (
                <button 
                  key={district}
                  onClick={() => setSelectedDistrict(district)}
                  className={`sidebar-btn flex justify-between items-center ${selectedDistrict === district ? 'bg-slate-900 text-white font-medium' : 'text-slate-600 hover:bg-slate-100'}`}
                >
                  {district}
                  <span className={`text-[9px] ${selectedDistrict === district ? 'opacity-60' : 'text-slate-400'}`}>
                    {SHANGHAI_HOUSES.filter(h => h.district === district).length}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="pt-6 border-t border-slate-100">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4 px-1">销售状态 · STATUS</div>
            <div className="space-y-1">
              <button 
                onClick={() => setSelectedStatus('All')}
                className={`sidebar-btn ${selectedStatus === 'All' ? 'bg-slate-900 text-white font-medium' : 'text-slate-600 hover:bg-slate-100'}`}
              >
                全部状态
              </button>
              {Object.values(SalesStatus).map(status => (
                <button 
                  key={status}
                  onClick={() => setSelectedStatus(status)}
                  className={`sidebar-btn flex justify-between items-center ${selectedStatus === status ? 'bg-slate-900 text-white font-medium' : 'text-slate-600 hover:bg-slate-100'}`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-6 border-t border-slate-100">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4 px-1">数据同步 · SYNC</div>
            <button
              onClick={triggerRescrape}
              disabled={syncing}
              className={`w-full flex items-center justify-center gap-2 py-2 px-3 border rounded-md text-xs font-medium transition-all ${
                syncing
                  ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
                  : 'bg-slate-50 border border-slate-200 text-slate-600 hover:bg-slate-100 hover:border-slate-300'
              }`}
            >
              {syncing ? (
                <>
                  <div className="w-3 h-3 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                  <span>触发中...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-500" />
                  <span>手动触发重新爬取</span>
                </>
              )}
            </button>
            <p className="text-[9px] text-slate-400 mt-2 px-1 text-center leading-relaxed">
              数据源: fangdi.com.cn<br/>
              * 爬取失败时保留原数据
            </p>
          </div>
        </aside>

        {/* 中间楼盘列表 - Project List */}
        <section className="w-full md:w-[420px] border-r border-slate-200 flex flex-col bg-white overflow-hidden shrink-0">
          <div className="p-5 border-b border-slate-100 bg-white shrink-0 flex justify-between items-end">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                {selectedDistrict === 'All' ? '当前查询楼盘' : selectedDistrict} 
                <span className="text-slate-400 ml-1">({filteredHouses.length})</span>
              </h2>
            </div>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Clock className="w-3 h-3" /> 最新更新
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
            <AnimatePresence mode="popLayout">
              {filteredHouses.length > 0 ? (
                filteredHouses.map((house) => (
                  <motion.div 
                    layout
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    key={house.id}
                    onClick={() => setSelectedHouse(house)}
                    className={`group p-4 rounded-xl border transition-all cursor-pointer bg-white ${
                      selectedHouse?.id === house.id 
                      ? 'border-slate-900 ring-1 ring-slate-900 shadow-md' 
                      : 'border-slate-200 hover:border-slate-400 shadow-sm'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="font-bold text-slate-900 group-hover:text-black">{house.name}</h3>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        house.salesStatus === SalesStatus.OnSale ? 'bg-slate-900 text-white' : 
                        house.salesStatus === SalesStatus.PreSale ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'
                      }`}>
                        {house.salesStatus}
                      </span>
                    </div>

                    <div className="flex gap-4">
                      <div className="w-20 h-20 bg-slate-100 rounded-lg overflow-hidden shrink-0">
                        <img src={house.coverImage} className="w-full h-full object-cover grayscale-[0.2] group-hover:grayscale-0 transition-all" />
                      </div>
                      <div className="flex-1">
                        <div className="text-xl font-black text-slate-900">
                          {house.averagePrice.toLocaleString()} 
                          <span className="text-[10px] font-normal text-slate-400 ml-1">元/㎡</span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {house.district} · {house.address.split('区')[1]?.substring(0, 8) || house.address.substring(0, 8)}
                        </div>
                        <div className="flex gap-1 mt-3">
                          {house.tags.slice(0, 2).map(tag => (
                            <span key={tag} className="text-[9px] px-1.5 py-0.5 bg-slate-50 text-slate-500 border border-slate-100 font-medium">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20">
                  <LayoutGrid className="w-12 h-12 mb-4 opacity-20" />
                  <p className="text-sm">未找到符合条件的楼盘</p>
                </div>
              )}
            </AnimatePresence>
          </div>
        </section>

        {/* 右侧详情面板 - Detail Panel (Desktop: Sidebar, Mobile: Absolute Overlay) */}
        <section className={`flex-1 bg-white flex flex-col overflow-hidden transition-all duration-300 fixed md:relative inset-0 z-30 md:z-auto md:flex ${selectedHouse ? 'translate-x-0' : 'translate-x-full md:translate-x-0'}`}>
          {selectedHouse ? (
            <AnimatePresence mode="wait">
              <motion.div 
                key={selectedHouse.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex-1 flex flex-col overflow-hidden"
              >
                {/* 移动端返回按钮 */}
                <div className="md:hidden absolute top-4 left-4 z-40">
                  <button 
                    onClick={() => setSelectedHouse(null)}
                    className="bg-white/80 backdrop-blur-sm p-2 rounded-full shadow-lg border border-slate-200"
                  >
                    <ChevronRight className="w-5 h-5 rotate-180" />
                  </button>
                </div>

                {/* Banner Area */}
                <div className="h-56 bg-slate-100 relative shrink-0 overflow-hidden">
                  <img src={selectedHouse.coverImage} className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-transparent to-transparent"></div>
                  <div className="absolute bottom-6 left-8 text-white">
                    <div className="text-[10px] uppercase tracking-[0.3em] opacity-80 mb-2">{selectedHouse.district} · 管理处公告</div>
                    <h2 className="text-3xl font-bold tracking-tight">{selectedHouse.name}</h2>
                  </div>
                  <div className="absolute top-6 right-8 hidden sm:block">
                    <div className="bg-white/20 backdrop-blur-md px-4 py-2 border border-white/20 rounded-lg text-white">
                      <div className="text-[10px] text-white/60 mb-1">更新于</div>
                      <div className="text-xs font-mono font-bold tracking-wider">2024-04-30</div>
                    </div>
                  </div>
                </div>
                
                {/* Content Area */}
                <div className="flex-1 p-6 md:p-10 grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-12 overflow-y-auto shadow-inner">
                  <div className="space-y-10">
                    <section>
                      <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-5 pb-2 border-b border-slate-100 flex items-center gap-2">
                        <Info className="w-3.5 h-3.5" /> 楼盘概况 · OVERVIEW
                      </h4>
                      <div className="space-y-4">
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-slate-400">开发商</span>
                          <span className="font-semibold text-slate-900">{selectedHouse.developer}</span>
                        </div>
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-slate-400">参考均价</span>
                          <span className="font-bold text-slate-900 text-lg">{selectedHouse.averagePrice.toLocaleString()} <span className="text-[10px] font-normal">元/㎡</span></span>
                        </div>
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-slate-400">发售时间</span>
                          <span className="font-semibold text-slate-900">{selectedHouse.launchDate}</span>
                        </div>
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-slate-400">项目地址</span>
                          <span className="font-semibold text-slate-900 text-right max-w-[200px]">{selectedHouse.address}</span>
                        </div>
                        {selectedHouse.permitNumber && (
                          <div className="flex justify-between text-sm py-1 pt-3 border-t border-slate-50">
                            <span className="text-slate-400">预售证号</span>
                            <span className="font-mono text-[11px] font-bold text-slate-900">{selectedHouse.permitNumber}</span>
                          </div>
                        )}
                      </div>
                    </section>

                    <section>
                      <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-5 pb-2 border-b border-slate-100 flex items-center gap-2">
                        <Home className="w-3.5 h-3.5" /> 主力房型 · UNIT TYPES
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-1 gap-3">
                        {selectedHouse.unitTypes.map((unit, i) => (
                          <div key={i} className="group p-4 border border-slate-100 rounded-xl bg-slate-50 flex justify-between items-center hover:border-slate-300 transition-colors">
                            <div>
                              <div className="text-sm font-bold text-slate-900">{unit.name}</div>
                              <div className="text-[11px] text-slate-500 mt-0.5">建面约 {unit.area} ㎡</div>
                            </div>
                            <div className="text-xs font-bold text-slate-900 opacity-60 group-hover:opacity-100 transition-opacity text-right">
                              {unit.priceLabel}
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  </div>

                  <div className="space-y-10">
                    <section>
                      <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-5 pb-2 border-b border-slate-100 flex items-center gap-2">
                        <ShieldCheck className="w-3.5 h-3.5" /> 限售与积分 · REGULATIONS
                      </h4>
                      <div className="bg-amber-50/50 p-5 rounded-2xl border border-amber-100/50">
                        <p className="text-sm text-amber-900/70 leading-relaxed font-medium italic">
                          “{selectedHouse.restrictionRules}”
                        </p>
                      </div>
                    </section>

                    <section>
                      <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-5 pb-2 border-b border-slate-100 flex items-center gap-2">
                        <GraduationCap className="w-3.5 h-3.5" /> 教育匹配 (预估) · EDUCATION
                      </h4>
                      <div className="space-y-4">
                        <div className="flex items-start gap-4 p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                          <div className="w-1.5 h-1.5 rounded-full bg-slate-900 mt-2"></div>
                          <div>
                            <div className="text-sm font-bold text-slate-900">{selectedHouse.schoolInfo.split('（')[0]}</div>
                            <div className="text-[11px] text-slate-400 mt-1">
                              {selectedHouse.schoolInfo.includes('（') ? `（${selectedHouse.schoolInfo.split('（')[1]}` : '*最终以教育局公示为准'}
                            </div>
                          </div>
                        </div>
                      </div>
                    </section>

                    <div className="pt-6 pb-12 md:pb-0 space-y-3">
                      {selectedHouse.sourceUrl && (
                        <a
                          href={selectedHouse.sourceUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="w-full bg-white border border-slate-200 text-slate-600 py-3 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-slate-50 transition-all text-sm"
                        >
                          <Info className="w-4 h-4" />
                          查看平台房源原文
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300">
              <div className="w-24 h-24 border-2 border-slate-100 rounded-full flex items-center justify-center mb-6">
                <LayoutGrid className="w-8 h-8 opacity-20" />
              </div>
              <p className="text-sm tracking-widest font-medium uppercase text-slate-400">选择楼盘查看详细数据</p>
            </div>
          )}
        </section>
      </main>

      
      {/* 底部信息栏 - Footer */}
      <footer className="h-8 bg-white border-t border-slate-200 px-8 flex items-center justify-between shrink-0 z-20">
        <div className="text-[10px] text-slate-400 flex items-center gap-4">
          <span className="flex items-center gap-1 uppercase tracking-widest">
            <Clock className="w-2.5 h-2.5" /> 
            Data Updated: {lastUpdated || 'Initial Data (Static)'}
          </span>
        </div>
        <div className="flex gap-6">
          <a href="#" className="text-[10px] text-slate-400 hover:text-slate-900 flex items-center gap-1 uppercase tracking-widest">Legal Notice</a>
          <a href="#" className="text-[10px] text-slate-400 hover:text-slate-900 flex items-center gap-1 uppercase tracking-widest">Policy Analysis</a>
        </div>
      </footer>
    </div>
  );
}

