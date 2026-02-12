import React, { useState, useMemo } from 'react';
import { Database, AlertCircle, TrendingUp, Target, Package, BarChart3, Info, Zap, CheckCircle, Filter, X, ChevronDown, ChevronUp, Send, Activity } from 'lucide-react';
import Plot from 'react-plotly.js';

const PrimaryDataTab = ({ uploadData, processedData, charts, safetyStockData }) => {
    // Alert Filter State
    const [isExporting, setIsExporting] = useState(false);
    const [activeInsightFilter, setActiveInsightFilter] = useState(null); // 'HIGH_VOLATILITY', 'LOW_VELOCITY', 'STABLE_FLOW'

    const handleExportNowcast = async () => {
        if (!uploadData?.filepath) return;
        setIsExporting(true);
        try {
            const response = await fetch('http://20.44.56.229:5050/api/export-to-nowcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath: uploadData.filepath })
            });
            const data = await response.json();
            if (data.success) {
                alert(data.message);
            } else {
                alert('Export failed: ' + data.error);
            }
        } catch (error) {
            console.error('Export error:', error);
            alert('Export error: ' + error.message);
        } finally {
            setIsExporting(false);
        }
    };

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
    const displayStats = (charts?.sku_stats || []).map(sku => {
        const ssInfo = safetyStockData?.find(r => r.sku_id === sku.key);
        return {
            ...sku,
            safety_stock: ssInfo?.safety_stock,
            reorder_point: ssInfo?.reorder_point
        };
    });

    // Pagination State
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 50;

    // Filter Logic
    const [filters, setFilters] = useState({
        chain: 'All',
        category: 'All',
        dtCode: 'All'
    });

    // Reset page on filter change
    React.useEffect(() => {
        setCurrentPage(1);
    }, [filters]);

    const uniqueChains = useMemo(() => {
        if (!displayStats.length) return ['All'];
        const relevant = displayStats.filter(s =>
            (filters.category === 'All' || s.Category === filters.category) &&
            (filters.dtCode === 'All' || s.DT_Code === filters.dtCode)
        );
        return ['All', ...new Set(relevant.map(s => s.Chain || 'Unknown').filter(Boolean))].sort();
    }, [displayStats, filters.category, filters.dtCode]);

    const uniqueCategories = useMemo(() => {
        if (!displayStats.length) return ['All'];
        const relevant = displayStats.filter(s =>
            (filters.chain === 'All' || s.Chain === filters.chain) &&
            (filters.dtCode === 'All' || s.DT_Code === filters.dtCode)
        );
        return ['All', ...new Set(relevant.map(s => s.Category || 'Unknown').filter(Boolean))].sort();
    }, [displayStats, filters.chain, filters.dtCode]);

    const uniqueDtCodes = useMemo(() => {
        if (!displayStats.length) return ['All'];
        const relevant = displayStats.filter(s =>
            (filters.chain === 'All' || s.Chain === filters.chain) &&
            (filters.category === 'All' || s.Category === filters.category)
        );
        return ['All', ...new Set(relevant.map(s => s.DT_Code || 'Unknown').filter(Boolean))].sort();
    }, [displayStats, filters.chain, filters.category]);

    const filteredStats = useMemo(() => {
        return displayStats.filter(sku => {
            return (filters.chain === 'All' || sku.Chain === filters.chain) &&
                (filters.category === 'All' || sku.Category === filters.category) &&
                (filters.dtCode === 'All' || sku.DT_Code === filters.dtCode);
        });
    }, [displayStats, filters]);

    const paginatedStats = useMemo(() => {
        const startIndex = (currentPage - 1) * itemsPerPage;
        return filteredStats.slice(startIndex, startIndex + itemsPerPage);
    }, [filteredStats, currentPage]);

    const totalPages = Math.ceil(filteredStats.length / itemsPerPage);

    const clearFilters = () => setFilters({ chain: 'All', category: 'All', dtCode: 'All' });

    // Filter Chart Data
    const chartData = useMemo(() => {
        if (!charts?.monthly_data || filteredStats.length === 0) return null;

        try {
            // Get top 10 visible keys sorted by total demand
            const topKeys = [...filteredStats]
                .sort((a, b) => b.total_demand - a.total_demand)
                .slice(0, 10)
                .map(s => String(s.key));

            if (topKeys.length === 0) return null;

            // Filter monthly data for these keys
            // Ensure comparison is string-to-string to avoid type mismatches
            const relevantData = charts.monthly_data.filter(d => topKeys.includes(String(d.key)));

            // Group by key
            const traces = {};
            relevantData.forEach(d => {
                const keyStr = String(d.key);
                if (!traces[keyStr]) traces[keyStr] = { x: [], y: [] };
                traces[keyStr].x.push(d.month_start || d.date);
                traces[keyStr].y.push(d.Offtake_Units);
            });

            // Convert to Plotly trace objects
            const data = Object.keys(traces).map(key => ({
                x: traces[key].x,
                y: traces[key].y,
                type: 'scatter',
                mode: 'lines+markers',
                name: key,
                line: { width: 2 },
                marker: { size: 6 }
            }));

            return {
                data,
                layout: {
                    autosize: true, height: 450,
                    margin: { l: 60, r: 20, t: 20, b: 60 },
                    title: null,
                    showlegend: true,
                    legend: { orientation: 'h', y: 1.1 }, // Legend above chart
                    xaxis: { title: 'Date', gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9' },
                    yaxis: { title: 'Offtake Units', gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9' },
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    font: { family: 'Outfit, sans-serif' }
                }
            };
        } catch (e) {
            console.error("Chart generation error", e);
            return null;
        }
    }, [charts, filteredStats]);

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
                {(filteredStats.length > 0) && (
                    <div className="flex items-center gap-3">
                        <div className="px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">Avg ROP Target</div>
                            <div className="text-xl font-black text-slate-800 flex items-center gap-2">
                                <Target size={18} className="text-purple-500" />
                                {(filteredStats.reduce((a, b) => a + (b.reorder_point || 0), 0) / filteredStats.length).toFixed(1)}
                            </div>
                        </div>
                        <div className="px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">Avg SS Target</div>
                            <div className="text-xl font-black text-slate-800 flex items-center gap-2">
                                <Package size={18} className="text-emerald-500" />
                                {(filteredStats.reduce((a, b) => a + (b.safety_stock || 0), 0) / filteredStats.length).toFixed(1)}
                            </div>
                        </div>
                    </div>
                )}
            </div>





            <div className="space-y-8">
                {/* Supply Chain Insights - Full Width Stacked */}
                <div className="premium-card p-8 bg-white border border-slate-100 shadow-sm rounded-[2.5rem]">
                    <div className="flex items-center justify-between mb-10">
                        <div className="flex items-center gap-4">
                            <div className="bg-slate-900 p-3 rounded-2xl text-white shadow-lg shadow-slate-200">
                                <Zap size={24} strokeWidth={2.5} />
                            </div>
                            <h3 className="text-2xl font-black text-slate-800 tracking-tight">Supply Chain Insights</h3>
                        </div>

                        <button
                            onClick={handleExportNowcast}
                            disabled={isExporting}
                            className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-sm transition-all shadow-lg active:scale-95 ${isExporting
                                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                                : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-blue-200 shadow-blue-100'
                                }`}
                        >
                            {isExporting ? (
                                <Activity size={18} className="animate-spin" />
                            ) : (
                                <Send size={18} />
                            )}
                            {isExporting ? 'Syncing Alerts...' : 'Export to Tower'}
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Critical Risk Path */}
                        <div
                            onClick={() => setActiveInsightFilter(activeInsightFilter === 'HIGH_VOLATILITY' ? null : 'HIGH_VOLATILITY')}
                            className={`p-8 rounded-[2rem] border-2 relative overflow-hidden group transition-all cursor-pointer ${activeInsightFilter === 'HIGH_VOLATILITY'
                                ? 'bg-rose-50 border-rose-500 shadow-xl scale-[1.02]'
                                : 'bg-rose-50 border-rose-100 hover:shadow-lg hover:shadow-rose-100 hover:-translate-y-1'
                                }`}
                        >
                            <div className="relative z-10 flex flex-col h-full justify-between">
                                <div>
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <AlertCircle size={16} className="text-rose-500" strokeWidth={3} />
                                            <span className="text-[11px] font-black text-rose-500 uppercase tracking-widest">Critical Risk Path</span>
                                        </div>
                                        {activeInsightFilter === 'HIGH_VOLATILITY' ? <ChevronUp className="text-rose-500" /> : <ChevronDown className="text-rose-300" />}
                                    </div>
                                    <div className="text-5xl font-black text-rose-900 mb-4 tracking-tight">
                                        {filteredStats.filter(s => (s.cv_demand || 0) > 1.5).length || 0}
                                    </div>
                                </div>
                                <div className="text-sm font-bold text-rose-700 leading-snug">
                                    High Volatility (CV &gt; 1.5) items that require strategic safety buffers.
                                </div>
                            </div>
                            <div className="absolute -right-6 -bottom-6 text-rose-100 opacity-80 group-hover:scale-110 transition-transform duration-500">
                                <TrendingUp size={140} strokeWidth={3} />
                            </div>
                        </div>

                        {/* Low Velocity Cache */}
                        <div
                            onClick={() => setActiveInsightFilter(activeInsightFilter === 'LOW_VELOCITY' ? null : 'LOW_VELOCITY')}
                            className={`p-8 rounded-[2rem] border-2 relative overflow-hidden group transition-all cursor-pointer ${activeInsightFilter === 'LOW_VELOCITY'
                                ? 'bg-amber-50 border-amber-500 shadow-xl scale-[1.02]'
                                : 'bg-amber-50 border-amber-100 hover:shadow-lg hover:shadow-amber-100 hover:-translate-y-1'
                                }`}
                        >
                            <div className="relative z-10 flex flex-col h-full justify-between">
                                <div>
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <Package size={16} className="text-amber-500" strokeWidth={3} />
                                            <span className="text-[11px] font-black text-amber-500 uppercase tracking-widest">Low Velocity Cache</span>
                                        </div>
                                        {activeInsightFilter === 'LOW_VELOCITY' ? <ChevronUp className="text-amber-500" /> : <ChevronDown className="text-amber-300" />}
                                    </div>
                                    <div className="text-5xl font-black text-amber-900 mb-4 tracking-tight">
                                        {filteredStats.filter(s => (s.avg_daily_demand || 0) < 1).length || 0}
                                    </div>
                                </div>
                                <div className="text-sm font-bold text-amber-700 leading-snug">
                                    Intermittent Demand items with sporadic sales cycles.
                                </div>
                            </div>
                            <div className="absolute -right-6 -bottom-6 text-amber-100 opacity-80 group-hover:scale-110 transition-transform duration-500">
                                <Database size={140} strokeWidth={3} />
                            </div>
                        </div>

                        {/* Stable Flow Assets */}
                        <div
                            onClick={() => setActiveInsightFilter(activeInsightFilter === 'STABLE_FLOW' ? null : 'STABLE_FLOW')}
                            className={`p-8 rounded-[2rem] border-2 relative overflow-hidden group transition-all cursor-pointer ${activeInsightFilter === 'STABLE_FLOW'
                                ? 'bg-emerald-50 border-emerald-500 shadow-xl scale-[1.02]'
                                : 'bg-emerald-50 border-emerald-100 hover:shadow-lg hover:shadow-emerald-100 hover:-translate-y-1'
                                }`}
                        >
                            <div className="relative z-10 flex flex-col h-full justify-between">
                                <div>
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <Target size={16} className="text-emerald-500" strokeWidth={3} />
                                            <span className="text-[11px] font-black text-emerald-500 uppercase tracking-widest">Stable Flow Assets</span>
                                        </div>
                                        {activeInsightFilter === 'STABLE_FLOW' ? <ChevronUp className="text-emerald-500" /> : <ChevronDown className="text-emerald-300" />}
                                    </div>
                                    <div className="text-5xl font-black text-emerald-900 mb-4 tracking-tight">
                                        {filteredStats.filter(s => (s.cv_demand || 1) < 0.5).length || 0}
                                    </div>
                                </div>
                                <div className="text-sm font-bold text-emerald-700 leading-snug">
                                    Highly predictable patterns suitable for just-in-time replenishment.
                                </div>
                            </div>
                            <div className="absolute -right-6 -bottom-6 text-emerald-100 opacity-80 group-hover:scale-110 transition-transform duration-500">
                                <CheckCircle size={140} strokeWidth={3} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Detailed Insight Table - Toggled by Insight Cards */}
                {activeInsightFilter && (
                    <div className="premium-card p-0 bg-white border border-slate-200 shadow-sm overflow-hidden animate-fade-in-up mb-8">
                        <div className={`px-6 py-4 border-b border-slate-100 flex items-center justify-between ${activeInsightFilter === 'HIGH_VOLATILITY' ? 'bg-rose-50/50' :
                            activeInsightFilter === 'LOW_VELOCITY' ? 'bg-amber-50/50' : 'bg-emerald-50/50'
                            }`}>
                            <h3 className={`font-black text-lg ${activeInsightFilter === 'HIGH_VOLATILITY' ? 'text-rose-700' :
                                activeInsightFilter === 'LOW_VELOCITY' ? 'text-amber-700' : 'text-emerald-700'
                                }`}>
                                {activeInsightFilter === 'HIGH_VOLATILITY' ? 'High Risk / Volatile Items' :
                                    activeInsightFilter === 'LOW_VELOCITY' ? 'Slow Moving Inventory' : 'Stable & Predictable Assets'}
                            </h3>
                            <div className="text-xs font-bold text-slate-400">
                                Filtering by {activeInsightFilter.replace('_', ' ')}
                            </div>
                        </div>

                        <div className="overflow-x-auto max-h-[500px] overflow-y-auto relative">
                            <table className="min-w-full text-sm text-left">
                                <thead className="bg-slate-50 border-b border-slate-100 text-xs uppercase font-black text-slate-500 sticky top-0 z-10 shadow-sm">
                                    <tr>
                                        <th className="px-6 py-4 bg-slate-50">Analysis Date</th>
                                        <th className="px-6 py-4 bg-slate-50">SKU Details</th>
                                        <th className="px-6 py-4 text-center bg-slate-50">Velocity Metrics</th>
                                        <th className="px-6 py-4 text-center bg-slate-50">Stock Coverage</th>
                                        <th className="px-6 py-4 bg-slate-50">Strategic Action Plan</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {filteredStats
                                        .filter(item => {
                                            if (activeInsightFilter === 'HIGH_VOLATILITY') return (item.cv_demand || 0) > 1.5;
                                            if (activeInsightFilter === 'LOW_VELOCITY') return (item.avg_daily_demand || 0) < 1;
                                            if (activeInsightFilter === 'STABLE_FLOW') return (item.cv_demand || 1) < 0.5;
                                            return false;
                                        })
                                        .map((item, i) => {
                                            const cv = item.cv_demand || 0;
                                            const demand = item.avg_daily_demand || 0;
                                            const stock = item.current_stock || 0;

                                            // Calculate Days of Supply
                                            const daysOfSupply = demand > 0 ? (stock / demand) : 999;

                                            let profileColor = 'slate';
                                            let profileText = 'Standard';
                                            let actionText = 'Monitor Performance';
                                            let actionColor = 'slate';

                                            if (activeInsightFilter === 'HIGH_VOLATILITY') {
                                                profileColor = 'rose';
                                                profileText = 'High Variance';
                                                if (daysOfSupply < 7) {
                                                    actionText = 'URGENT: Stockout Risk. Expedite replenishment.';
                                                    actionColor = 'rose';
                                                } else {
                                                    actionText = 'Review safety stock buffers. Forecast erratic.';
                                                    actionColor = 'orange';
                                                }
                                            } else if (activeInsightFilter === 'LOW_VELOCITY') {
                                                profileColor = 'amber';
                                                profileText = 'Slow Mover';
                                                if (daysOfSupply > 60) {
                                                    actionText = 'Overstocked. Consider liquidation promo.';
                                                    actionColor = 'rose';
                                                } else {
                                                    actionText = 'Monitor for obsolescence. Reduce reorder qty.';
                                                    actionColor = 'amber';
                                                }
                                            } else if (activeInsightFilter === 'STABLE_FLOW') {
                                                profileColor = 'emerald';
                                                profileText = 'Stable Demand';
                                                if (daysOfSupply < 14) {
                                                    actionText = 'Replenish soon to maintain service level.';
                                                    actionColor = 'emerald';
                                                } else {
                                                    actionText = 'Ideal candidate for automated reordering.';
                                                    actionColor = 'blue';
                                                }
                                            }

                                            return (
                                                <tr key={i} className="hover:bg-slate-50 transition-colors">
                                                    <td className="px-6 py-4 font-medium text-slate-500 whitespace-nowrap">
                                                        {new Date().toLocaleDateString()}
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="font-bold text-slate-700">{item.key}</div>
                                                        <div className="text-[10px] uppercase font-bold text-slate-400">{item.Category || 'Uncategorized'}</div>
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        <div className="font-black text-slate-700">{demand.toFixed(2)} <span className="text-[10px] font-medium text-slate-400">units/day</span></div>
                                                        <div className="text-[10px] font-bold text-slate-400">~{(demand * 7).toFixed(0)} / weekly</div>
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        <div className={`font-black ${daysOfSupply < 7 ? 'text-rose-600' : daysOfSupply > 60 ? 'text-amber-600' : 'text-slate-700'}`}>
                                                            {daysOfSupply > 365 ? '> 1 Year' : `${daysOfSupply.toFixed(0)} Days`}
                                                        </div>
                                                        <div className="text-[10px] font-bold text-slate-400">Current Coverage</div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className={`flex items-start gap-2 text-xs font-bold ${actionColor === 'rose' ? 'text-rose-600' :
                                                            actionColor === 'amber' || actionColor === 'orange' ? 'text-amber-600' :
                                                                actionColor === 'emerald' ? 'text-emerald-600' : 'text-blue-600'
                                                            }`}>
                                                            <Info size={14} className="mt-0.5 shrink-0" />
                                                            {actionText}
                                                        </div>
                                                    </td>
                                                </tr>
                                            );
                                        })}

                                </tbody>
                            </table>
                        </div>
                    </div>
                )}



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

                    {chartData && chartData.data.length > 0 ? (
                        <div className="w-full h-[450px] animate-fade-in">
                            <Plot
                                data={chartData.data}
                                layout={chartData.layout}
                                useResizeHandler={true}
                                style={{ width: '100%', height: '100%' }}
                                config={{ displayModeBar: false }}
                            />
                        </div>
                    ) : (
                        <div className="bg-slate-50 rounded-[1.5rem] p-20 text-center border-2 border-dashed border-slate-100 flex flex-col items-center justify-center">
                            <div className="inline-block p-4 bg-white rounded-full shadow-sm mb-4">
                                <BarChart3 size={32} className="text-slate-200" />
                            </div>
                            <h4 className="text-slate-500 font-bold mb-1">Visualization Unavailable</h4>
                            <p className="text-slate-400 text-sm max-w-md mx-auto">
                                {!charts?.monthly_data ? (
                                    <span>
                                        Expanded dataset required for dynamic charting.
                                        <br />Please go to <b>Analysis Tab</b> and click <b>Process Data</b> to update your session.
                                    </span>
                                ) : filteredStats.length === 0 ? (
                                    "No SKUs match your current filters. Try selecting 'All' to reset."
                                ) : (
                                    "No trending data found for the top items in this selection."
                                )}
                            </p>
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

                    {/* Filters Toolbar */}
                    <div className="p-4 bg-white border-b border-slate-100 flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-wider mr-2">
                            <Filter size={14} /> Filters:
                        </div>

                        <select
                            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg p-2 font-medium focus:ring-2 focus:ring-blue-100 outline-none"
                            value={filters.chain}
                            onChange={(e) => setFilters(prev => ({ ...prev, chain: e.target.value }))}
                        >
                            <option value="All">All Chains</option>
                            {uniqueChains.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                        </select>

                        <select
                            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg p-2 font-medium focus:ring-2 focus:ring-blue-100 outline-none"
                            value={filters.category}
                            onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                        >
                            <option value="All">All Categories</option>
                            {uniqueCategories.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                        </select>

                        <select
                            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg p-2 font-medium focus:ring-2 focus:ring-blue-100 outline-none"
                            value={filters.dtCode}
                            onChange={(e) => setFilters(prev => ({ ...prev, dtCode: e.target.value }))}
                        >
                            <option value="All">All DT Codes</option>
                            {uniqueDtCodes.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                        </select>

                        {(filters.chain !== 'All' || filters.category !== 'All' || filters.dtCode !== 'All') && (
                            <button
                                onClick={clearFilters}
                                className="flex items-center gap-1 text-xs font-bold text-rose-500 hover:text-rose-600 bg-rose-50 hover:bg-rose-100 px-3 py-2 rounded-lg transition-colors ml-auto"
                            >
                                <X size={14} /> Clear Filters
                            </button>
                        )}

                        <div className="ml-auto text-xs font-bold text-slate-400">
                            Showing {filteredStats.length} / {displayStats.length} items
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
                                    <th className="px-6 py-5 text-center text-[10px] font-black text-rose-600 bg-rose-50/50 uppercase tracking-widest font-black">
                                        <div className="flex flex-col items-center">
                                            <span>Inventory Alert</span>
                                            <span className="opacity-70 text-[9px]">Next Critical Point (ROP)</span>
                                        </div>
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 bg-white">
                                {paginatedStats.map((sku, i) => (
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
                                        <td className="px-6 py-4 whitespace-nowrap text-center bg-rose-50/20">
                                            <span className="text-rose-700 font-black text-base drop-shadow-sm flex items-center justify-center gap-1">
                                                {sku.reorder_point ? (
                                                    <>
                                                        <AlertCircle size={14} className="text-rose-400" />
                                                        {Math.round(sku.reorder_point).toLocaleString()}
                                                    </>
                                                ) : '-'}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-bold text-slate-600 disabled:opacity-50 hover:bg-slate-50"
                            >
                                Previous
                            </button>
                            <span className="text-sm font-bold text-slate-500">
                                Page {currentPage} of {totalPages}
                            </span>
                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-bold text-slate-600 disabled:opacity-50 hover:bg-slate-50"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div >
    );
};

export default PrimaryDataTab;
