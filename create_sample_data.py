import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

def create_sample_csvs():
    """Cria arquivos CSV de exemplo"""
    
    output_dir = Path("./dados")
    output_dir.mkdir(exist_ok=True)
    
    # 1. PACIENTES
    print("Criando pacientes.csv...")
    pacientes = pd.DataFrame({
        'id_paciente': range(1, 101),
        'nome': [f"Paciente {i}" for i in range(1, 101)],
        'idade': np.random.randint(18, 85, 100),
        'sexo': np.random.choice(['M', 'F'], 100),
        'cidade': np.random.choice(['Rio de Janeiro', 'Niterói', 'São Gonçalo'], 100),
        'tem_diabetes': np.random.choice([True, False], 100, p=[0.15, 0.85]),
        'tem_hipertensao': np.random.choice([True, False], 100, p=[0.25, 0.75]),
        'plano_saude': np.random.choice(['SUS', 'Privado'], 100, p=[0.7, 0.3])
    })
    pacientes.to_csv(output_dir / 'pacientes.csv', index=False)
    
    # 2. CONSULTAS
    print("Criando consultas.csv...")
    consultas = []
    especialidades = ['Clínica Geral', 'Cardiologia', 'Endocrinologia', 'Ortopedia', 'Pediatria']
    status_opcoes = ['Realizada', 'Faltou', 'Cancelada', 'Remarcada']
    
    for i in range(1, 501):
        data_base = datetime.now() - timedelta(days=random.randint(1, 90))
        consultas.append({
            'id_consulta': i,
            'id_paciente': random.randint(1, 100),
            'especialidade': random.choice(especialidades),
            'data': data_base.strftime('%Y-%m-%d'),
            'status': random.choice(status_opcoes),
            'custo': round(random.uniform(80, 200), 2)
        })
    
    df_consultas = pd.DataFrame(consultas)
    df_consultas.to_csv(output_dir / 'consultas.csv', index=False)
    
    # 3. MEDICAMENTOS
    print("Criando medicamentos.csv...")
    medicamentos = pd.DataFrame({
        'id_medicamento': range(1, 51),
        'nome': [f"Medicamento {i}" for i in range(1, 51)],
        'tipo': np.random.choice(['Antibiótico', 'Anti-hipertensivo', 'Analgésico', 'Antidiabético'], 50),
        'estoque': np.random.randint(0, 500, 50),
        'preco_unitario': np.round(np.random.uniform(5, 150, 50), 2),
        'requer_receita': np.random.choice([True, False], 50, p=[0.6, 0.4])
    })
    medicamentos.to_csv(output_dir / 'medicamentos.csv', index=False)
    
    # 4. CUSTOS
    print("Criando custos.csv...")
    meses = pd.date_range(start='2024-01-01', end='2024-09-01', freq='MS')
    custos = []
    
    for mes in meses:
        custos.append({
            'mes': mes.strftime('%Y-%m'),
            'categoria': 'Pessoal',
            'valor': round(random.uniform(150000, 200000), 2)
        })
        custos.append({
            'mes': mes.strftime('%Y-%m'),
            'categoria': 'Medicamentos',
            'valor': round(random.uniform(30000, 50000), 2)
        })
        custos.append({
            'mes': mes.strftime('%Y-%m'),
            'categoria': 'Infraestrutura',
            'valor': round(random.uniform(20000, 35000), 2)
        })
    
    df_custos = pd.DataFrame(custos)
    df_custos.to_csv(output_dir / 'custos.csv', index=False)
    
    print("\n✅ Arquivos CSV criados em ./dados/")
    print(f"  - pacientes.csv: {len(pacientes)} registros")
    print(f"  - consultas.csv: {len(consultas)} registros")
    print(f"  - medicamentos.csv: {len(medicamentos)} registros")
    print(f"  - custos.csv: {len(custos)} registros")

if __name__ == "__main__":
    create_sample_csvs()