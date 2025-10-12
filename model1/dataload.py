import pandas as pd
import glob
import os

# --- Configuração ---
# Altere esta variável para o caminho da sua pasta 'data'
caminho_para_pasta = './data/' # '.' significa o diretório atual

# --- Lógica de Carregamento ---

def carregar_dataframe_particionado(caminho_base, nome_base):
    """
    Encontra todos os arquivos parquet para uma tabela base,
    lê todos eles e os concatena em um único DataFrame.
    """
    # Cria um padrão de busca, ex: 'data/marcacao-*.parquet'
    padrao_busca = os.path.join(caminho_base, f"{nome_base}-*.parquet")
    
    # Usa glob para encontrar todos os arquivos que correspondem ao padrão
    lista_de_arquivos = glob.glob(padrao_busca)
    
    if not lista_de_arquivos:
        print(f"Aviso: Nenhum arquivo encontrado para '{nome_base}'")
        return None
        
    # Lê cada arquivo parquet em uma lista de DataFrames
    lista_dfs = [pd.read_parquet(arquivo) for arquivo in lista_de_arquivos]
    
    # Concatena todos os DataFrames da lista em um só
    df_completo = pd.concat(lista_dfs, ignore_index=True)
    
    print(f"DataFrame '{nome_base}' carregado com {len(df_completo):,} linhas a partir de {len(lista_de_arquivos)} arquivos.")
    return df_completo

def carregar_dataframe_unico(caminho_base, nome_arquivo):
    """
    Lê um único arquivo parquet que não é particionado.
    """
    caminho_completo = os.path.join(caminho_base, f"{nome_arquivo}-000000000000.parquet")
    
    if not os.path.exists(caminho_completo):
        print(f"Aviso: Arquivo '{caminho_completo}' não encontrado.")
        return None
        
    df = pd.read_parquet(caminho_completo)
    print(f"DataFrame '{nome_arquivo}' carregado com {len(df):,} linhas.")
    return df


# Nomes base das tabelas que são particionadas (têm múltiplos arquivos)
tabelas_particionadas = [
    'marcacao',
    'oferta_programada',
    'profissional_historico',
    'solicitacao'
]

# Nomes das tabelas que são arquivos únicos
tabelas_unicas = [
    'cids',
    'equipamento_historico',
    'habilitacao_historico',
    'leito_historico',
    'procedimento',
    'tempo_espera',
    'unidade_historico'
]

# Dicionário para armazenar todos os nossos DataFrames
dataframes = {}

print("--- Iniciando carregamento de tabelas particionadas ---")
for nome_tabela in tabelas_particionadas:
    dataframes[nome_tabela] = carregar_dataframe_particionado(caminho_para_pasta, nome_tabela)

print("\n--- Iniciando carregamento de tabelas únicas ---")
for nome_tabela in tabelas_unicas:
    dataframes[nome_tabela] = carregar_dataframe_unico(caminho_para_pasta, nome_tabela)

print("\n--- Carregamento Concluído! ---")

# --- Exemplo de como acessar um DataFrame ---
# Vamos verificar o cabeçalho do DataFrame 'marcacao'
if 'marcacao' in dataframes and dataframes['marcacao'] is not None:
    print("\nExemplo: 5 primeiras linhas do DataFrame 'marcacao':")
    print(dataframes['marcacao'].head())