import React from 'react';
import { Database, AlertCircle, TrendingUp, Target, Package, BarChart3, Info, Zap, CheckCircle } from 'lucide-react';
import Plot from 'react-plotly.js';

const PrimaryDataTab = ({ uploadData, processedData, charts, safetyStockData }) => {
    if (!uploadData) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <Database size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">Data Stream Required</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Please upload your dataset to initialize the analysis engine.</p>
            </div>
        );
    }

    if (!processedData) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <Zap size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">Engine Idle</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Navigate to the <b>Analysis</b> tab and process your data to activate this view.</p>
            </div>
        );
    }

    // Merge stats with safety stock if available
    const displayStats = (charts?.sku_stats || []).slice(0, 50).map(sku => {
        const ssInfo = safetyStockData?.find(r => r.sku_id === sku.key);
        return {
            ...sku,
            safety_stock: ssInfo?.safety_stock,
            reorder_point: ssInfo?.reorder_point
        };
    });

    return (
        <div className="animate-fade-in space-y-8 p-4 md:p-8">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-8">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-blue-600 font-black text-xs uppercase tracking-widest mb-1">
                        <Database size={14} /> Master Data Repository
                    </div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Primary Inventory Intel</h2>
                    <p className="text-slate-500 font-medium">Consolidated view of historical performance and computed planning targets.</p>
                </div>
                {safetyStockData && safetyStockData.length > 0 && (
                    <div className="flex items-center gap-3">
                        <div className="px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">Avg ROP Target</div>
                            <div className="text-xl font-black text-slate-800 flex items-center gap-2">
                                <Target size={18} className="text-purple-500" />
                                {(safetyStockData.reduce((a, b) => a + (b.reorder_point || 0), 0) / safetyStockData.length).toFixed(1)}
                            </div>
                        </div>
                        <div className="px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">Avg SS Target</div>
                            <div className="text-xl font-black text-slate-800 flex items-center gap-2">
                                <Package size={18} className="text-emerald-500" />
                                {(safetyStockData.reduce((a, b) => a + (b.safety_stock || 0), 0) / safetyStockData.length).toFixed(1)}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="space-y-8">
                {/* Supply Chain Insights - Full Width Stacked */}
                <div className="premium-card p-8">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="bg-slate-900 p-2.5 rounded-2xl text-white">
                            <Zap size={24} />
                        </div>
                        <h3 className="text-xl font-black text-slate-800 tracking-tight">Supply Chain Insights</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="p-6 rounded-[1.5rem] bg-rose-50/50 border border-rose-100 relative overflow-hidden group">
                            <div className="relative z-10">
                                <div className="text-[10px] font-black text-rose-500 uppercase tracking-widest mb-1 flex items-center gap-1.5">
                                    <AlertCircle size={12} /> Critical Risk Path
                                </div>
                                <div className="text-3xl font-black text-rose-900 mb-2">
                                    {charts?.sku_stats?.filter(s => s.cv_demand > 1.5).length || 0}
                                </div>
                                <div className="text-xs font-bold text-rose-700 leading-tight">High Volatility (CV {'\u003e'} 1.5) items that require strategic safety buffers.</div>
                            </div>
                            <div className="absolute -right-4 -bottom-4 text-rose-100 transition-transform group-hover:-rotate-12">
                                <TrendingUp size={80} strokeWidth={4} />
                            </div>
                        </div>

                        <div className="p-6 rounded-[1.5rem] bg-amber-50/50 border border-amber-100 relative overflow-hidden group">
                            <div className="relative z-10">
                                <div className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-1 flex items-center gap-1.5">
                                    <Package size={12} /> Low Velocity Cache
                                </div>
                                <div className="text-3xl font-black text-amber-900 mb-2">
                                    {charts?.sku_stats?.filter(s => s.avg_daily_demand < 1).length || 0}
                                </div>
                                <div className="text-xs font-bold text-amber-700 leading-tight">Intermittent Demand items with sporadic sales cycles.</div>
                            </div>
                            <div className="absolute -right-4 -bottom-4 text-amber-100 transition-transform group-hover:-rotate-12">
                                <Database size={80} strokeWidth={4} />
                            </div>
                        </div>

                        <div className="p-6 rounded-[1.5rem] bg-emerald-50/50 border border-emerald-100 relative overflow-hidden group">
                            <div className="relative z-10">
                                <div className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-1 flex items-center gap-1.5">
                                    <Target size={12} /> Stable Flow Assets
                                </div>
                                <div className="text-3xl font-black text-emerald-900 mb-2">
                                    {charts?.sku_stats?.filter(s => s.cv_demand < 0.5).length || 0}
                                </div>
                                <div className="text-xs font-bold text-emerald-700 leading-tight">Highly predictable patterns suitable for just-in-time replenishment.</div>
                            </div>
                            <div className="absolute -right-4 -bottom-4 text-emerald-100 transition-transform group-hover:-rotate-12">
                                <CheckCircle size={80} strokeWidth={4} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Offtake Velocity Trends - Full Width Stacked */}
                <div className="premium-card p-8">
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-3">
                            <div className="bg-blue-50 p-2.5 rounded-2xl text-blue-600">
                                <TrendingUp size={24} />
                            </div>
                            <h3 className="text-xl font-black text-slate-800 tracking-tight">Offtake Velocity Trends</h3>
                        </div>
                        <div className="text-[10px] font-bold bg-slate-100 text-slate-500 px-3 py-1 rounded-full uppercase tracking-tighter shadow-inner">Top Performer Analysis</div>
                    </div>

                    {charts?.offtake_trends ? (
                        <div className="w-full h-[450px] animate-fade-in">
                            <Plot
                                data={JSON.parse(charts.offtake_trends).data}
                                layout={{
                                    ...JSON.parse(charts.offtake_trends).layout,
                                    autosize: true, height: 450,
                                    margin: { l: 80, r: 40, t: 20, b: 80 },
                                    title: null,
                                    plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
                                    font: { family: 'Outfit, sans-serif' },
                                    xaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true },
                                    yaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true },
                                    legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }
                                }}
                                useResizeHandler={true}
                                style={{ width: '100%', height: '100%' }}
                                config={{ displayModeBar: false }}
                            />
                        </div>
                    ) : (
                        <div className="bg-slate-50 rounded-[1.5rem] p-20 text-center border-2 border-dashed border-slate-100">
                            <div className="inline-block p-4 bg-white rounded-full shadow-sm mb-4">
                                <BarChart3 size={32} className="text-slate-200" />
                            </div>
                            <p className="text-slate-400 font-bold italic">Visualization stream not detected. Re-run analysis.</p>
                        </div>
                    )}
                </div>

                {/* Full Width SKU Analytics Table */}
                <div className="premium-card overflow-hidden">
                    <div className="p-8 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50/30">
                        <div className="flex items-center gap-3">
                            <div className="bg-white p-2.5 rounded-2xl shadow-sm text-slate-700 border border-slate-100">
                                <BarChart3 size={20} />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-slate-800 tracking-tight">Primary Data Log</h3>
                                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">MASTER STATISTICAL LEDGER (TOP 50 ITEMS)</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] font-black text-slate-400">
                            <span className="w-2 h-2 rounded-full bg-blue-500"></span> Computed Targets Enabled
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                            <thead className="bg-white border-b border-slate-200">
                                <tr>
                                    <th className="sticky left-0 bg-white px-8 py-5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest border-r border-slate-100 z-20">SKU ID</th>
                                    <th className="px-6 py-5 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">Avg Daily Offtake</th>
                                    <th className="px-6 py-5 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">CV (Volatility %)</th>
                                    <th className="px-6 py-5 text-center text-[10px] font-black text-blue-600 bg-blue-50/50 uppercase tracking-widest font-black">Safety Stock</th>
                                    <th className="px-6 py-5 text-center text-[10px] font-black text-purple-600 bg-purple-50/50 uppercase tracking-widest font-black">Reorder Point (ROP)</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 bg-white">
                                {displayStats.map((sku, i) => (
                                    <tr key={i} className="hover:bg-slate-50 animate-fade-in group" style={{ animationDelay: `${i * 0.02}s` }}>
                                        <td className="sticky left-0 bg-white group-hover:bg-slate-50 px-8 py-4 whitespace-nowrap text-sm font-black text-slate-700 border-r border-slate-100 z-10 flex items-center gap-3">
                                            <div className="w-1.5 h-1.5 rounded-full bg-blue-100"></div> {sku.key}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right font-bold text-slate-600">{sku.avg_daily_demand?.toFixed(2)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right">
                                            <span className={`px-2 py-1 rounded-lg text-[10px] font-black ${sku.cv_demand > 1 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-600'}`}>
                                                {(sku.cv_demand * 100).toFixed(1)}%
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center bg-blue-50/20">
                                            <span className="text-blue-700 font-black text-base drop-shadow-sm">
                                                {sku.safety_stock ? Math.round(sku.safety_stock).toLocaleString() : '-'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center bg-purple-50/20">
                                            <span className="text-purple-700 font-black text-base drop-shadow-sm">
                                                {sku.reorder_point ? Math.round(sku.reorder_point).toLocaleString() : '-'}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PrimaryDataTab;
