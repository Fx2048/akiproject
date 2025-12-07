import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Upload, Play, Loader, Download } from 'lucide-react';
import './index.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [simId, setSimId] = useState(null);
  const [pdbFile, setPdbFile] = useState(null);
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/status/${id}`);
        const data = response.data;
        
        setStatus(data.status);
        setProgress(data.progress || 0);
        setLogs(data.logs || []);
        
        if (data.status === 'completed') {
          setResults(data.results);
          clearInterval(interval);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          alert('Simulación falló: ' + data.error);
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    }, 2000);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !file.name.endsWith('.pdb')) {
      alert('Sube un archivo PDB válido');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData);
      setSimId(response.data.sim_id);
      setPdbFile(file);
      setStatus('ready');
    } catch (error) {
      alert('Error al subir archivo: ' + error.message);
    }
  };

  const startSimulation = async () => {
    try {
      await axios.post(`${API_URL}/simulate/${simId}`);
      setStatus('running');
      pollStatus(simId);
    } catch (error) {
      alert('Error al iniciar simulación: ' + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8">
          Simulador MD - GROMACS
        </h1>

        <div className="bg-slate-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Cargar PDB</h2>
          <input
            type="file"
            accept=".pdb"
            onChange={handleUpload}
            className="mb-4"
          />
          {pdbFile && (
            <p className="text-green-400">✓ {pdbFile.name}</p>
          )}
          <button
            onClick={startSimulation}
            disabled={!simId || status === 'running'}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-2 rounded mt-4"
          >
            <Play className="inline mr-2" size={16} />
            Iniciar Simulación
          </button>
        </div>

        {status === 'running' && (
          <div className="bg-slate-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">
              <Loader className="inline animate-spin mr-2" />
              Progreso: {progress}%
            </h2>
            <div className="bg-slate-900 p-4 rounded h-64 overflow-y-auto font-mono text-sm">
              {logs.map((log, i) => (
                <div key={i} className="text-green-400">
                  {log.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {results && (
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Resultados</h2>
            <pre className="bg-slate-900 p-4 rounded overflow-auto">
              {JSON.stringify(results, null, 2)}
            </pre>
            <button
              onClick={() => {
                const blob = new Blob([JSON.stringify(results, null, 2)]);
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'results.json';
                a.click();
              }}
              className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded mt-4"
            >
              <Download className="inline mr-2" size={16} />
              Descargar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;