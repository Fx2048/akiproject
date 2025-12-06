# Simulador de Dinámica Molecular Web

Sistema completo de simulación molecular basado en GROMACS con visualización 3D interactiva.

## 🚀 Características

- ✅ Pipeline automatizado de GROMACS (limpieza → topología → solvatación → minimización → equilibración → producción)
- ✅ Visualización 3D interactiva en tiempo real
- ✅ Análisis automático (RMSD, radio de gyration, energía)
- ✅ API REST para control remoto
- ✅ Interfaz web responsiva

## 🛠️ Stack Tecnológico

- **Backend**: Flask + Python 3.9+
- **Motor MD**: GROMACS 2023.1
- **Frontend**: React + Three.js
- **Contenedores**: Docker
- **Deployment**: Render.com

## 📦 Instalación Local

### Con Docker (Recomendado)
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/md-simulator-web.git
cd md-simulator-web

# Construir y ejecutar
docker-compose up --build

# Acceder en http://localhost:5000
```

### Sin Docker
```bash
# Instalar GROMACS
sudo apt-get install gromacs

# Instalar dependencias Python
cd backend
pip install -r requirements.txt

# Ejecutar servidor
python app.py
```

## 🌐 Deploy en Render.com

### 1. Preparar Repositorio GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/md-simulator-web.git
git push -u origin main
```

### 2. Configurar Render

1. Ve a [Render.com](https://render.com) y crea una cuenta
2. Click en "New +" → "Web Service"
3. Conecta tu repositorio GitHub
4. Configuración:
   - **Name**: md-simulator
   - **Environment**: Docker
   - **Region**: Oregon (US West)
   - **Branch**: main
   - **Dockerfile Path**: ./backend/Dockerfile
   - **Instance Type**: Free (o Starter para mejor rendimiento)

5. Variables de entorno (opcional):
```
   FLASK_ENV=production
   MAX_SIMULATION_TIME=600
```

6. Click "Create Web Service"

### 3. Limitaciones del Free Tier

⚠️ **Importante**: El free tier de Render tiene limitaciones:

- 512 MB RAM (suficiente para proteínas pequeñas <100 residuos)
- CPU compartida
- El servicio "hiberna" después de 15 min de inactividad
- 750 horas/mes gratis

**Recomendaciones**:
- Reduce `nsteps` en los archivos MDP para simulaciones más rápidas
- Usa proteínas pequeñas para pruebas (ej: 1AKI - 74 residuos)
- Para simulaciones largas, considera el plan Starter ($7/mes)

## 📚 Uso

### API Endpoints
```bash
# Subir PDB
curl -X POST -F "file=@protein.pdb" http://localhost:5000/upload

# Iniciar simulación
curl -X POST http://localhost:5000/simulate/{sim_id}

# Consultar estado
curl http://localhost:5000/status/{sim_id}

# Descargar resultados
curl http://localhost:5000/results/{sim_id}
```

### Interfaz Web

1. Accede a la URL de tu servicio Render
2. Sube un archivo PDB
3. Click en "Iniciar Simulación"
4. Observa el progreso en tiempo real
5. Visualiza y descarga resultados

## 🧪 Ejemplos de Proteínas

Prueba con estas proteínas pequeñas del PDB:

- **1AKI** (74 residuos) - Ovomucoid third domain
- **1UBQ** (76 residuos) - Ubiquitin
- **1VII** (36 residuos) - Villin headpiece subdomain
```bash
# Descargar ejemplo
wget https://files.rcsb.org/download/1AKI.pdb
```

## 🔧 Configuración Avanzada

### Ajustar Parámetros de Simulación

Edita `md_engine.py` para modificar:

- Force field (línea 47): `charmm36`, `amber99sb-ildn`, `oplsaa`
- Modelo de agua (línea 48): `tip3p`, `tip4p`, `spc`
- Tiempo de simulación (ajusta `nsteps` en MDPs)
- Distancia de caja (línea 61): `-d 1.0` (más pequeño = más rápido)

### Optimización para Free Tier
```python
# En md_engine.py, reduce los pasos:

# Minimización: 5000 → 1000 pasos
nsteps = 1000

# NVT: 50000 → 10000 pasos (20 ps)
nsteps = 10000

# NPT: 250000 → 50000 pasos (100 ps)
nsteps = 50000

# Producción: 5000000 → 500000 pasos (1 ns)
nsteps = 500000
```

## 🐛 Troubleshooting

### Error: "Out of Memory"

Reduce el tamaño de la simulación:
- Usa proteínas más pequeñas
- Reduce la caja de simulación (`-d 0.8`)
- Disminuye los pasos de producción

### Error: "GROMACS command not found"

Verifica que GROMACS esté instalado en el contenedor:
```bash
docker exec -it <container> gmx --version
```

### Simulación muy lenta

Para el free tier:
- Reduce drásticamente `nsteps`
- Usa `-nb cpu` en mdrun
- Considera usar el plan Starter de Render

## 📊 Análisis Avanzado

Para análisis adicionales, agrega a `md_engine.py`:
```python
def analyze_hbonds(self):
    """Análisis de enlaces de hidrógeno"""
    cmd = [
        'gmx', 'hbond',
        '-s', os.path.join(self.work_dir, 'md.tpr'),
        '-f', os.path.join(self.work_dir, 'md.xtc'),
        '-num', os.path.join(self.work_dir, 'hbnum.xvg')
    ]
    self.run_command(cmd, stdin_input='1\n1\n')
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver archivo LICENSE

## 🙏 Créditos

- GROMACS: https://www.gromacs.org
- Basado en tutoriales de Justin Lemkul
- Visualización inspirada en PyMOL y NGL Viewer

## 📧 Contacto

Para preguntas o soporte: [tu-email@ejemplo.com]