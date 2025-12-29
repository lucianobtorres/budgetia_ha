import os
import sys
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
# Tenta importar as configs do projeto para garantir consistência
try:
    src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from config import (
        NomesAbas, 
        LAYOUT_PLANILHA, 
        ColunasTransacoes,
        ColunasOrcamentos,
        ColunasDividas,
        ColunasMetas,
        ColunasInsights,
        ColunasPerfil
    )
except ImportError as e:
    print(f"ERRO CRÍTICO: Não foi possível importar src/config.py. Certifique-se de rodar na raiz do projeto. ({e})")
    sys.exit(1)

OUTPUT_FILE = "planilha_mestra.xlsx"

def create_empty_dataframe(columns):
    return pd.DataFrame(columns=columns)

def main():
    print(f"Gerando '{OUTPUT_FILE}' baseado no schema oficial...")
    
    with pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter") as writer:
        
        # 1. Visão Geral e Transações
        cols_trans = LAYOUT_PLANILHA[NomesAbas.TRANSACOES]
        df_trans = create_empty_dataframe(cols_trans)
        # Adicionar uma transação de exemplo para não ficar vazio
        df_trans.loc[0] = [
            1, 
            datetime.now(), 
            "Receita", 
            "Salário", 
            "Salário Inicial", 
            1000.00, 
            "Concluído"
        ]
        df_trans.to_excel(writer, sheet_name=NomesAbas.TRANSACOES, index=False)
        print(f"✅ Aba '{NomesAbas.TRANSACOES}' criada.")

        # 2. Meus Orçamentos
        cols_orc = LAYOUT_PLANILHA[NomesAbas.ORCAMENTOS]
        df_orc = create_empty_dataframe(cols_orc)
        df_orc.to_excel(writer, sheet_name=NomesAbas.ORCAMENTOS, index=False)
        print(f"✅ Aba '{NomesAbas.ORCAMENTOS}' criada.")

        # 3. Minhas Dívidas
        cols_div = LAYOUT_PLANILHA[NomesAbas.DIVIDAS]
        df_div = create_empty_dataframe(cols_div)
        df_div.to_excel(writer, sheet_name=NomesAbas.DIVIDAS, index=False)
        print(f"✅ Aba '{NomesAbas.DIVIDAS}' criada.")

        # 4. Metas Financeiras
        cols_metas = LAYOUT_PLANILHA[NomesAbas.METAS]
        df_metas = create_empty_dataframe(cols_metas)
        df_metas.to_excel(writer, sheet_name=NomesAbas.METAS, index=False)
        print(f"✅ Aba '{NomesAbas.METAS}' criada.")

        # 5. Consultoria da IA
        cols_ia = LAYOUT_PLANILHA[NomesAbas.CONSULTORIA_IA]
        df_ia = create_empty_dataframe(cols_ia)
        df_ia.to_excel(writer, sheet_name=NomesAbas.CONSULTORIA_IA, index=False)
        print(f"✅ Aba '{NomesAbas.CONSULTORIA_IA}' criada.")

        # 6. Perfil Financeiro
        cols_perfil = LAYOUT_PLANILHA[NomesAbas.PERFIL_FINANCEIRO]
        df_perfil = create_empty_dataframe(cols_perfil)
        df_perfil.to_excel(writer, sheet_name=NomesAbas.PERFIL_FINANCEIRO, index=False)
        print(f"✅ Aba '{NomesAbas.PERFIL_FINANCEIRO}' criada.")

    print(f"\n🎉 Sucesso! '{OUTPUT_FILE}' gerado na raiz.")

if __name__ == "__main__":
    main()
