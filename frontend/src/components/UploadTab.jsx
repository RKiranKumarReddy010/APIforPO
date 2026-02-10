import React, { useState } from 'react';
import { Upload, CheckCircle, AlertCircle, Loader, ChevronDown, ChevronRight, FileText, Database, Layers, Info } from 'lucide-react';
import { uploadFile } from '../api';

const UploadTab = ({ onSuccess }) => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [uploadedData, setUploadedData] = useState(null);
    const [showPreview, setShowPreview] = useState(false);
    const [showColumnInfo, setShowColumnInfo] = useState(false);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        setFile(selectedFile);
        setError(null);
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Please select a file first.");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await uploadFile(file);
            setUploadedData(response.data);
            if (onSuccess) {
                onSuccess(response.data, false);
            }
        } catch (err) {
            console.error('Upload error:', err);
            setError(err.response?.data?.error || err.message || "Upload failed. Is the server running?");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="animate-fade-in space-y-8 p-4 md:p-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Ingest Dataset</h2>
                    <p className="text-slate-500 font-medium">Power your simulation engine with historical demand snapshots.</p>
                </div>
                <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
                    <Info size={14} /> Supported: CSV, XLSX
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Upload Zone */}
                <div className="lg:col-span-1 space-y-6">
                    <div
                        className={`group relative overflow-hidden rounded-3xl border-2 border-dashed transition-all duration-300 ${file
                            ? 'border-blue-200 bg-blue-50/30'
                            : 'border-slate-200 hover:border-blue-400 hover:bg-slate-50 bg-white'
                            }`}
                        onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('border-blue-500', 'bg-blue-50/50'); }}
                        onDragLeave={(e) => { e.preventDefault(); e.currentTarget.classList.remove('border-blue-500', 'bg-blue-50/50'); }}
                        onDrop={(e) => {
                            e.preventDefault();
                            e.currentTarget.classList.remove('border-blue-500', 'bg-blue-50/50');
                            if (e.dataTransfer.files?.[0]) {
                                setFile(e.dataTransfer.files[0]);
                                setError(null);
                            }
                        }}
                    >
                        <div className="p-10 text-center space-y-4">
                            <div className={`mx-auto w-16 h-16 rounded-2xl flex items-center justify-center transition-transform duration-500 group-hover:scale-110 ${file ? 'bg-blue-500 text-white shadow-lg shadow-blue-200' : 'bg-slate-100 text-slate-400'
                                }`}>
                                <Upload size={32} />
                            </div>

                            <div className="space-y-1">
                                <p className="font-bold text-slate-700">
                                    {file ? 'File Staged' : 'Drop your data here'}
                                </p>
                                <p className="text-sm text-slate-500 font-medium">
                                    {file ? file.name : 'or click to browse local files'}
                                </p>
                            </div>

                            <input
                                type="file"
                                onChange={handleFileChange}
                                accept=".csv,.xlsx,.xls"
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                        </div>

                        {file && (
                            <div className="bg-blue-500/5 px-6 py-4 flex items-center justify-between border-t border-blue-100 italic text-xs text-blue-600 font-medium">
                                <span>Size: {(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                                <button onClick={(e) => { e.preventDefault(); setFile(null); }} className="hover:underline font-bold">Clear</button>
                            </div>
                        )}
                    </div>

                    <button
                        className="btn-primary w-full py-4 rounded-2xl font-black text-sm uppercase tracking-wider flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group"
                        onClick={handleUpload}
                        disabled={loading || !file}
                    >
                        {loading ? (
                            <><Loader className="spin" size={18} /> Processing Payload...</>
                        ) : (
                            <><Layers size={18} className="group-hover:rotate-12 transition-transform" /> Execute Upload</>
                        )}
                    </button>

                    {error && (
                        <div className="flex items-start gap-3 bg-rose-50 border border-rose-100 text-rose-700 p-4 rounded-2xl animate-fade-in">
                            <AlertCircle size={20} className="shrink-0 mt-0.5" />
                            <div className="text-sm font-bold leading-tight">{error}</div>
                        </div>
                    )}
                </div>

                {/* Status & Preview Column */}
                <div className="lg:col-span-2 space-y-6">
                    {!uploadedData ? (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center bg-slate-50/50 border border-slate-100 rounded-[2rem] border-dashed">
                            <div className="bg-white p-6 rounded-half shadow-sm border border-slate-100 mb-6 group-hover:rotate-3 transition-transform">
                                <Database size={48} className="text-slate-200" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-400 mb-2">Awaiting Input Stream</h3>
                            <p className="text-slate-400 text-sm max-w-xs font-medium">
                                Please upload a valid CSV or Excel file to begin the inventory planning cycle.
                            </p>
                        </div>
                    ) : (
                        <div className="animate-fade-in space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="bg-white border border-slate-100 p-6 rounded-[1.5rem] shadow-sm flex items-center gap-4">
                                    <div className="bg-emerald-100 p-3 rounded-2xl text-emerald-600">
                                        <CheckCircle size={24} />
                                    </div>
                                    <div>
                                        <div className="text-xs font-black text-slate-400 uppercase tracking-widest mb-0.5">Stream Active</div>
                                        <div className="text-lg font-black text-slate-800 break-all">{uploadedData.filename}</div>
                                    </div>
                                </div>
                                <div className="bg-white border border-slate-100 p-6 rounded-[1.5rem] shadow-sm flex items-center gap-4">
                                    <div className="bg-blue-100 p-3 rounded-2xl text-blue-600">
                                        <FileText size={24} />
                                    </div>
                                    <div>
                                        <div className="text-xs font-black text-slate-400 uppercase tracking-widest mb-0.5">Dataset Density</div>
                                        <div className="text-2xl font-black text-slate-800">
                                            {uploadedData.rows.toLocaleString()} <span className="text-sm font-bold text-slate-400">Rows</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Preview Sections */}
                            <div className="space-y-4">
                                <div className="premium-card overflow-hidden">
                                    <button
                                        onClick={() => setShowPreview(!showPreview)}
                                        className="w-full flex items-center justify-between p-6 bg-white hover:bg-slate-50 transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="bg-indigo-50 p-2 rounded-lg text-indigo-500">
                                                <Layers size={20} />
                                            </div>
                                            <span className="font-black text-slate-800 uppercase tracking-wide text-sm text-left">Data Snapshot (First 20 Rows)</span>
                                        </div>
                                        <div className={`transition-transform duration-300 ${showPreview ? 'rotate-180' : ''}`}>
                                            <ChevronDown size={20} className="text-slate-400" />
                                        </div>
                                    </button>
                                    {showPreview && uploadedData.preview_data && (
                                        <div className="p-0 animate-fade-in">
                                            <div className="overflow-x-auto max-h-[400px]">
                                                <table className="min-w-full text-sm">
                                                    <thead className="bg-slate-50/80 backdrop-blur sticky top-0 z-10 border-b border-slate-100">
                                                        <tr>
                                                            <th className="px-6 py-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-tighter w-12 border-r border-slate-100">ID</th>
                                                            {uploadedData.columns.map((col, idx) => (
                                                                <th key={idx} className="px-6 py-4 text-left text-xs font-bold text-slate-700 whitespace-nowrap">
                                                                    {col}
                                                                </th>
                                                            ))}
                                                        </tr>
                                                    </thead>
                                                    <tbody className="bg-white divide-y divide-slate-100">
                                                        {uploadedData.preview_data.map((row, rowIdx) => (
                                                            <tr key={rowIdx} className="hover:bg-slate-50/50 transition-colors">
                                                                <td className="px-6 py-3 text-[10px] font-bold text-slate-300 border-r border-slate-100 bg-slate-50/30 font-mono italic">{rowIdx + 1}</td>
                                                                {uploadedData.columns.map((col, colIdx) => (
                                                                    <td key={colIdx} className="px-6 py-3 text-xs font-medium text-slate-600 whitespace-nowrap">
                                                                        {row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}
                                                                    </td>
                                                                ))}
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="premium-card overflow-hidden">
                                    <button
                                        onClick={() => setShowColumnInfo(!showColumnInfo)}
                                        className="w-full flex items-center justify-between p-6 bg-white hover:bg-slate-50 transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="bg-amber-50 p-2 rounded-lg text-amber-500">
                                                <Info size={20} />
                                            </div>
                                            <span className="font-black text-slate-800 uppercase tracking-wide text-sm text-left">Schema Intelligence</span>
                                        </div>
                                        <div className={`transition-transform duration-300 ${showColumnInfo ? 'rotate-180' : ''}`}>
                                            <ChevronDown size={20} className="text-slate-400" />
                                        </div>
                                    </button>
                                    {showColumnInfo && uploadedData.column_info && (
                                        <div className="p-0 animate-fade-in overflow-x-auto">
                                            <table className="min-w-full text-sm">
                                                <thead className="bg-slate-50/80 backdrop-blur border-b border-slate-100">
                                                    <tr>
                                                        <th className="px-6 py-4 text-left text-[10px] font-black text-slate-400 uppercase">Field</th>
                                                        <th className="px-6 py-4 text-left text-[10px] font-black text-slate-400 uppercase">Type</th>
                                                        <th className="px-6 py-4 text-left text-[10px] font-black text-slate-400 uppercase text-right">Null Density</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-slate-100 bg-white">
                                                    {uploadedData.column_info.map((col, idx) => (
                                                        <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                                                            <td className="px-6 py-4 text-xs font-black text-slate-800">{col.name}</td>
                                                            <td className="px-6 py-4">
                                                                <span className="px-2 py-0.5 rounded-full bg-slate-100 text-[10px] font-bold text-slate-500 uppercase">
                                                                    {col.type}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4 text-right">
                                                                <div className="flex flex-col items-end gap-1">
                                                                    <div className="text-xs font-bold text-slate-700">{col.null_percentage}%</div>
                                                                    <div className="w-20 h-1 bg-slate-100 rounded-full overflow-hidden">
                                                                        <div
                                                                            className={`h-full rounded-full ${parseFloat(col.null_percentage) > 10 ? 'bg-amber-400' : 'bg-emerald-400'}`}
                                                                            style={{ width: `${col.null_percentage}%` }}
                                                                        ></div>
                                                                    </div>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default UploadTab;

