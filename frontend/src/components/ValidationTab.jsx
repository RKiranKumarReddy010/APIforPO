import React, { useState } from 'react';
import { FileCheck, Loader, CheckCircle, AlertCircle, ChevronDown, ChevronRight, ShieldCheck, Database, Info, ShieldAlert, Layers, Search } from 'lucide-react';
import { validateData } from '../api';

const ValidationTab = ({ uploadData, onValidate }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [validationResult, setValidationResult] = useState(null);
    const [showWarnings, setShowWarnings] = useState(true);
    const [showInfo, setShowInfo] = useState(true);
    const [showDetailedIssues, setShowDetailedIssues] = useState(true);

    const handleValidate = async () => {
        if (!uploadData?.filepath) {
            setError("Please upload data first.");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await validateData(uploadData.filepath);
            const data = response.data;
            setValidationResult(data.validation);
            if (onValidate) onValidate(data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.error || "Validation protocol failed.");
        } finally {
            setLoading(false);
        }
    };

    if (!uploadData) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-[2rem] border-dashed m-8">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                    <Search size={48} className="text-slate-200" />
                </div>
                <h2 className="text-2xl font-black text-slate-400 mb-2 tracking-tight">System Ready for Audit</h2>
                <p className="text-slate-400 font-medium text-center max-w-sm">Data source required to initiate quality benchmarks and schema verification.</p>
            </div>
        );
    }

    return (
        <div className="animate-fade-in space-y-8 p-4 md:p-8">
            {/* Header section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-emerald-600 font-black text-xs uppercase tracking-widest mb-1">
                        <ShieldCheck size={14} /> Integrity Audit
                    </div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Data Quality Benchmark</h2>
                    <p className="text-slate-500 font-medium">Automatic verification of schema compliance and missing nodes.</p>
                </div>
                <button
                    className="btn-primary flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest disabled:opacity-50"
                    onClick={handleValidate}
                    disabled={loading}
                >
                    {loading ? (
                        <><Loader className="spin" size={18} /> Auditing...</>
                    ) : (
                        <><FileCheck size={18} /> Run Integrity Check</>
                    )}
                </button>
            </div>

            {error && (
                <div className="flex items-start gap-4 bg-rose-50 border border-rose-100 p-6 rounded-3xl animate-fade-in text-rose-700">
                    <ShieldAlert size={24} className="shrink-0" />
                    <div className="font-black text-sm leading-tight italic">{error}</div>
                </div>
            )}

            {validationResult && (
                <div className="animate-fade-in space-y-8">
                    {/* Primary Status Banner */}
                    <div className={`p-8 rounded-[2rem] border relative overflow-hidden flex items-center gap-6 ${validationResult.is_valid
                        ? 'bg-emerald-50 border-emerald-100 text-emerald-900'
                        : 'bg-rose-50 border-rose-100 text-rose-900'
                        }`}>
                        <div className={`p-5 rounded-3xl shadow-lg ${validationResult.is_valid ? 'bg-emerald-500 text-white' : 'bg-rose-500 text-white'
                            }`}>
                            {validationResult.is_valid ? <CheckCircle size={32} /> : <AlertCircle size={32} />}
                        </div>
                        <div className="relative z-10">
                            <h3 className="text-2xl font-black tracking-tight mb-1">
                                {validationResult.is_valid ? 'Validation Protocol Passed' : 'Structural Issues Detected'}
                            </h3>
                            <p className={`font-bold text-sm ${validationResult.is_valid ? 'text-emerald-600' : 'text-rose-600'
                                }`}>
                                {validationResult.is_valid
                                    ? 'Dataset fulfills all critical schema and integrity requirements.'
                                    : 'Some nodes require attention before proceeding to high-fidelity analysis.'}
                            </p>
                        </div>
                        <div className="absolute right-0 top-0 h-full w-1/3 opacity-5 pointer-events-none">
                            <Layers size={200} className="translate-x-1/2 -translate-y-1/4" />
                        </div>
                    </div>

                    {/* Critical Faults - Full Width */}
                    {validationResult.errors && validationResult.errors.length > 0 && (
                        <div className="premium-card p-8 border-rose-100 bg-rose-50/20">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="bg-rose-500 p-2 rounded-xl text-white">
                                    <ShieldAlert size={20} />
                                </div>
                                <h4 className="text-lg font-black text-slate-800 tracking-tight">Critical Impediments</h4>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {validationResult.errors.map((err, idx) => (
                                    <div key={idx} className="flex items-start gap-3 p-4 bg-white rounded-2xl border border-rose-50 shadow-sm text-sm font-bold text-rose-700">
                                        <span className="shrink-0 mt-0.5 text-rose-400">•</span> {err}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Main Diagnostic Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
                        {/* Warnings Tab */}
                        {validationResult.warnings && validationResult.warnings.length > 0 && (
                            <div className="premium-card flex flex-col overflow-hidden transition-all h-full">
                                <button
                                    onClick={() => setShowWarnings(!showWarnings)}
                                    className="w-full flex items-center justify-between p-8 bg-amber-50/30 hover:bg-amber-100/30 transition-colors"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="bg-amber-500 p-2 rounded-xl text-white shadow-lg shadow-amber-100">
                                            <AlertCircle size={20} />
                                        </div>
                                        <div className="text-left">
                                            <h4 className="text-lg font-black text-slate-800 tracking-tight">Attention Zones ({validationResult.warnings.length})</h4>
                                            <p className="text-[10px] font-black text-amber-600 uppercase tracking-widest leading-none mt-1">Non-critical optimizations</p>
                                        </div>
                                    </div>
                                    <div className={`transition-transform duration-300 ${showWarnings ? 'rotate-180' : ''}`}>
                                        <ChevronDown size={24} className="text-slate-400" />
                                    </div>
                                </button>
                                {showWarnings && (
                                    <div className="flex-1 p-8 bg-white border-t border-slate-50 space-y-4">
                                        {validationResult.warnings.map((warning, idx) => (
                                            <div key={idx} className="min-h-[64px] p-4 bg-amber-50/50 rounded-2xl border border-amber-100 text-sm font-bold text-amber-800 flex items-start gap-3 italic">
                                                <span className="shrink-0 text-amber-400 mt-0.5">⚠️</span> {warning}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Audit Insights */}
                        {validationResult.info && validationResult.info.length > 0 && (
                            <div className="premium-card flex flex-col overflow-hidden transition-all h-full">
                                <button
                                    onClick={() => setShowInfo(!showInfo)}
                                    className="w-full flex items-center justify-between p-8 bg-blue-50/30 hover:bg-blue-100/30 transition-colors"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="bg-blue-500 p-2 rounded-xl text-white shadow-lg shadow-blue-100">
                                            <Info size={20} />
                                        </div>
                                        <div className="text-left">
                                            <h4 className="text-lg font-black text-slate-800 tracking-tight">Audit Insights</h4>
                                            <p className="text-[10px] font-black text-blue-600 uppercase tracking-widest leading-none mt-1">Schema and Feature metadata</p>
                                        </div>
                                    </div>
                                    <div className={`transition-transform duration-300 ${showInfo ? 'rotate-180' : ''}`}>
                                        <ChevronDown size={24} className="text-slate-400" />
                                    </div>
                                </button>
                                {showInfo && (
                                    <div className="flex-1 p-8 bg-white border-t border-slate-50 space-y-4">
                                        {validationResult.info.map((info, idx) => (
                                            <div key={idx} className="min-h-[64px] p-4 bg-blue-50/50 rounded-2xl border border-blue-100 text-sm font-bold text-blue-800 flex items-start gap-3">
                                                <span className="shrink-0 text-blue-400 mt-0.5">ℹ️</span> {info}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Data Quality Issues - Spanning Full Width for cleaner finish */}
                    {validationResult.data_quality_issues && Object.keys(validationResult.data_quality_issues).length > 0 && (
                        <div className="premium-card overflow-hidden">
                            <button
                                onClick={() => setShowDetailedIssues(!showDetailedIssues)}
                                className="w-full flex items-center justify-between p-8 bg-slate-50/80 hover:bg-slate-100/80 transition-colors"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="bg-slate-800 p-2 rounded-xl text-white shadow-lg shadow-slate-200">
                                        <Search size={20} />
                                    </div>
                                    <div className="text-left">
                                        <h4 className="text-lg font-black text-slate-800 tracking-tight">Full Quality Log</h4>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mt-1">Raw telemetry nodes</p>
                                    </div>
                                </div>
                                <div className={`transition-transform duration-300 ${showDetailedIssues ? 'rotate-180' : ''}`}>
                                    <ChevronDown size={24} className="text-slate-400" />
                                </div>
                            </button>
                            {showDetailedIssues && (
                                <div className="p-4 bg-slate-900 overflow-hidden">
                                    <div className="max-h-[500px] overflow-y-auto custom-scrollbar p-6 bg-slate-900 text-emerald-400 font-mono text-xs leading-relaxed space-y-1">
                                        <pre className="whitespace-pre-wrap">
                                            {JSON.stringify(validationResult.data_quality_issues, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ValidationTab;
