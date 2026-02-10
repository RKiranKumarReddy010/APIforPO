import React, { useState } from 'react';
import { calculateSafetyStock, batchCalculate } from '../api';
import { BarChart2, Loader, CheckCircle, AlertOctagon, TrendingUp, Package, Activity, Target, ShieldCheck, Database, Layers, ArrowRight } from 'lucide-react';
import Plot from 'react-plotly.js';

const SafetyStockTab = ({ uploadData, analysisData, appConfig, onCalculate }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [results, setResults] = useState([]);

    const handleCalculateAll = async () => {
        if (!analysisData?.sku_ids || analysisData.sku_ids.length === 0) {
            setError("No SKUs found. Please process data first.");
            return;
        }

        setLoading(true);
        setError(null);
        setResults([]);

        try {
            const skuList = analysisData.sku_ids.slice(0, 50);
            const response = await batchCalculate({
                filepath: uploadData.filepath,
                sku_ids: skuList,
                service_level: appConfig?.default_service_level || 0.975,
                lead_time_days: appConfig?.default_lead_time_days || 7
            });

            const data = response.data;
            const successResults = data.results.filter(r => r.status === 'success');
            setResults(successResults);
            if (onCalculate) onCalculate(data.results);
        } catch (err) {
            console.error("Calculation error details:", err);
            const serverError = err.response?.data?.error;
            const errorMsg = serverError
                ? `Calculation abort: ${typeof serverError === 'object' ? JSON.stringify(serverError) : serverError}`
                : `System error: ${err.message}`;
            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    if (!analysisData) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <ShieldCheck size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">Analytics Stream Pending</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Complete the <b>Analysis</b> step to initialize target calculations.</p>
            </div>
        );
    }

    const totalSS = results.reduce((sum, r) => sum + (r.safety_stock || 0), 0);
    const avgSS = results.length > 0 ? totalSS / results.length : 0;
    const leadTime = appConfig?.default_lead_time_days || 7;
    const totalROP = results.reduce((sum, r) => (sum + (r.demand_mean * leadTime) + r.safety_stock), 0);
    const avgROP = results.length > 0 ? totalROP / results.length : 0;

    const topResults = [...results].sort((a, b) => b.demand_mean - a.demand_mean).slice(0, 20);
    const chartData = [
        {
            y: topResults.map(r => r.sku_id),
            x: topResults.map(r => r.demand_mean),
            type: 'bar', orientation: 'h', name: 'Avg Demand',
            marker: { color: 'rgba(79, 70, 229, 0.8)', line: { color: '#4F46E5', width: 1 } }
        },
        {
            y: topResults.map(r => r.sku_id),
            x: topResults.map(r => r.safety_stock),
            type: 'bar', orientation: 'h', name: 'Safety Buffer',
            marker: { color: 'rgba(244, 63, 94, 0.8)', line: { color: '#F43F5E', width: 1 } }
        }
    ];

    return (
        <div className="animate-fade-in space-y-8 p-4 md:p-8">
            {/* Header section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-rose-600 font-black text-xs uppercase tracking-widest mb-1">
                        <ShieldCheck size={14} /> Buffer Optimization
                    </div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Safety Stock Stratification</h2>
                    <p className="text-slate-500 font-medium">Quantify risk-adjusted inventory levels based on lead time and service targets.</p>
                </div>
                <button
                    className="btn-primary flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest disabled:opacity-50"
                    onClick={handleCalculateAll}
                    disabled={loading}
                >
                    {loading ? (
                        <><Loader className="spin" size={18} /> Calculating...</>
                    ) : (
                        <><Activity size={18} /> Run Calculation</>
                    )}
                </button>
            </div>

            {error && (
                <div className="flex items-start gap-4 bg-rose-50 border border-rose-100 p-6 rounded-3xl animate-fade-in text-rose-700">
                    <AlertOctagon size={24} className="shrink-0" />
                    <div className="font-black text-sm leading-tight italic">{error}</div>
                </div>
            )}

            {results.length > 0 && (
                <div className="animate-fade-in space-y-8">
                    {/* Success Banner */}
                    <div className="bg-emerald-50 border border-emerald-100 p-6 rounded-3xl flex items-center gap-4">
                        <div className="bg-emerald-500 p-3 rounded-2xl text-white shadow-lg shadow-emerald-100">
                            <CheckCircle size={24} />
                        </div>
                        <div>
                            <div className="text-xs font-black text-emerald-400 uppercase tracking-widest mb-0.5">Engine Status</div>
                            <div className="text-lg font-black text-emerald-700">Stock targets successfully stratified for the selected domain.</div>
                        </div>
                    </div>

                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        {[
                            { label: 'Service Level Target', val: '97.5%', icon: Target, color: 'text-blue-600', bg: 'bg-blue-50' },
                            { label: 'Cumulative Safety Stock', val: totalSS.toLocaleString(undefined, { maximumFractionDigits: 0 }), icon: ShieldCheck, color: 'text-rose-600', bg: 'bg-rose-50' },
                            { label: 'Avg Safety Stock Target', val: avgSS.toLocaleString(undefined, { maximumFractionDigits: 1 }), icon: Package, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                            { label: 'Average Reorder Point (ROP)', val: avgROP.toLocaleString(undefined, { maximumFractionDigits: 1 }), icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-50' },
                        ].map((stat, i) => (
                            <div key={i} className="bg-white border border-slate-100 p-6 rounded-[1.5rem] shadow-sm flex items-center gap-4 group hover:-translate-y-1 transition-transform">
                                <div className={`${stat.bg} ${stat.color} p-4 rounded-2xl`}>
                                    <stat.icon size={24} />
                                </div>
                                <div>
                                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">{stat.label}</div>
                                    <div className="text-2xl font-black text-slate-800">{stat.val}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Visual & Ledger Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 premium-card p-8 group">
                            <div className="flex items-center gap-3 mb-8">
                                <div className="bg-slate-50 p-2.5 rounded-2xl text-slate-400 group-hover:rotate-6 transition-transform">
                                    <BarChart2 size={20} />
                                </div>
                                <h4 className="text-lg font-black text-slate-800 tracking-tight">Forecast vs Safety Stock Buffer</h4>
                            </div>
                            <div className="w-full h-[500px]">
                                <Plot
                                    data={chartData}
                                    layout={{
                                        barmode: 'group',
                                        autosize: true,
                                        margin: { l: 80, r: 20, t: 10, b: 40 },
                                        legend: { orientation: 'h', y: 1.05, font: { family: 'Outfit, sans-serif' } },
                                        plot_bgcolor: 'rgba(0,0,0,0)',
                                        paper_bgcolor: 'rgba(0,0,0,0)',
                                        font: { family: 'Outfit, sans-serif' },
                                        xaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', title: 'Unit Volume' },
                                        yaxis: { automargin: true, gridcolor: '#F1F5F9' }
                                    }}
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '100%' }}
                                    config={{ displayModeBar: false }}
                                />
                            </div>
                        </div>

                        <div className="premium-card flex flex-col">
                            <div className="p-8 border-b border-slate-100 bg-slate-50/50">
                                <h4 className="text-lg font-black text-slate-800 tracking-tight">Detailed Reorder Log</h4>
                                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">OPEX-Optimized Inventory Targets</p>
                            </div>
                            <div className="flex-1 overflow-y-auto max-h-[500px] no-scrollbar">
                                <div className="divide-y divide-slate-100">
                                    {results.map((r, i) => (
                                        <div key={i} className="p-6 hover:bg-slate-50 transition-colors group">
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="text-sm font-black text-slate-800">{r.sku_id}</div>
                                                <div className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-black rounded-lg">CALC_OK</div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 text-rose-500">Safety Stock</div>
                                                    <div className="text-lg font-black text-slate-800">{r.safety_stock?.toLocaleString()}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 text-indigo-500">Reorder Point (ROP)</div>
                                                    <div className="text-lg font-black text-slate-800">{r.reorder_point?.toLocaleString()}</div>
                                                </div>
                                            </div>
                                            <div className="mt-3 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2 text-[10px] font-black text-slate-400">
                                                <ArrowRight size={10} /> CV: {r.cv_demand?.toFixed(4)} <Layers size={10} className="ml-2" /> SLA: {r.service_level}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SafetyStockTab;

