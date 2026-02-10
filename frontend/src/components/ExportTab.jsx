import React from 'react';
import { Download, AlertCircle, FileText, CheckCircle, TrendingUp, Search, Activity, BarChart, FileSpreadsheet, Box, Info, Zap, Layers } from 'lucide-react';

const ExportTab = ({ uploadData, processedData, charts, safetyStockData, simulationData }) => {

    const downloadCSV = (data, filename) => {
        if (!data || (Array.isArray(data) && data.length === 0)) {
            alert("No data available for distribution. Please initialize the analytical stream.");
            return;
        }

        try {
            const arrayData = Array.isArray(data) ? data : [data];
            const headers = Object.keys(arrayData[0]).join(',');
            const rows = arrayData.map(obj => {
                return Object.values(obj).map(val => {
                    if (val === null || val === undefined) return '';
                    const str = String(val);
                    if (str.includes(',') || str.includes('\n') || str.includes('"')) {
                        return `"${str.replace(/"/g, '""')}"`;
                    }
                    return str;
                }).join(',');
            });

            const csvContent = "\ufeff" + [headers, ...rows].join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);

            const link = document.createElement("a");
            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();

            setTimeout(() => {
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }, 100);
        } catch (err) {
            console.error("Export error:", err);
            alert("Export protocol interrupted: " + err.message);
        }
    };

    const handleDownload = (dataType) => {
        switch (dataType) {
            case 'SKU Statistics':
                downloadCSV(charts?.sku_stats || [], 'inventory_intelligence_report.csv');
                break;
            case 'Safety Stock':
                downloadCSV(safetyStockData || [], 'stock_optimization_targets.csv');
                break;
            case 'Simulation Log':
                downloadCSV(simulationData?.metrics || [], 'simulation_lifecycle_trace.csv');
                break;
            case 'Summary Stats':
                if (processedData?.summary_statistics) {
                    const flatStats = Object.entries(processedData.summary_statistics).flatMap(([col, metrics]) =>
                        Object.entries(metrics).map(([metric, value]) => ({ column: col, metric, value }))
                    );
                    downloadCSV(flatStats, 'dataset_summary_telemetry.csv');
                }
                break;
            default:
                alert(`Export for ${dataType} is not configured.`);
        }
    };

    if (!uploadData) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <Box size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">Export Locked</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Data source required to unlock export protocols and distribution reports.</p>
            </div>
        );
    }

    const hasAnalysis = !!charts;
    const hasSkuStats = charts && charts.sku_stats && charts.sku_stats.length > 0;
    const hasSafetyStock = safetyStockData && safetyStockData.length > 0;
    const hasSimulation = simulationData && simulationData.metrics && simulationData.metrics.length > 0;

    return (
        <div className="animate-fade-in space-y-8 p-4 md:p-8">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-100 pb-8">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-emerald-600 font-black text-xs uppercase tracking-widest mb-1">
                        <Download size={14} /> Intelligence Distribution
                    </div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Export Results Center</h2>
                    <p className="text-slate-500 font-medium">Download high-fidelity CSV reports for decision support and ERP integration.</p>
                </div>
            </div>

            {/* Readiness Checklist */}
            <div className="premium-card p-8 bg-slate-50/50">
                <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-6 flex items-center gap-2">
                    <Search size={14} /> Ready for distribution
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    {[
                        { label: 'Source Active', icon: FileText, status: true, color: 'emerald' },
                        { label: 'Trend Analysis', icon: Activity, status: hasAnalysis, color: 'blue' },
                        { label: 'Safety Stock', icon: BarChart, status: hasSafetyStock, color: 'purple' },
                        { label: 'Simulation run', icon: TrendingUp, status: hasSimulation, color: 'indigo' }
                    ].map((item, i) => (
                        <div key={i} className="flex items-center gap-3">
                            <div className={`p-2 rounded-xl border ${item.status ? `bg-${item.color}-50 border-${item.color}-100 text-${item.color}-600` : 'bg-slate-100 border-slate-200 text-slate-300'}`}>
                                {item.status ? <CheckCircle size={18} /> : <item.icon size={18} />}
                            </div>
                            <span className={`text-sm font-bold ${item.status ? 'text-slate-700' : 'text-slate-400 italic'}`}>{item.label}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Historical & Analysis */}
                <div className="space-y-4">
                    <h3 className="text-lg font-black text-slate-800 flex items-center gap-2 mb-2">
                        <FileSpreadsheet size={20} className="text-blue-600" />
                        Observational Data
                    </h3>

                    <button
                        onClick={() => handleDownload('SKU Statistics')}
                        disabled={!hasSkuStats}
                        className={`w-full premium-card p-6 flex items-center justify-between group transition-all text-left ${hasSkuStats ? 'hover:border-blue-200 hover:shadow-xl' : 'opacity-50 grayscale'}`}
                    >
                        <div className="space-y-1">
                            <div className="text-sm font-black text-slate-800 tracking-tight flex items-center gap-2">
                                SKU Intel Report {hasSkuStats && <Zap size={12} className="text-blue-500 fill-current" />}
                            </div>
                            <p className="text-[10px] font-bold text-slate-500 max-w-[240px]">Export demand metrics and volatility (CV%) for all tokens.</p>
                        </div>
                        <div className={`p-3 rounded-2xl ${hasSkuStats ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'bg-slate-100 text-slate-300'}`}>
                            <Download size={20} className="group-hover:scale-110 transition-transform" />
                        </div>
                    </button>

                    <button
                        onClick={() => handleDownload('Summary Stats')}
                        disabled={!hasAnalysis}
                        className={`w-full premium-card p-6 flex items-center justify-between group transition-all text-left ${hasAnalysis ? 'hover:border-blue-200 hover:shadow-xl' : 'opacity-50 grayscale'}`}
                    >
                        <div className="space-y-1">
                            <div className="text-sm font-black text-slate-800 tracking-tight">Summary Statistics</div>
                            <p className="text-[10px] font-bold text-slate-500 max-w-[240px]">High-level aggregate distribution metrics for the entire dataset.</p>
                        </div>
                        <div className={`p-3 rounded-2xl ${hasAnalysis ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'bg-slate-100 text-slate-300'}`}>
                            <Download size={20} className="group-hover:scale-110 transition-transform" />
                        </div>
                    </button>
                </div>

                {/* Planning Outputs */}
                <div className="space-y-4">
                    <h3 className="text-lg font-black text-slate-800 flex items-center gap-2 mb-2">
                        <Layers size={20} className="text-purple-600" />
                        Computed Strategy
                    </h3>

                    <button
                        onClick={() => handleDownload('Safety Stock')}
                        disabled={!hasSafetyStock}
                        className={`w-full premium-card p-6 flex items-center justify-between group transition-all text-left ${hasSafetyStock ? 'hover:border-purple-200 hover:shadow-xl' : 'opacity-50 grayscale'}`}
                    >
                        <div className="space-y-1">
                            <div className="text-sm font-black text-slate-800 tracking-tight flex items-center gap-2">
                                Stock Optimization Hub {hasSafetyStock && <Zap size={12} className="text-purple-500 fill-current" />}
                            </div>
                            <p className="text-[10px] font-bold text-slate-500 max-w-[240px]">Critical SS and ROP levels for replenishment automation.</p>
                        </div>
                        <div className={`p-3 rounded-2xl ${hasSafetyStock ? 'bg-purple-600 text-white shadow-lg shadow-purple-100' : 'bg-slate-100 text-slate-300'}`}>
                            <Download size={20} className="group-hover:scale-110 transition-transform" />
                        </div>
                    </button>

                    <button
                        onClick={() => handleDownload('Simulation Log')}
                        disabled={!hasSimulation}
                        className={`w-full premium-card p-6 flex items-center justify-between group transition-all text-left ${hasSimulation ? 'hover:border-indigo-200 hover:shadow-xl' : 'opacity-50 grayscale'}`}
                    >
                        <div className="space-y-1">
                            <div className="text-sm font-black text-slate-800 tracking-tight">Simulation Trace</div>
                            <p className="text-[10px] font-bold text-slate-500 max-w-[240px]">Day-by-day inventory simulation log for structural testing.</p>
                        </div>
                        <div className={`p-3 rounded-2xl ${hasSimulation ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-100' : 'bg-slate-100 text-slate-300'}`}>
                            <Download size={20} className="group-hover:scale-110 transition-transform" />
                        </div>
                    </button>
                </div>
            </div>

            {!hasAnalysis && (
                <div className="relative overflow-hidden premium-card p-10 bg-slate-900 text-white">
                    <div className="relative z-10 flex flex-col md:flex-row items-center gap-8 justify-between">
                        <div className="space-y-4">
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-widest border border-blue-500/20">
                                <Info size={12} /> Knowledge Center
                            </div>
                            <h4 className="text-2xl font-black tracking-tight leading-tight">Why are download protocols locked?</h4>
                            <p className="text-slate-400 text-sm font-medium max-w-lg leading-relaxed">
                                Our distribution system requires raw data processing and strategy calculation before it can compile distribution-ready reports.
                            </p>
                            <button
                                onClick={() => window.location.hash = '#analysis'}
                                className="btn-primary px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-2"
                            >
                                <Zap size={14} /> Initialize Engine
                            </button>
                        </div>
                        <div className="opacity-10 pointer-events-none absolute right-[-5%] top-[-20%]">
                            <Layers size={300} />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ExportTab;
