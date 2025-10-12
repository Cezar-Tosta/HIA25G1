# ==============================================================================
# SEÇÃO 0: IMPORTAÇÕES E CONFIGURAÇÃO
# ==============================================================================
import pandas as pd
import numpy as np
import glob
import os
import lightgbm as lgb
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, log_loss

# --- Configuração ---
# O script espera que a pasta 'data' esteja no mesmo diretório que ele.
caminho_para_pasta = '.' 

# ==============================================================================
# SEÇÃO 1: CARREGAMENTO DOS DADOS
# ==============================================================================
print("--- [SEÇÃO 1] Iniciando Carregamento dos Dados ---")

def carregar_dataframe(caminho_base, nome_base):
    padrao_busca = os.path.join(caminho_base, 'data', f"{nome_base}-*.parquet")
    lista_de_arquivos = glob.glob(padrao_busca)
    
    if not lista_de_arquivos:
        print(f"Aviso: Nenhum arquivo encontrado para '{nome_base}'")
        return None
        
    lista_dfs = [pd.read_parquet(arquivo) for arquivo in lista_de_arquivos]
    df_completo = pd.concat(lista_dfs, ignore_index=True)
    
    print(f"DataFrame '{nome_base}' carregado com {len(df_completo):,} linhas.")
    return df_completo

# Dicionário para armazenar todos os DataFrames
dataframes = {}

# Lista de todas as tabelas base encontradas
nomes_tabelas = [
    'marcacao', 'oferta_programada', 'profissional_historico', 'solicitacao',
    'cids', 'equipamento_historico', 'habilitacao_historico', 'leito_historico',
    'procedimento', 'tempo_espera', 'unidade_historico'
]

for nome_tabela in nomes_tabelas:
    dataframes[nome_tabela] = carregar_dataframe(caminho_para_pasta, nome_tabela)

# Atribuindo a variáveis mais fáceis de usar
dfMarcacao = dataframes['marcacao']
dfUnidadeHistorico = dataframes['unidade_historico']
dfProcedimento = dataframes['procedimento']
dfCids = dataframes['cids']

dfCids.rename(columns={'cid': 'cid_categoria_descricao'}, inplace=True)  # Garantir consistência na nomenclatura


print("\n--- [SEÇÃO 1] Carregamento de Dados Concluído ---\n")


# ==============================================================================
# SEÇÃO 2: DEFINIÇÃO DA VARIÁVEL ALVO (Y) - LÓGICA CORRIGIDA
# ==============================================================================
print("--- [SEÇÃO 2] Iniciando Definição da Variável Alvo ---")

# A fonte da verdade para o absenteísmo é o status da solicitação.
condicao_absenteismo = (dfMarcacao['solicitacao_status'] == 'AGENDAMENTO / FALTA / EXECUTANTE')
dfMarcacao['alvo_absenteismo'] = condicao_absenteismo.astype(int)

# Filtramos o dataset para incluir apenas os resultados finais que nos interessam:
# Pacientes que compareceram ou que faltaram.
status_relevantes = [
    'AGENDAMENTO / CONFIRMADO / EXECUTANTE', # Classe 0 (Compareceu)
    'AGENDAMENTO / FALTA / EXECUTANTE'       # Classe 1 (Faltou)
]
df_modelagem = dfMarcacao[dfMarcacao['solicitacao_status'].isin(status_relevantes)].copy()

# Verificação
print(f"Total de agendamentos relevantes para análise: {len(df_modelagem):,}")
print("Distribuição da variável alvo:")
print(df_modelagem['alvo_absenteismo'].value_counts())
print(f"Taxa de Absenteísmo no dataset: {df_modelagem['alvo_absenteismo'].mean():.2%}")
print("\n--- [SEÇÃO 2] Definição da Variável Alvo Concluída ---\n")


# ==============================================================================
# SEÇÃO 3: ENGENHARIA DE ATRIBUTOS (FEATURE ENGINEERING)
# ==============================================================================
print("--- [SEÇÃO 3] Iniciando Engenharia de Atributos ---")

# A. Fatores Temporais
df_modelagem['data_solicitacao'] = pd.to_datetime(df_modelagem['data_solicitacao'], errors='coerce')
df_modelagem['data_marcacao'] = pd.to_datetime(df_modelagem['data_marcacao'], errors='coerce')
df_modelagem['lead_time_dias'] = (df_modelagem['data_marcacao'] - df_modelagem['data_solicitacao']).dt.days
df_modelagem['lead_time_dias'] = df_modelagem['lead_time_dias'].clip(lower=0)
df_modelagem['dia_semana'] = df_modelagem['data_marcacao'].dt.dayofweek
df_modelagem['hora_dia'] = df_modelagem['data_marcacao'].dt.hour
df_modelagem['mes'] = df_modelagem['data_marcacao'].dt.month

