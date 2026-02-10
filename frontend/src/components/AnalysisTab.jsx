import React from 'react';
import { processData, getCharts } from '../api';
import { Activity, Loader, CheckCircle, TrendingUp, BarChart3, ChevronDown, ChevronRight, Zap, Target, Database, Layers, Info } from 'lucide-react';
import Plot from 'react-plotly.js';

const AnalysisTab = ({ uploadData, onAnalyze }) => {
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [stats, setStats] = React.useState(null);
    const [charts, setCharts] = React.useState(null);
    const [loadingCharts, setLoadingCharts] = React.useState(false);
    const [showSkuStats, setShowSkuStats] = React.useState(false);
    const [statusMessage, setStatusMessage] = React.useState('');

    const handleProcess = async () => {
        if (!uploadData?.filepath) {
            setError("Please upload data first. No filepath found.");
            return;
        }

        setLoading(true);
        setError(null);
        setStatusMessage("Initializing Processing Engine...");

        try {
            setStatusMessage("Aggregating temporal demand snapshots...");
            const response = await processData(uploadData.filepath);
            const data = response.data;
            if (!data || !data.statistics) {
                throw new Error("Invalid response from server: No statistics returned");
            }
            setStats(data.statistics);

            setStatusMessage("Generating visual intelligence...");
            setLoadingCharts(true);
            try {
                const chartsResponse = await getCharts(uploadData.filepath);
                if (chartsResponse.data && chartsResponse.data.charts) {
                    const chartsData = chartsResponse.data.charts;
                    setCharts(chartsData);
                    setStatusMessage("Analysis protocol complete.");
                    if (onAnalyze) onAnalyze(data.statistics, chartsData);
                } else {
                    setStatusMessage("Stream complete (Visuals unavailable).");
                    if (onAnalyze) onAnalyze(data.statistics, null);
                }
            } catch (chartErr) {
                console.error('Charts error:', chartErr);
                setStatusMessage("Stream complete (Visual errors).");
                if (onAnalyze) onAnalyze(data.statistics, null);
            } finally {
                setLoadingCharts(false);
            }
        } catch (err) {
            console.error("Processing error:", err);
            setError(err.message || err.response?.data?.error || "Processing failure.");
            setStatusMessage("Protocol aborted.");
        } finally {
            setLoading(false);
            setTimeout(() => {
                if (!error) setStatusMessage('');
            }, 3000);
        }
    };

    if (!uploadData) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <Database size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">Stream Connection Required</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Please establish a data source in the <b>Upload</b> tab before initializing analysis.</p>
            </div>
        );
    }

    return (
        <div className="animate-fade-in space-y-8 p-4 md:p-8">
            {/* Header section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-blue-600 font-black text-xs uppercase tracking-widest mb-1">
                        <Activity size={14} /> Analytics Engine
                    </div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Advanced Trend Extraction</h2>
                    <p className="text-slate-500 font-medium">Model demand volatility and inventory patterns across SKU tiers.</p>
                </div>
                <button
                    className="btn-primary flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest disabled:opacity-50"
                    onClick={handleProcess}
                    disabled={loading}
                >
                    {loading ? (
                        <><Loader className="spin" size={18} /> Processing...</>
                    ) : (
                        <><Zap size={18} /> Analyze Stream</>
                    )}
                </button>
            </div>

            {/* Status indicators */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {loading && (
                    <div className="bg-blue-50/50 border border-blue-100 p-6 rounded-3xl animate-pulse flex items-center gap-4">
                        <div className="bg-blue-500 p-3 rounded-2xl text-white shadow-lg shadow-blue-100">
                            <Loader className="spin" size={24} />
                        </div>
                        <div>
                            <div className="text-xs font-black text-blue-400 uppercase tracking-widest mb-0.5">Engine Status</div>
                            <div className="text-lg font-black text-blue-700">{statusMessage}</div>
                        </div>
                    </div>
                )}

                {!loading && statusMessage && !error && (
                    <div className="bg-emerald-50 border border-emerald-100 p-6 rounded-3xl flex items-center gap-4 animate-fade-in">
                        <div className="bg-emerald-500 p-3 rounded-2xl text-white shadow-lg shadow-emerald-100">
                            <CheckCircle size={24} />
                        </div>
                        <div>
                            <div className="text-xs font-black text-emerald-400 uppercase tracking-widest mb-0.5">Protocol Result</div>
                            <div className="text-lg font-black text-emerald-700">{statusMessage}</div>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="bg-rose-50 border border-rose-100 p-6 rounded-3xl flex items-center gap-4 animate-fade-in col-span-2">
                        <div className="bg-rose-500 p-3 rounded-2xl text-white shadow-lg shadow-rose-100">
                            <Activity size={24} />
                        </div>
                        <div>
                            <div className="text-xs font-black text-rose-400 uppercase tracking-widest mb-0.5">Critical Fault</div>
                            <div className="text-lg font-black text-rose-700">{error}</div>
                        </div>
                    </div>
                )}
            </div>

            {stats && (
                <div className="animate-fade-in space-y-8">
                    {/* Key Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {[
                            { label: 'Historical Data points', val: stats.processed_rows.toLocaleString(), icon: Layers, color: 'text-blue-600', bg: 'bg-blue-50' },
                            { label: 'SKU Count', val: stats.sku_ids?.length || 0, icon: Target, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                            { label: 'Analytical Attributes', val: stats.columns?.length || 0, icon: Database, color: 'text-purple-600', bg: 'bg-purple-50' },
                        ].map((stat, i) => (
                            <div key={i} className="bg-white border border-slate-100 p-6 rounded-[1.5rem] shadow-sm flex items-center gap-4 group hover:-translate-y-1 transition-transform">
                                <div className={`${stat.bg} ${stat.color} p-4 rounded-2xl`}>
                                    <stat.icon size={28} />
                                </div>
                                <div>
                                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">{stat.label}</div>
                                    <div className="text-3xl font-black text-slate-800">{stat.val}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {charts && (
                        <div className="space-y-8">
                            <div className="grid grid-cols-1 gap-8">
                                <div className="premium-card p-4 group">
                                    <div className="flex items-center gap-3 mb-4 px-4 pt-4">
                                        <div className="bg-indigo-50 p-2.5 rounded-2xl text-indigo-500 group-hover:rotate-6 transition-transform">
                                            <BarChart3 size={20} />
                                        </div>
                                        <h4 className="text-lg font-black text-slate-800 tracking-tight">Pareto Demand Distribution</h4>
                                    </div>
                                    <div className="w-full h-[500px]">
                                        <Plot
                                            data={JSON.parse(charts.demand_distribution).data}
                                            layout={{
                                                ...JSON.parse(charts.demand_distribution).layout,
                                                autosize: true,
                                                margin: { l: 150, r: 120, t: 30, b: 60 },
                                                title: null,
                                                showlegend: false,
                                                plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
                                                font: { family: 'Outfit, sans-serif' },
                                                xaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true },
                                                yaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true }
                                            }}
                                            config={{ responsive: true, displayModeBar: false }}
                                            useResizeHandler={true}
                                            style={{ width: '100%', height: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div className="premium-card p-4 group">
                                    <div className="flex items-center gap-3 mb-4 px-4 pt-4">
                                        <div className="bg-amber-50 p-2.5 rounded-2xl text-amber-500 group-hover:rotate-6 transition-transform">
                                            <Activity size={20} />
                                        </div>
                                        <h4 className="text-lg font-black text-slate-800 tracking-tight">Demand Stability Profile</h4>
                                    </div>
                                    <div className="w-full h-[500px]">
                                        <Plot
                                            data={JSON.parse(charts.cv_distribution).data}
                                            layout={{
                                                ...JSON.parse(charts.cv_distribution).layout,
                                                autosize: true,
                                                margin: { l: 60, r: 40, t: 80, b: 60 },
                                                title: null,
                                                // Aggressive cleaning of backend annotations to prevent overlap
                                                annotations: [
                                                    { x: 0.25, y: 1.05, yref: "paper", text: "STABLE", showarrow: false, font: { color: "#22c55e", size: 10, weight: 'bold' }, yanchor: "bottom" },
                                                    { x: 0.5, y: 1.15, yref: "paper", text: "MODERATE", showarrow: false, font: { color: "#f97316", size: 10, weight: 'bold' }, yanchor: "bottom" },
                                                    { x: 0.75, y: 1.05, yref: "paper", text: "VOLATILE", showarrow: false, font: { color: "#ef4444", size: 10, weight: 'bold' }, yanchor: "bottom" }
                                                ],
                                                plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
                                                font: { family: 'Outfit, sans-serif' },
                                                xaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true },
                                                yaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true }
                                            }}
                                            config={{ responsive: true, displayModeBar: false }}
                                            useResizeHandler={true}
                                            style={{ width: '100%', height: '100%' }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="premium-card p-4 group">
                                <div className="flex items-center gap-3 mb-6 px-4 pt-4">
                                    <div className="bg-emerald-50 p-2.5 rounded-2xl text-emerald-500 group-hover:rotate-6 transition-transform">
                                        <TrendingUp size={20} />
                                    </div>
                                    <h4 className="text-lg font-black text-slate-800 tracking-tight">Historical Offtake Trends</h4>
                                </div>
                                <div className="w-full h-[550px]">
                                    <Plot
                                        data={JSON.parse(charts.offtake_trends).data}
                                        layout={{
                                            ...JSON.parse(charts.offtake_trends).layout,
                                            autosize: true,
                                            margin: { l: 80, r: 160, t: 30, b: 80 },
                                            title: null,
                                            plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
                                            font: { family: 'Outfit, sans-serif' },
                                            xaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true },
                                            yaxis: { gridcolor: '#F1F5F9', zerolinecolor: '#F1F5F9', automargin: true },
                                            legend: { orientation: 'v', yanchor: 'top', y: 1, xanchor: 'left', x: 1.02 }
                                        }}
                                        config={{ responsive: true, displayModeBar: true }}
                                        useResizeHandler={true}
                                        style={{ width: '100%', height: '100%' }}
                                    />
                                </div>
                            </div>

                            {charts.sku_stats && charts.sku_stats.length > 0 && (
                                <div className="premium-card overflow-hidden">
                                    <button
                                        onClick={() => setShowSkuStats(!showSkuStats)}
                                        className="w-full flex items-center justify-between p-8 bg-slate-50/50 hover:bg-slate-100/50 transition-colors"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="bg-white p-2.5 rounded-2xl shadow-sm text-slate-700 border border-slate-100">
                                                <Layers size={20} />
                                            </div>
                                            <div className="text-left">
                                                <h3 className="text-xl font-black text-slate-800 tracking-tight">Primary Data Summary</h3>
                                                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">DETAILED ANALYTICAL LOG (Top 50 Items)</p>
                                            </div>
                                        </div>
                                        <div className={`transition-transform duration-300 ${showSkuStats ? 'rotate-180' : ''}`}>
                                            <ChevronDown size={24} className="text-slate-400" />
                                        </div>
                                    </button>
                                    {showSkuStats && (
                                        <div className="animate-fade-in overflow-x-auto">
                                            <table className="min-w-full text-sm">
                                                <thead className="bg-white border-b border-slate-100">
                                                    <tr>
                                                        <th className="px-8 py-5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">SKU ID</th>
                                                        <th className="px-6 py-5 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">Avg Daily Offtake</th>
                                                        <th className="px-6 py-5 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">Demand Deviation</th>
                                                        <th className="px-6 py-5 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">CV (Coefficient of Var.)</th>
                                                        <th className="px-8 py-5 text-right text-[10px] font-black text-indigo-600 uppercase tracking-widest">Cumulative Forecast</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-slate-100 bg-white">
                                                    {charts.sku_stats.slice(0, 50).map((sku, idx) => (
                                                        <tr key={idx} className="hover:bg-slate-50 transition-colors">
                                                            <td className="px-8 py-4 whitespace-nowrap text-sm font-black text-slate-700">{sku.key}</td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-right font-bold text-slate-600">{sku.avg_daily_demand?.toFixed(2) || '—'}</td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-right text-slate-500 font-medium">{sku.std_daily_demand?.toFixed(2) || '—'}</td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-right">
                                                                <span className={`px-2 py-1 rounded-lg text-[10px] font-black ${sku.cv_demand > 1 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-500'}`}>
                                                                    {sku.cv_demand?.toFixed(3) || '—'}
                                                                </span>
                                                            </td>
                                                            <td className="px-8 py-4 whitespace-nowrap text-right font-black text-indigo-600">{sku.total_demand?.toLocaleString() || '—'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default AnalysisTab;

