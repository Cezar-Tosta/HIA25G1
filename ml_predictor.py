import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class NoShowPredictor:
    """Sistema simulado de predição de no-show"""
    
    def __init__(self):
        self.dados_dir = Path("./dados")
        self.pacientes_df = None
        self.consultas_df = None
        self._load_data()
    
    def _load_data(self):
        """Carrega dados dos CSVs"""
        try:
            self.pacientes_df = pd.read_csv(self.dados_dir / "pacientes.csv")
            if (self.dados_dir / "consultas.csv").exists():
                self.consultas_df = pd.read_csv(self.dados_dir / "consultas.csv")
            print(f"[ML Predictor] Dados carregados: {len(self.pacientes_df)} pacientes")
        except Exception as e:
            print(f"[ML Predictor] Erro ao carregar dados: {e}")
    
    def predict_individual(self, patient_id: int) -> Dict[str, Any]:
        """
        Prediz probabilidade de no-show para um paciente específico
        
        Returns:
            {
                'probabilidade': float,
                'paciente_info': dict,
                'fatores_risco': list,
                'recomendacoes': list
            }
        """
        
        if self.pacientes_df is None:
            return {'error': 'Dados não carregados'}
        
        # Buscar paciente
        paciente = self.pacientes_df[self.pacientes_df['id_paciente'] == patient_id]
        
        if len(paciente) == 0:
            return {'error': f'Paciente {patient_id} não encontrado'}
        
        paciente = paciente.iloc[0]
        
        # MODELO SIMPLIFICADO DE PREDIÇÃO
        # Em produção, usar modelo ML treinado
        
        prob = 0.3  # Base
        fatores = []
        
        # Idade
        if paciente['idade'] < 30:
            prob += 0.15
            fatores.append('Jovem (< 30 anos): +15%')
        elif paciente['idade'] > 70:
            prob += 0.10
            fatores.append('Idoso (> 70 anos): +10%')
        
        # Condições
        if paciente.get('tem_diabetes', False):
            prob -= 0.05
            fatores.append('Tem diabetes: -5% (pacientes crônicos faltam menos)')
        
        if paciente.get('tem_hipertensao', False):
            prob -= 0.05
            fatores.append('Tem hipertensão: -5%')
        
        # Plano de saúde
        if paciente.get('plano_saude', 'SUS') == 'SUS':
            prob += 0.10
            fatores.append('SUS: +10% (maior dificuldade de acesso)')
        
        # Limitar entre 0 e 1
        prob = max(0.05, min(0.95, prob))
        
        # Gerar recomendações
        recomendacoes = self._gerar_recomendacoes_individual(prob, paciente)
        
        return {
            'probabilidade': prob,
            'paciente_info': {
                'id': int(patient_id),
                'idade': int(paciente['idade']),
                'sexo': paciente['sexo'],
                'cidade': paciente.get('cidade', 'N/A'),
                'tem_diabetes': bool(paciente.get('tem_diabetes', False)),
                'tem_hipertensao': bool(paciente.get('tem_hipertensao', False)),
                'plano': paciente.get('plano_saude', 'SUS')
            },
            'fatores_risco': fatores,
            'recomendacoes': recomendacoes
        }
    
    def predict_batch(self, date: str) -> Dict[str, Any]:
        """
        Prediz no-show para todos pacientes de uma data
        
        Args:
            date: Data no formato 'YYYY-MM-DD'
            
        Returns:
            {
                'date': str,
                'total_pacientes': int,
                'taxa_media': float,
                'alto_risco': int,
                'medio_risco': int,
                'baixo_risco': int,
                'por_especialidade': dict,
                'detalhes': list
            }
        """
        
        # Simular consultas agendadas para aquela data
        # Em produção, buscar do banco de dados
        
        if self.pacientes_df is None:
            return {'error': 'Dados não carregados'}
        
        # Simular 20-30 pacientes agendados
        num_pacientes = np.random.randint(20, 31)
        pacientes_agendados = self.pacientes_df.sample(min(num_pacientes, len(self.pacientes_df)))
        
        detalhes = []
        probabilidades = []
        
        especialidades = ['Cardiologia', 'Clínica Geral', 'Ortopedia', 'Endocrinologia']
        
        for _, paciente in pacientes_agendados.iterrows():
            # Predição individual
            pred = self.predict_individual(paciente['id_paciente'])
            prob = pred['probabilidade']
            
            especialidade = np.random.choice(especialidades)
            
            detalhes.append({
                'id_paciente': int(paciente['id_paciente']),
                'nome': paciente.get('nome', f"Paciente {paciente['id_paciente']}"),
                'especialidade': especialidade,
                'probabilidade': prob,
                'risco': 'ALTO' if prob >= 0.6 else 'MEDIO' if prob >= 0.3 else 'BAIXO'
            })
            
            probabilidades.append(prob)
        
        # Calcular estatísticas
        taxa_media = np.mean(probabilidades)
        alto_risco = sum(1 for p in probabilidades if p >= 0.6)
        medio_risco = sum(1 for p in probabilidades if 0.3 <= p < 0.6)
        baixo_risco = sum(1 for p in probabilidades if p < 0.3)
        
        # Por especialidade
        df_detalhes = pd.DataFrame(detalhes)
        por_especialidade = {}
        
        for esp in df_detalhes['especialidade'].unique():
            esp_data = df_detalhes[df_detalhes['especialidade'] == esp]
            por_especialidade[esp] = {
                'total': len(esp_data),
                'taxa_media': float(esp_data['probabilidade'].mean()),
                'alto_risco': len(esp_data[esp_data['risco'] == 'ALTO'])
            }
        
        return {
            'date': date,
            'total_pacientes': len(detalhes),
            'taxa_media': float(taxa_media),
            'alto_risco': alto_risco,
            'medio_risco': medio_risco,
            'baixo_risco': baixo_risco,
            'por_especialidade': por_especialidade,
            'detalhes': detalhes[:10]  # Enviar apenas top 10 para não sobrecarregar
        }
    
    def _gerar_recomendacoes_individual(self, prob: float, paciente: pd.Series) -> List[str]:
        """Gera recomendações baseadas no risco"""
        
        recomendacoes = []
        
        if prob >= 0.6:
            recomendacoes.append("🔴 URGENTE: Ligar 48h antes + SMS 24h antes")
            recomendacoes.append("Oferecer remarcação facilitada")
            recomendacoes.append("Considerar auxílio transporte se aplicável")
        elif prob >= 0.3:
            recomendacoes.append("🟡 MODERADO: Enviar SMS 24h antes")
            recomendacoes.append("Monitorar resposta à confirmação")
        else:
            recomendacoes.append("🟢 BAIXO: Confirmação automática suficiente")
        
        return recomendacoes


    def predict_batch_range(self, date_start: str, date_end: str) -> Dict[str, Any]:
        """
        Prediz no-show para um intervalo de datas
        """
    
        if self.pacientes_df is None:
            return {'error': 'Dados não carregados'}
        
        # Calcular dias
        start = datetime.strptime(date_start, '%Y-%m-%d')
        end = datetime.strptime(date_end, '%Y-%m-%d')
        dias = (end - start).days + 1
    
        # Simular pacientes para todo o período
        num_pacientes_dia = np.random.randint(15, 25)
        total_pacientes = num_pacientes_dia * dias
        
        # Agregar predições
        all_details = []
        all_probs = []
    
        for dia in range(dias):
            data_consulta = start + timedelta(days=dia)
            pacientes_dia = self.pacientes_df.sample(min(num_pacientes_dia, len(self.pacientes_df)))
            
            for _, paciente in pacientes_dia.iterrows():
                pred = self.predict_individual(paciente['id_paciente'])
                prob = pred['probabilidade']
                
                all_details.append({
                    'id_paciente': int(paciente['id_paciente']),
                    'data': data_consulta.strftime('%Y-%m-%d'),
                    'probabilidade': prob,
                    'risco': 'ALTO' if prob >= 0.6 else 'MEDIO' if prob >= 0.3 else 'BAIXO'
                })
                all_probs.append(prob)
    
        # Estatísticas
        taxa_media = np.mean(all_probs)
        alto = sum(1 for p in all_probs if p >= 0.6)
        medio = sum(1 for p in all_probs if 0.3 <= p < 0.6)
        baixo = sum(1 for p in all_probs if p < 0.3)
    
        return {
            'date_start': date_start,
            'date_end': date_end,
            'dias': dias,
            'total_pacientes': len(all_details),
            'taxa_media': float(taxa_media),
            'alto_risco': alto,
            'medio_risco': medio,
            'baixo_risco': baixo,
            'por_especialidade': {},  # Pode adicionar depois
            'detalhes': all_details[:20]  # Top 20
        }
# Instância global
predictor = NoShowPredictor()