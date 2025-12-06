import os
import subprocess
import re
from typing import Generator, Tuple, Dict
import numpy as np

class MDSimulator:
    """
    Motor de simulación MD que automatiza el pipeline de GROMACS
    """
    
    def __init__(self, pdb_path: str, work_dir: str):
        self.pdb_path = pdb_path
        self.work_dir = work_dir
        os.makedirs(work_dir, exist_ok=True)
        
        # Archivos generados
        self.clean_pdb = os.path.join(work_dir, 'clean.pdb')
        self.processed_gro = os.path.join(work_dir, 'processed.gro')
        self.topol_top = os.path.join(work_dir, 'topol.top')
        
    def run_command(self, cmd: list, stdin_input: str = None) -> Tuple[str, str]:
        """Ejecuta comando de shell y retorna stdout, stderr"""
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE if stdin_input else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=stdin_input)
            return stdout, stderr
        except Exception as e:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{str(e)}")
    
    def clean_pdb(self) -> None:
        """Paso 1: Limpiar PDB (remover cristales de agua)"""
        with open(self.pdb_path, 'r') as f:
            lines = f.readlines()
        
        with open(self.clean_pdb, 'w') as f:
            for line in lines:
                if not line.startswith('HOH') and not line.startswith('HETATM'):
                    f.write(line)
    
    def pdb2gmx(self) -> None:
        """Paso 2: Generar topología con pdb2gmx"""
        cmd = [
            'gmx', 'pdb2gmx',
            '-f', self.clean_pdb,
            '-o', self.processed_gro,
            '-water', 'tip3p',
            '-ff', 'charmm36'
        ]
        # Seleccionar force field automáticamente: 1 para CHARMM36
        self.run_command(cmd, stdin_input='1\n1\n')
    
    def editconf(self) -> None:
        """Paso 3: Definir caja de simulación"""
        cmd = [
            'gmx', 'editconf',
            '-f', self.processed_gro,
            '-o', os.path.join(self.work_dir, 'newbox.gro'),
            '-c',
            '-d', '1.2',
            '-bt', 'cubic'
        ]
        self.run_command(cmd)
    
    def solvate(self) -> None:
        """Paso 4: Solvatar sistema"""
        cmd = [
            'gmx', 'solvate',
            '-cp', os.path.join(self.work_dir, 'newbox.gro'),
            '-cs', 'spc216.gro',
            '-o', os.path.join(self.work_dir, 'solv.gro'),
            '-p', self.topol_top
        ]
        self.run_command(cmd)
    
    def add_ions(self) -> None:
        """Paso 5: Añadir iones para neutralizar"""
        # Generar archivo de entrada para genion
        ions_mdp = os.path.join(self.work_dir, 'ions.mdp')
        with open(ions_mdp, 'w') as f:
            f.write('; ions.mdp\nintegrator = steep\nnsteps = 50\n')
        
        # Preparar sistema
        cmd_grompp = [
            'gmx', 'grompp',
            '-f', ions_mdp,
            '-c', os.path.join(self.work_dir, 'solv.gro'),
            '-p', self.topol_top,
            '-o', os.path.join(self.work_dir, 'ions.tpr'),
            '-maxwarn', '1'
        ]
        self.run_command(cmd_grompp)
        
        # Añadir iones (grupo 13 = SOL)
        cmd_genion = [
            'gmx', 'genion',
            '-s', os.path.join(self.work_dir, 'ions.tpr'),
            '-o', os.path.join(self.work_dir, 'solv_ions.gro'),
            '-p', self.topol_top,
            '-pname', 'NA',
            '-nname', 'CL',
            '-neutral'
        ]
        self.run_command(cmd_genion, stdin_input='13\n')
    
    def energy_minimization(self) -> None:
        """Paso 6: Minimización de energía"""
        em_mdp = os.path.join(self.work_dir, 'em.mdp')
        with open(em_mdp, 'w') as f:
            f.write("""
integrator  = steep
nsteps      = 5000
emtol       = 1000.0
emstep      = 0.01
""")
        
        cmd_grompp = [
            'gmx', 'grompp',
            '-f', em_mdp,
            '-c', os.path.join(self.work_dir, 'solv_ions.gro'),
            '-p', self.topol_top,
            '-o', os.path.join(self.work_dir, 'em.tpr'),
            '-maxwarn', '1'
        ]
        self.run_command(cmd_grompp)
        
        cmd_mdrun = [
            'gmx', 'mdrun',
            '-v',
            '-deffnm', os.path.join(self.work_dir, 'em')
        ]
        self.run_command(cmd_mdrun)
    
    def nvt_equilibration(self) -> None:
        """Paso 7: Equilibración NVT"""
        nvt_mdp = os.path.join(self.work_dir, 'nvt.mdp')
        with open(nvt_mdp, 'w') as f:
            f.write("""
integrator  = md
nsteps      = 50000
dt          = 0.002
tcoupl      = V-rescale
ref_t       = 300
tau_t       = 0.1
""")
        
        cmd_grompp = [
            'gmx', 'grompp',
            '-f', nvt_mdp,
            '-c', os.path.join(self.work_dir, 'em.gro'),
            '-p', self.topol_top,
            '-o', os.path.join(self.work_dir, 'nvt.tpr'),
            '-maxwarn', '2'
        ]
        self.run_command(cmd_grompp)
        
        cmd_mdrun = [
            'gmx', 'mdrun',
            '-deffnm', os.path.join(self.work_dir, 'nvt')
        ]
        self.run_command(cmd_mdrun)
    
    def npt_equilibration(self) -> None:
        """Paso 8: Equilibración NPT"""
        npt_mdp = os.path.join(self.work_dir, 'npt.mdp')
        with open(npt_mdp, 'w') as f:
            f.write("""
integrator  = md
nsteps      = 250000
dt          = 0.002
pcoupl      = Parrinello-Rahman
ref_p       = 1.0
""")
        
        cmd_grompp = [
            'gmx', 'grompp',
            '-f', npt_mdp,
            '-c', os.path.join(self.work_dir, 'nvt.gro'),
            '-t', os.path.join(self.work_dir, 'nvt.cpt'),
            '-p', self.topol_top,
            '-o', os.path.join(self.work_dir, 'npt.tpr'),
            '-maxwarn', '2'
        ]
        self.run_command(cmd_grompp)
        
        cmd_mdrun = [
            'gmx', 'mdrun',
            '-deffnm', os.path.join(self.work_dir, 'npt')
        ]
        self.run_command(cmd_mdrun)
    
    def production_md(self) -> None:
        """Paso 9: Simulación de producción (10 ns)"""
        md_mdp = os.path.join(self.work_dir, 'md.mdp')
        with open(md_mdp, 'w') as f:
            f.write("""
integrator  = md
nsteps      = 5000000
dt          = 0.002
nstxout     = 5000
""")
        
        cmd_grompp = [
            'gmx', 'grompp',
            '-f', md_mdp,
            '-c', os.path.join(self.work_dir, 'npt.gro'),
            '-t', os.path.join(self.work_dir, 'npt.cpt'),
            '-p', self.topol_top,
            '-o', os.path.join(self.work_dir, 'md.tpr'),
            '-maxwarn', '2'
        ]
        self.run_command(cmd_grompp)
        
        cmd_mdrun = [
            'gmx', 'mdrun',
            '-deffnm', os.path.join(self.work_dir, 'md'),
            '-nb', 'cpu'  # Para compatibilidad
        ]
        self.run_command(cmd_mdrun)
    
    def analyze_rmsd(self) -> None:
        """Análisis: RMSD"""
        cmd = [
            'gmx', 'rms',
            '-s', os.path.join(self.work_dir, 'md.tpr'),
            '-f', os.path.join(self.work_dir, 'md.xtc'),
            '-o', os.path.join(self.work_dir, 'rmsd.xvg'),
            '-tu', 'ns'
        ]
        self.run_command(cmd, stdin_input='4\n4\n')  # Backbone
    
    def analyze_gyrate(self) -> None:
        """Análisis: Radio de gyration"""
        cmd = [
            'gmx', 'gyrate',
            '-s', os.path.join(self.work_dir, 'md.tpr'),
            '-f', os.path.join(self.work_dir, 'md.xtc'),
            '-o', os.path.join(self.work_dir, 'gyrate.xvg')
        ]
        self.run_command(cmd, stdin_input='1\n')  # Protein
    
    def run_full_pipeline(self) -> Generator[Tuple[str, int], None, None]:
        """Ejecuta pipeline completo con yields de progreso"""
        steps = [
            ("Limpiando estructura PDB...", self.clean_pdb),
            ("Generando topología (pdb2gmx)...", self.pdb2gmx),
            ("Definiendo caja de simulación...", self.editconf),
            ("Solvatando sistema...", self.solvate),
            ("Añadiendo iones...", self.add_ions),
            ("Minimización de energía...", self.energy_minimization),
            ("Equilibración NVT...", self.nvt_equilibration),
            ("Equilibración NPT...", self.npt_equilibration),
            ("Producción MD (10 ns)...", self.production_md),
            ("Analizando RMSD...", self.analyze_rmsd),
            ("Analizando radio de gyration...", self.analyze_gyrate),
        ]
        
        for i, (msg, func) in enumerate(steps):
            yield msg, int((i / len(steps)) * 100)
            func()
        
        yield "Simulación completada!", 100
    
    def get_results(self) -> Dict:
        """Parsear y retornar resultados"""
        results = {}
        
        # Parsear RMSD
        rmsd_file = os.path.join(self.work_dir, 'rmsd.xvg')
        if os.path.exists(rmsd_file):
            rmsd_data = self._parse_xvg(rmsd_file)
            results['rmsd'] = rmsd_data
        
        # Parsear Gyrate
        gyrate_file = os.path.join(self.work_dir, 'gyrate.xvg')
        if os.path.exists(gyrate_file):
            gyrate_data = self._parse_xvg(gyrate_file)
            results['gyrate'] = gyrate_data
        
        return results
    
    def _parse_xvg(self, filepath: str) -> list:
        """Parser para archivos XVG de GROMACS"""
        data = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('#') or line.startswith('@'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    data.append({
                        'time': float(parts[0]),
                        'value': float(parts[1])
                    })
        return data