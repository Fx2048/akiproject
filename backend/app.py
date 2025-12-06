from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import subprocess
import json
import threading
from datetime import datetime
import uuid
from md_engine import MDSimulator

app = Flask(__name__)
CORS(app)

# Configuración
UPLOAD_FOLDER = '/tmp/md_uploads'
RESULTS_FOLDER = '/tmp/md_results'
ALLOWED_EXTENSIONS = {'pdb'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Estado de simulaciones
simulations = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/upload', methods=['POST'])
def upload_pdb():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    sim_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, f"{sim_id}_{filename}")
    file.save(filepath)
    
    simulations[sim_id] = {
        'status': 'uploaded',
        'filename': filename,
        'filepath': filepath,
        'progress': 0,
        'logs': [],
        'created': datetime.now().isoformat()
    }
    
    return jsonify({'sim_id': sim_id, 'filename': filename})

@app.route('/simulate/<sim_id>', methods=['POST'])
def start_simulation(sim_id):
    if sim_id not in simulations:
        return jsonify({'error': 'Simulation not found'}), 404
    
    if simulations[sim_id]['status'] == 'running':
        return jsonify({'error': 'Simulation already running'}), 400
    
    # Iniciar simulación en background
    thread = threading.Thread(target=run_md_simulation, args=(sim_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Simulation started', 'sim_id': sim_id})

def run_md_simulation(sim_id):
    sim = simulations[sim_id]
    sim['status'] = 'running'
    
    try:
        simulator = MDSimulator(
            sim['filepath'],
            os.path.join(RESULTS_FOLDER, sim_id)
        )
        
        # Ejecutar pipeline completo
        for step, progress in simulator.run_full_pipeline():
            sim['logs'].append({
                'timestamp': datetime.now().isoformat(),
                'message': step
            })
            sim['progress'] = progress
        
        # Guardar resultados
        sim['status'] = 'completed'
        sim['results'] = simulator.get_results()
        
    except Exception as e:
        sim['status'] = 'failed'
        sim['error'] = str(e)
        sim['logs'].append({
            'timestamp': datetime.now().isoformat(),
            'message': f'ERROR: {str(e)}'
        })

@app.route('/status/<sim_id>', methods=['GET'])
def get_status(sim_id):
    if sim_id not in simulations:
        return jsonify({'error': 'Simulation not found'}), 404
    
    return jsonify(simulations[sim_id])

@app.route('/results/<sim_id>', methods=['GET'])
def get_results(sim_id):
    if sim_id not in simulations:
        return jsonify({'error': 'Simulation not found'}), 404
    
    sim = simulations[sim_id]
    if sim['status'] != 'completed':
        return jsonify({'error': 'Simulation not completed'}), 400
    
    return jsonify(sim['results'])

@app.route('/download/<sim_id>/<filename>', methods=['GET'])
def download_file(sim_id, filename):
    filepath = os.path.join(RESULTS_FOLDER, sim_id, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)