# B. Histórico do Paciente
df_modelagem = df_modelagem.sort_values(by=['paciente_id', 'data_marcacao'])
grouped = df_modelagem.groupby('paciente_id')
df_modelagem['num_agendamentos_anteriores'] = grouped.cumcount()
df_modelagem['num_faltas_anteriores'] = grouped['alvo_absenteismo'].cumsum().shift(1).fillna(0)
df_modelagem['taxa_absenteismo_anterior'] = np.where(
    df_modelagem['num_agendamentos_anteriores'] > 0,
    df_modelagem['num_faltas_anteriores'] / df_modelagem['num_agendamentos_anteriores'],
    0
)

# C. Fatores Geográficos
unidades = dfUnidadeHistorico.sort_values(['ano', 'mes'], ascending=False).drop_duplicates('unidade_id_cnes')
df_modelagem = pd.merge(df_modelagem, unidades[['unidade_id_cnes', 'unidade_latitude', 'unidade_longitude']], left_on='unidade_solicitante_id_cnes', right_on='unidade_id_cnes', how='left')
df_modelagem = pd.merge(df_modelagem, unidades[['unidade_id_cnes', 'unidade_latitude', 'unidade_longitude']], left_on='unidade_executante_id_cnes', right_on='unidade_id_cnes', how='left', suffixes=('_solicitante', '_executante'))

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

df_modelagem['distancia_km'] = haversine_distance(df_modelagem['unidade_latitude_solicitante'], df_modelagem['unidade_longitude_solicitante'], df_modelagem['unidade_latitude_executante'], df_modelagem['unidade_longitude_executante'])

# D. Fatores Clínicos
df_modelagem = pd.merge(df_modelagem, dfProcedimento[['procedimento_sisreg_id', 'procedimento_especialidade']], on='procedimento_sisreg_id', how='left')
df_modelagem = pd.merge(df_modelagem, dfCids[['cid_id', 'cid_categoria_descricao']], left_on='cid_agendado_id', right_on='cid_id', how='left')

print("Novos atributos criados com sucesso.")
print("\n--- [SEÇÃO 3] Engenharia de Atributos Concluída ---\n")


# ==============================================================================
# SEÇÃO 4: MODELAGEM (TREINAMENTO E AVALIAÇÃO)
# ==============================================================================
print("--- [SEÇÃO 4] Iniciando Modelagem ---")

# 1. Definição de Variáveis e Divisão dos Dados
features_para_usar = [
    'lead_time_dias', 'dia_semana', 'hora_dia', 'mes', 'num_agendamentos_anteriores',
    'taxa_absenteismo_anterior', 'distancia_km', 'paciente_sexo', 'paciente_faixa_etaria',
    'paciente_avisado', 'solicitacao_risco', 'vaga_consumida_tp',
    'procedimento_especialidade', 'cid_categoria_descricao'
]
alvo = 'alvo_absenteismo'

# Tratamento de nulos simples antes de dividir
df_modelagem.dropna(subset=['data_marcacao'], inplace=True) # Essencial para divisão temporal se necessária

X = df_modelagem[features_para_usar]
y = df_modelagem[alvo]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Dados divididos em {len(X_train):,} para treino e {len(X_test):,} para teste.")

# 2. Pipeline de Pré-processamento e Modelo Baseline (Regressão Logística)
numerical_features = X.select_dtypes(include=np.number).columns.tolist()
categorical_features = X.select_dtypes(exclude=np.number).columns.tolist()

