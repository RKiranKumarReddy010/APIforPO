import React, { useState, useEffect, useMemo } from 'react';
import { Play, Loader, CheckCircle, AlertCircle, TrendingUp, Package, Calendar, Database, Zap, ArrowRight, Table, Filter, X } from 'lucide-react';
import Plot from 'react-plotly.js';
import { simulateInventory } from '../api';

const SimulationTab = ({ uploadData, safetyStockData, onSimulate }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [simulationResults, setSimulationResults] = useState(null);

    // UI State
    const [selectedSku, setSelectedSku] = useState('');
    const [initialInventory, setInitialInventory] = useState(5000);
    const [simulationDays, setSimulationDays] = useState(90);

    // Filter valid safety stock results
    const validSkus = safetyStockData?.filter(r => r.status === 'success') || [];

    useEffect(() => {
        if (validSkus.length > 0 && !selectedSku) {
            setSelectedSku(validSkus[0].sku_id);
            const skuData = validSkus[0];
            setInitialInventory(Math.ceil(skuData.demand_mean * 30));
        }
    }, [validSkus, selectedSku]);

    const handleSkuChange = (e) => {
        const skuId = e.target.value;
        setSelectedSku(skuId);
        const skuData = validSkus.find(r => r.sku_id === skuId);
        if (skuData) {
            setInitialInventory(Math.ceil(skuData.demand_mean * 30));
        }
    };

    // Filter Logic
    const [filters, setFilters] = useState({
        chain: 'All',
        category: 'All',
        dtCode: 'All'
    });

    const uniqueChains = useMemo(() => {
        const relevant = validSkus.filter(s =>
            (filters.category === 'All' || s.Category === filters.category) &&
            (filters.dtCode === 'All' || s.DT_Code === filters.dtCode)
        );
        return ['All', ...new Set(relevant.map(s => s.Chain || 'Unknown').filter(Boolean))].sort();
    }, [validSkus, filters.category, filters.dtCode]);

    const uniqueCategories = useMemo(() => {
        const relevant = validSkus.filter(s =>
            (filters.chain === 'All' || s.Chain === filters.chain) &&
            (filters.dtCode === 'All' || s.DT_Code === filters.dtCode)
        );
        return ['All', ...new Set(relevant.map(s => s.Category || 'Unknown').filter(Boolean))].sort();
    }, [validSkus, filters.chain, filters.dtCode]);

    const uniqueDtCodes = useMemo(() => {
        const relevant = validSkus.filter(s =>
            (filters.chain === 'All' || s.Chain === filters.chain) &&
            (filters.category === 'All' || s.Category === filters.category)
        );
        return ['All', ...new Set(relevant.map(s => s.DT_Code || 'Unknown').filter(Boolean))].sort();
    }, [validSkus, filters.chain, filters.category]);

    const filteredSkus = useMemo(() => {
        return validSkus.filter(sku => {
            return (filters.chain === 'All' || sku.Chain === filters.chain) &&
                (filters.category === 'All' || sku.Category === filters.category) &&
                (filters.dtCode === 'All' || sku.DT_Code === filters.dtCode);
        });
    }, [validSkus, filters]);

    const clearFilters = () => setFilters({ chain: 'All', category: 'All', dtCode: 'All' });

    // Update selection when filtered list changes
    useEffect(() => {
        if (filteredSkus.length > 0 && !filteredSkus.some(s => s.sku_id === selectedSku)) {
            setSelectedSku(filteredSkus[0].sku_id);
            setInitialInventory(Math.ceil(filteredSkus[0].demand_mean * 30));
        }
    }, [filteredSkus, selectedSku]);

    const handleRunSimulation = async () => {
        if (!uploadData?.filepath) {
            setError("Please upload data first.");
            return;
        }

        if (!selectedSku) {
            setError("Please select an SKU to simulate.");
            return;
        }

        const skuData = validSkus.find(r => r.sku_id === selectedSku);
        if (!skuData) {
            setError("Could not find data for selected SKU.");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const params = {
                filepath: uploadData.filepath,
                sku_id: selectedSku,
                initial_inventory: initialInventory,
                reorder_point: skuData.reorder_point,
                safety_stock: skuData.safety_stock,
                service_level: skuData.service_level || 0.975,
                lead_time_days: 7,
                coverage_days: 30,
                case_pack: 1,
                simulation_days: simulationDays
            };

            const response = await simulateInventory(params);
            setSimulationResults(response.data);
            if (onSimulate) onSimulate(response.data);

        } catch (err) {
            console.error("Simulation error:", err);
            setError(err.response?.data?.error || "Simulation failed.");
        } finally {
            setLoading(false);
        }
    };

    if (!uploadData) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <Database size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">Data Stream Required</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Upload your dataset to initialize the simulation engine.</p>
            </div>
        );
    }

    if (!safetyStockData || validSkus.length === 0) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <Zap size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">Targets Not Found</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Complete <b>Safety Stock</b> calculation to generate parameters for simulation.</p>
            </div>
        );
    }

    const getChartData = () => {
        if (!simulationResults?.metrics) return [];
        const metrics = simulationResults.metrics;
        const x = metrics.map((_, i) => i + 1);

        return [
            {
                x: x,
                y: metrics.map(m => m.inventory),
                type: 'scatter',
                mode: 'lines',
                name: 'Ending Inventory',
                line: { color: '#4F46E5', width: 3 }
            },
            {
                x: x,
                y: metrics.map(m => m.net_inventory),
                type: 'scatter',
                mode: 'lines',
                name: 'Net Stock Position',
                line: { color: '#9333ea', width: 2, dash: 'dash' }
            },
            {
                x: x,
                y: metrics.map(m => m.rop),
                type: 'scatter',
                mode: 'lines',
                name: 'Reorder Point (ROP)',
                line: { color: '#EF4444', width: 2, dash: 'dot' }
            }
        ];
    };

    return (
        <div className="animate-fade-in space-y-8 p-4 md:p-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-indigo-600 font-black text-xs uppercase tracking-widest mb-1">
                        <Zap size={14} /> Predictive Sandbox
                    </div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Inventory Trajectory Simulation</h2>
                    <p className="text-slate-500 font-medium">Model future stock behaviors using advanced offtake projections.</p>
                </div>
            </div>

            {/* Control Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-3 premium-card p-8">

                    {/* Filters Toolbar */}
                    <div className="flex flex-wrap items-center gap-4 mb-6 pb-6 border-b border-slate-100">
                        <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-wider mr-2">
                            <Filter size={14} /> Filters:
                        </div>

                        <select
                            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg p-2 font-medium focus:ring-2 focus:ring-indigo-100 outline-none"
                            value={filters.chain}
                            onChange={(e) => setFilters(prev => ({ ...prev, chain: e.target.value }))}
                        >
                            <option value="All">All Chains</option>
                            {uniqueChains.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                        </select>

                        <select
                            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg p-2 font-medium focus:ring-2 focus:ring-indigo-100 outline-none"
                            value={filters.category}
                            onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                        >
                            <option value="All">All Categories</option>
                            {uniqueCategories.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                        </select>

                        <select
                            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg p-2 font-medium focus:ring-2 focus:ring-indigo-100 outline-none"
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
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div>
                            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Target Asset (SKU)</label>
                            <div className="relative group">
                                <Package className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={18} />
                                <select
                                    className="w-full pl-12 pr-4 py-4 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-50/50 bg-slate-50 text-slate-800 font-black text-sm appearance-none outline-none transition-all"
                                    value={selectedSku}
                                    onChange={handleSkuChange}
                                >
                                    {filteredSkus.map(sku => (
                                        <option key={sku.sku_id} value={sku.sku_id}>{sku.sku_id}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Seed Inventory Units</label>
                            <div className="relative group">
                                <Database className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={18} />
                                <input
                                    type="number"
                                    className="w-full pl-12 pr-4 py-4 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-50/50 bg-slate-50 text-slate-800 font-black text-sm outline-none transition-all"
                                    value={initialInventory}
                                    onChange={(e) => setInitialInventory(parseInt(e.target.value))}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Horizon (Days)</label>
                            <div className="relative group">
                                <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={18} />
                                <input
                                    type="number"
                                    className="w-full pl-12 pr-4 py-4 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-50/50 bg-slate-50 text-slate-800 font-black text-sm outline-none transition-all"
                                    value={simulationDays}
                                    onChange={(e) => setSimulationDays(parseInt(e.target.value))}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <button
                    className="btn-primary flex items-center justify-center flex-col gap-2 rounded-3xl p-6 group disabled:opacity-50"
                    onClick={handleRunSimulation}
                    disabled={loading}
                >
                    {loading ? (
                        <Loader className="spin" size={32} />
                    ) : (
                        <div className="bg-white/20 p-4 rounded-2xl group-hover:scale-110 transition-transform">
                            <Play size={32} />
                        </div>
                    )}
                    <span className="font-black text-xs uppercase tracking-widest">{loading ? 'Simulating...' : 'Execute Run'}</span>
                </button>
            </div>

            {error && (
                <div className="flex items-start gap-4 bg-rose-50 border border-rose-100 p-6 rounded-3xl animate-fade-in text-rose-700">
                    <AlertCircle size={24} className="shrink-0" />
                    <div className="font-black text-sm leading-tight italic">{error}</div>
                </div>
            )}

            {simulationResults && (
                <div className="animate-fade-in space-y-8">
                    {/* Key Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        {[
                            { label: 'Avg Daily Inventory', val: simulationResults.results_summary.avg_inventory, color: 'text-indigo-600', bg: 'bg-indigo-50', icon: Database },
                            { label: 'Closing Stock', val: simulationResults.results_summary.final_inventory, color: 'text-emerald-600', bg: 'bg-emerald-50', icon: Package },
                            { label: 'Out of Stock Incidents', val: simulationResults.results_summary.stock_outs, color: 'text-rose-600', bg: 'bg-rose-50', icon: AlertCircle },
                            { label: 'Reorder Point (ROP)', val: simulationResults.reorder_point, color: 'text-amber-600', bg: 'bg-amber-50', icon: TrendingUp },
                        ].map((stat, i) => (
                            <div key={i} className="bg-white border border-slate-100 p-6 rounded-[1.5rem] shadow-sm flex items-center gap-4 group hover:-translate-y-1 transition-transform">
                                <div className={`${stat.bg} ${stat.color} p-4 rounded-2xl transition-transform group-hover:rotate-12`}>
                                    <stat.icon size={24} />
                                </div>
                                <div>
                                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-0.5">{stat.label}</div>
                                    <div className={`text-2xl font-black text-slate-800`}>{Math.round(stat.val).toLocaleString()}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Chart Center */}
                    <div className="premium-card p-8">
                        <div className="flex items-center gap-3 mb-8">
                            <div className="bg-indigo-600 p-2.5 rounded-2xl text-white shadow-lg shadow-indigo-100">
                                <TrendingUp size={24} />
                            </div>
                            <h3 className="text-xl font-black text-slate-800 tracking-tight">Projected Trajectory Mapping</h3>
                        </div>
                        <div className="w-full h-[450px]">
                            <Plot
                                data={getChartData()}
                                layout={{
                                    autosize: true,
                                    margin: { l: 80, r: 40, t: 20, b: 80 },
                                    title: null,
                                    showlegend: true,
                                    legend: { orientation: 'h', y: -0.2, font: { family: 'Outfit, sans-serif', size: 12 } },
                                    plot_bgcolor: 'rgba(0,0,0,0)',
                                    paper_bgcolor: 'rgba(0,0,0,0)',
                                    font: { family: 'Outfit, sans-serif' },
                                    xaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', title: 'Cycle Day (T+n)', automargin: true },
                                    yaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', title: 'Stock Units', automargin: true },
                                    hovermode: 'x unified'
                                }}
                                useResizeHandler={true}
                                style={{ width: '100%', height: '100%' }}
                                config={{ displayModeBar: false }}
                            />
                        </div>
                    </div>

                    {/* Performance Ledger */}
                    <div className="premium-card overflow-hidden">
                        <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50/30">
                            <div className="flex items-center gap-3">
                                <div className="bg-white p-2.5 rounded-2xl shadow-sm text-slate-700 border border-slate-100">
                                    <Table size={20} />
                                </div>
                                <div>
                                    <h3 className="text-xl font-black text-slate-800 tracking-tight">Inventory Trajectory Log</h3>
                                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">DETAILED 90-DAY SIMULATION AUDIT</p>
                                </div>
                            </div>
                            <div className="px-4 py-1.5 bg-white border border-slate-100 rounded-full text-[10px] font-black text-slate-400 uppercase tracking-widest shadow-sm">
                                {simulationResults.metrics.length} Days Simulated
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="min-w-full text-sm">
                                <thead className="bg-white border-b border-slate-100 sticky top-0 z-10">
                                    <tr>
                                        <th className="px-8 py-5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest border-r border-slate-100">S.No</th>
                                        <th className="px-6 py-5 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">Opening Stock</th>
                                        <th className="px-6 py-5 text-right text-[10px] font-black text-emerald-500 uppercase tracking-widest">Inbound Units</th>
                                        <th className="px-6 py-5 text-right text-[10px] font-black text-rose-500 uppercase tracking-widest">Offtake Forecast</th>
                                        <th className="px-6 py-5 text-right text-[10px] font-black text-slate-900 uppercase tracking-widest">Closing Stock</th>
                                        <th className="px-6 py-5 text-center text-[10px] font-black text-indigo-500 uppercase tracking-widest">System Remarks</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 bg-white">
                                    {simulationResults.metrics.map((row, idx) => (
                                        <tr key={idx} className={`hover:bg-slate-50 transition-colors animate-fade-in ${row.stockout ? 'bg-rose-50/50' : ''}`} style={{ animationDelay: `${idx * 0.01}s` }}>
                                            <td className="px-8 py-4 whitespace-nowrap text-xs font-black text-slate-400 border-r border-slate-100">T+{idx + 1}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-slate-700">
                                                {Math.round(row.inventory || row.beginning_inventory || 0).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-black text-emerald-600">
                                                {row.inventory_received > 0 ? `+${Math.round(row.inventory_received).toLocaleString()}` : '—'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-black text-rose-600">
                                                {Math.round(row.daily_offtake_forecast || row.demand || 0).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right">
                                                <span className={`text-sm font-black drop-shadow-sm ${row.net_inventory < 0 ? 'text-rose-600' : 'text-slate-900'}`}>
                                                    {Math.round(row.net_inventory).toLocaleString()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                                {row.reorder_point || row.reorder_flag || row.order_placed ? (
                                                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black bg-indigo-600 text-white shadow-lg shadow-indigo-100">
                                                        <ArrowRight size={10} /> REFILL: {Math.round(row.reorder_quantity || row.order_qty)}
                                                    </span>
                                                ) : row.stockout ? (
                                                    <span className="text-[10px] font-black text-rose-600 italic">CRITICAL STOCKOUT</span>
                                                ) : <span className="text-slate-200">...</span>}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SimulationTab;

