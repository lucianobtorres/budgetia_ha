import os

import pandas as pd

from agent_implementations.langchain_agent import IADeFinancas
from finance.planilha_manager import PlanilhaManager


# Esta função ainda é útil para quando a IA precisar VER os dados
def formatar_dados_planilha_para_ia(df: pd.DataFrame) -> str:
    """
    Formata o DataFrame da planilha em um texto compreensível para a IA.
    Para uma análise inicial, podemos converter o DF em um JSON ou texto tabular.
    """
    if df.empty:
        return "Nenhum dado financeiro disponível na planilha para análise."
    return str(df.to_json(orient="records", indent=2, date_format="iso"))


def main() -> None:
    """
    Função principal que orquestra a leitura da planilha e a geração de insights pela IA.
    """
    print("Iniciando o Sistema de Gestão Financeira Inteligente...")

    # Definindo o caminho da planilha de forma robusta
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    planilha_path = os.path.join(project_root, "planilha_mestra.xlsx")

    # 1. Inicializa o gerenciador da planilha
    plan_manager = PlanilhaManager(nome_arquivo=planilha_path)

    # 2. Garante que temos alguns dados na planilha para a IA analisar
    # Remove a adição automática de dados se já tiver, para evitar duplicação em cada execução.
    if plan_manager.visualizar_dados().empty:
        print("Planilha vazia. Adicionando dados de exemplo para demonstração.")
        plan_manager.adicionar_registro(
            "2024-07-01", "Receita", "Salário", "Pagamento mensal", 3000.00, "Concluído"
        )
        plan_manager.adicionar_registro(
            "2024-07-05", "Despesa", "Aluguel", "Aluguel Junho", 1200.00, "Concluído"
        )
        plan_manager.adicionar_registro(
            "2024-07-10",
            "Despesa",
            "Alimentação",
            "Compras de supermercado",
            350.50,
            "Concluído",
        )
        plan_manager.adicionar_registro(
            "2024-07-12", "Receita", "Extra", "Freelance X", 500.00, "Pendente"
        )
        plan_manager.adicionar_registro(
            "2024-07-15", "Despesa", "Transporte", "Combustível", 150.00, "Concluído"
        )
        plan_manager.adicionar_registro(
            "2024-07-20", "Despesa", "Lazer", "Cinema e Jantar", 100.00, "Pendente"
        )
    else:
        print(
            f"Planilha existente: {planilha_path}. {len(plan_manager.visualizar_dados())} registros encontrados."
        )

    # 3. Inicializa a IA, passando a instância do PlanilhaManager
    ia_financas = IADeFinancas(planilha_manager=plan_manager)

    print("\n--- Conversando com a IA (digite 'sair' para encerrar) ---")
    while True:
        user_input = input("Você: ")
        if user_input.lower() == "sair":
            print("Encerrando a conversa.")
            break

        print("IA (pensando...):")
        resposta_ia = ia_financas.interagir_com_usuario(user_input)
        # Ajustado para imprimir apenas a resposta final do agente, evitando duplicação.
        # Os logs internos do agente (verbose=True) já mostram o processo de pensamento.
        print(f"IA: {resposta_ia}")

    # Opcional: Visualizar a planilha após a interação para ver se algo foi adicionado
    print("\n--- Dados Finais da Planilha ---")
    print(plan_manager.visualizar_dados())


if __name__ == "__main__":
    main()