numeric_transformer = Pipeline(steps=[('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
categorical_transformer = Pipeline(steps=[('imputer', SimpleImputer(strategy='constant', fill_value='missing')), ('onehot', OneHotEncoder(handle_unknown='ignore'))])
preprocessor = ColumnTransformer(transformers=[('num', numeric_transformer, numerical_features), ('cat', categorical_transformer, categorical_features)])

lr_pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', LogisticRegression(random_state=42, solver='liblinear'))])
print("\nTreinando Regressão Logística...")
lr_pipeline.fit(X_train, y_train)

lr_probs = lr_pipeline.predict_proba(X_test)[:, 1]
print("--- Resultados da Regressão Logística ---")
print(f"ROC-AUC: {roc_auc_score(y_test, lr_probs):.4f}")
print(f"Log-Loss: {log_loss(y_test, lr_probs):.4f}")

# 3. Modelo Avançado (LightGBM)
for col in categorical_features:
    X_train[col] = X_train[col].astype('category')
    X_test[col] = X_test[col].astype('category')

lgbm_model = lgb.LGBMClassifier(objective='binary', random_state=42, n_estimators=500, learning_rate=0.05)
print("\nTreinando LightGBM...")
lgbm_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], eval_metric='logloss', callbacks=[lgb.early_stopping(10, verbose=False)])

lgbm_probs = lgbm_model.predict_proba(X_test)[:, 1]
print("--- Resultados do LightGBM ---")
print(f"ROC-AUC: {roc_auc_score(y_test, lgbm_probs):.4f}")
print(f"Log-Loss: {log_loss(y_test, lgbm_probs):.4f}")

# 4. Importância das Features
feature_importances = pd.DataFrame({
    'feature': X_train.columns,
    'importance': lgbm_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n--- Top 10 Features Mais Importantes (LightGBM) ---")
print(feature_importances.head(10))
print("\n--- [SEÇÃO 4] Modelagem Concluída ---")
# ==============================================================================
# SEÇÃO 5: EXPORTAÇÃO DOS MODELOS TREINADOS
# ==============================================================================
import joblib

print("\n--- [SEÇÃO 5] Iniciando Exportação dos Modelos ---")

# Criar um diretório para salvar os modelos, se não existir
output_dir = 'modelos_treinados'
os.makedirs(output_dir, exist_ok=True)

# 1. Exportar o pipeline completo da Regressão Logística
# O pipeline inclui o pré-processador (imputers, scalers, one-hot encoder) e o modelo.
# Isso é crucial, pois garante que os novos dados passarão exatamente pelo mesmo
# pré-processamento que os dados de treino.
caminho_modelo_lr = os.path.join(output_dir, 'pipeline_regressao_logistica.joblib')
joblib.dump(lr_pipeline, caminho_modelo_lr)
print(f"Pipeline da Regressão Logística salvo em: {caminho_modelo_lr}")


# 2. Exportar o modelo LightGBM
# Como o LightGBM lidou com as categorias nativamente, podemos salvar apenas o modelo.
# No entanto, é vital lembrar de converter as colunas categóricas para o tipo 'category'
# antes de fazer previsões em um novo notebook.
caminho_modelo_lgbm = os.path.join(output_dir, 'modelo_lightgbm.joblib')
joblib.dump(lgbm_model, caminho_modelo_lgbm)
print(f"Modelo LightGBM salvo em: {caminho_modelo_lgbm}")

# 3. (Opcional, mas recomendado) Salvar a lista de colunas usadas no treino
# Isso ajuda a garantir que você passará os dados na ordem e formato corretos
# ao usar o modelo no futuro.
caminho_lista_colunas = os.path.join(output_dir, 'features_usadas.joblib')
joblib.dump(features_para_usar, caminho_lista_colunas)
print(f"Lista de features salva em: {caminho_lista_colunas}")


print("\n--- [SEÇÃO 5] Exportação Concluída ---")
# ==============================================================================
# SEÇÃO 6: SALVAR DADOS DE TESTE PARA AVALIAÇÃO EXTERNA
# ==============================================================================
# Adicione este bloco ao final do seu script treinar_modelo_absenteismo.py

print("\n--- [SEÇÃO 6] Salvando dados de teste em CSV ---")

# Criar o diretório de saída se não existir
output_dir = 'modelos_treinados'
os.makedirs(output_dir, exist_ok=True)

# Salvar X_test e y_test
caminho_X_test = os.path.join(output_dir, 'X_test.csv')
caminho_y_test = os.path.join(output_dir, 'y_test.csv')

X_test.to_csv(caminho_X_test, index=False)
y_test.to_csv(caminho_y_test, index=False)

print(f"X_test salvo em: {caminho_X_test}")
print(f"y_test salvo em: {caminho_y_test}")
print("\n--- [SEÇÃO 6] Salvamento Concluído ---")

# ==============================================================================
# SEÇÃO 7: SALVAR MAPEAMENTO DE CATEGORIAS PARA LIGHTGBM
# ==============================================================================
# Adicione este bloco ao final do seu script treinar_modelo_absenteismo.py

print("\n--- [SEÇÃO 7] Salvando mapeamento de categorias do LightGBM ---")

# Criar o diretório de saída se não existir
output_dir = 'modelos_treinados'
os.makedirs(output_dir, exist_ok=True)

# Identificar quais colunas em X_train são categóricas
categorical_features_train = X_train.select_dtypes(exclude=np.number).columns.tolist()

# Criar um dicionário para armazenar as categorias de cada coluna
# Este dicionário guardará o "DNA" de cada coluna categórica
category_mappings = {}

# Iterar sobre cada coluna categórica em X_train
for col in categorical_features_train:
    # 1. Converte a coluna para o tipo 'category'. Isso faz o Pandas
    #    criar uma lista interna de todas as categorias únicas.
    X_train[col] = X_train[col].astype('category')
    
    # 2. Extrai essa lista de categorias e a salva no nosso dicionário.
    #    A chave é o nome da coluna, e o valor é a lista de categorias.
    category_mappings[col] = X_train[col].cat.categories.tolist()

# Salvar o dicionário completo em um arquivo usando joblib
caminho_mappings = os.path.join(output_dir, 'category_mappings.joblib')
joblib.dump(category_mappings, caminho_mappings)

print(f"Mapeamento de categorias salvo com sucesso em: {caminho_mappings}")
print("\n--- [SEÇÃO 7] Salvamento Concluído ---")