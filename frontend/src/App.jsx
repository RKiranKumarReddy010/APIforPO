import React, { useState, useEffect } from 'react';
import { Upload, FileCheck, BarChart2, Activity, TrendingUp, Database, Download, Box, Zap } from 'lucide-react';
import UploadTab from './components/UploadTab';
import ValidationTab from './components/ValidationTab';
import AnalysisTab from './components/AnalysisTab';
import SafetyStockTab from './components/SafetyStockTab';
import SimulationTab from './components/SimulationTab';
import PrimaryDataTab from './components/PrimaryDataTab';
import ExportTab from './components/ExportTab';
import { getHealth, getConfig } from './api';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadData, setUploadData] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [processedStats, setProcessedStats] = useState(null);
  const [processedCharts, setProcessedCharts] = useState(null);
  const [safetyStockResults, setSafetyStockResults] = useState(null);
  const [simulationData, setSimulationData] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');
  const [appConfig, setAppConfig] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        await getHealth();
        setServerStatus('online');
        const configRes = await getConfig();
        setAppConfig(configRes.data);
      } catch (err) {
        setServerStatus('offline');
      }
    };
    fetchData();
  }, []);

  const handleUploadSuccess = (data, shouldNavigate = false) => {
    setUploadData(data);
    if (shouldNavigate) setActiveTab('validation');
  };

  const tabs = [
    { id: 'upload', label: 'Upload', icon: Upload, color: 'text-blue-500' },
    { id: 'validation', label: 'Validation', icon: FileCheck, color: 'text-green-500' },
    { id: 'analysis', label: 'Analysis', icon: Activity, color: 'text-purple-500' },
    { id: 'safetystock', label: 'Safety Stock', icon: TrendingUp, color: 'text-orange-500' },
    { id: 'simulation', label: 'Simulation', icon: BarChart2, color: 'text-indigo-500' },
    { id: 'primarydata', label: 'Primary Data', icon: Database, color: 'text-cyan-500' },
    { id: 'export', label: 'Export', icon: Download, color: 'text-emerald-500' }
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-20">
      {/* Premium Header */}
      <header className="relative bg-white border-b border-gray-100 overflow-hidden pt-12 pb-16">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600"></div>
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-xs font-bold uppercase tracking-wider mb-4 animate-fade-in shadow-sm border border-blue-100">
              <Zap size={14} className="fill-current" />
              Next-Gen Inventory Intelligence
            </div>

            <h1 className="text-5xl font-black text-slate-900 tracking-tight mb-4 animate-fade-in drop-shadow-sm">
              <span className="gradient-text">Inventory</span> Planning Dashboard
            </h1>

            <p className="max-w-2xl text-lg text-slate-500 font-medium leading-relaxed mb-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
              Simulate volatility, optimize safety stock, and automate reorder points with precision data engineering.
            </p>

            <div className="flex items-center gap-4 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className={`flex items-center gap-2 px-4 py-1.5 rounded-2xl text-sm font-bold shadow-sm border transition-all duration-500 ${serverStatus === 'online'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                : 'bg-rose-50 text-rose-700 border-rose-100'
                }`}>
                <span className={`w-2.5 h-2.5 rounded-full ${serverStatus === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                  }`}></span>
                System {serverStatus === 'online' ? 'Operational' : 'Disconnected'}
              </div>
              {appConfig && (
                <div className="px-4 py-1.5 rounded-2xl bg-slate-100 text-slate-600 text-sm font-bold border border-slate-200">
                  v{appConfig.version || '1.0.0'}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 -mt-10 relative z-20">
        {/* Modern Tab Navigation */}
        <div className="glass-panel p-2 rounded-[2rem] mb-10 border border-white/40 shadow-xl overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-2 p-1 min-w-max">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2.5 px-6 py-3.5 rounded-[1.5rem] font-bold text-sm transition-all duration-300 group nav-tab ${isActive
                    ? 'bg-white text-slate-900 shadow-sm active ring-1 ring-slate-100'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-white/50'
                    }`}
                >
                  <Icon size={18} className={`${isActive ? tab.color : 'text-slate-400 group-hover:text-slate-600'} transition-colors`} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content Area */}
        <main className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <div className="premium-card p-1">
            {activeTab === 'upload' && <UploadTab onSuccess={handleUploadSuccess} />}
            {activeTab === 'validation' && <ValidationTab uploadData={uploadData} onValidate={setValidationResult} />}
            {activeTab === 'analysis' && <AnalysisTab uploadData={uploadData} onAnalyze={(stats, charts) => { setProcessedStats(stats); setProcessedCharts(charts); }} />}
            {activeTab === 'safetystock' && <SafetyStockTab uploadData={uploadData} analysisData={processedStats} appConfig={appConfig} onCalculate={setSafetyStockResults} />}
            {activeTab === 'simulation' && <SimulationTab uploadData={uploadData} safetyStockData={safetyStockResults} appConfig={appConfig} onSimulate={setSimulationData} />}
            {activeTab === 'primarydata' && <PrimaryDataTab uploadData={uploadData} processedData={processedStats} charts={processedCharts} safetyStockData={safetyStockResults} />}
            {activeTab === 'export' && <ExportTab uploadData={uploadData} processedData={processedStats} charts={processedCharts} safetyStockData={safetyStockResults} simulationData={simulationData} />}
          </div>
        </main>
      </div>

      {/* Floating Status Bar Mockup */}
      <div className="fixed bottom-6 right-6 z-50">
        <div className="glass-panel px-4 py-2 rounded-full border border-white/60 shadow-lg flex items-center gap-3">
          <div className="bg-slate-100 p-1.5 rounded-full">
            <Box size={14} className="text-slate-600" />
          </div>
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
            Node: PO-Node-01
          </span>
        </div>
      </div>
    </div>
  );
}

export default App;

