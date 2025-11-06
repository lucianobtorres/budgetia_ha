# Em: src/finance/planilha_manager.py
import datetime
from typing import Any  # <-- ADICIONE Optional, Any, Dict, List

import pandas as pd

import config

from .excel_handler import ExcelHandler
from .financial_calculator import FinancialCalculator
from .mapping_strategies.base_strategy import BaseMappingStrategy
from .mapping_strategies.custom_json_strategy import CustomJsonStrategy
from .mapping_strategies.default_strategy import DefaultStrategy


class PlanilhaManager:
    """
    Orquestra os dados financeiros em memória (self.dfs) e delega
    cálculos e persistência para classes especialistas.
    """

    # --- __INIT__ MODIFICADO ---
    def __init__(
        self,
        excel_handler: ExcelHandler,
        mapeamento: dict[str, Any] | None = None,  # <-- NOVO ARGUMENTO
    ) -> None:
        """
        Inicializa o gerenciador.
        'mapeamento' é um dicionário que instrui o ExcelHandler
        sobre como traduzir a planilha do usuário para o nosso schema.
        """
        self.excel_handler = excel_handler
        self.calculator = FinancialCalculator()
        self.mapeamento = mapeamento  # <-- Armazena o mapa

        self.strategy: BaseMappingStrategy
        if self.mapeamento:
            # Se temos um mapa, usamos a estratégia JSON
            self.strategy = CustomJsonStrategy(config.LAYOUT_PLANILHA, self.mapeamento)
        else:
            # Senão, usamos a estratégia Padrão
            self.strategy = DefaultStrategy(config.LAYOUT_PLANILHA, self.mapeamento)

        # Passa o mapeamento (ou None) para o ExcelHandler
        self.dfs, is_new_file = self.excel_handler.load_sheets(
            config.LAYOUT_PLANILHA, self.strategy
        )

        self.is_new_file = is_new_file  # Armazena a flag

        if self.is_new_file:
            print("LOG: Detectado arquivo novo ou abas faltando.")
            # Só popula dados de exemplo se for um arquivo novo E padrão (sem mapa)
            if self.mapeamento is None:
                print(
                    "--- DEBUG PM: Arquivo novo padrão. Populando com dados de exemplo... ---"
                )
                self._populate_initial_data()  # (Este método já existe abaixo)
                self.save(add_intelligence=True)  # Salva dados de exemplo e formato
            else:
                print(
                    "--- DEBUG PM: Arquivo mapeado/novo. Salvando abas do sistema (ex: Perfil)... ---"
                )
                # Salva o arquivo para criar as abas que faltavam (ex: Perfil Financeiro)
                self.save(add_intelligence=False)
        else:
            # Se o arquivo já existe e está completo (ou mapeado)
            print("LOG: Arquivo existente carregado. Recalculando orçamentos...")
            self.recalculate_budgets()  # (Este método já existe abaixo)

    # --- FIM DO __INIT__ MODIFICADO ---

    # --- MÉTODOS DE PERSISTÊNCIA ---
    def save(self, add_intelligence: bool = False) -> None:
        """
        Delega a tarefa de salvar todos os DataFrames para o ExcelHandler,
        passando a estratégia de mapeamento correta.
        """
        # Passa self.strategy para o handler saber como salvar "de volta"
        self.excel_handler.save_sheets(self.dfs, self.strategy, add_intelligence)

    # --- MÉTODOS DE ACESSO E MANIPULAÇÃO (CRUD) ---
    def visualizar_dados(self, aba_nome: str) -> pd.DataFrame:
        """Retorna uma cópia do DataFrame solicitado para visualização segura."""
        # Garante que a aba exista no self.dfs, se não, cria vazia
        if aba_nome not in self.dfs:
            if aba_nome in config.LAYOUT_PLANILHA:
                print(
                    f"AVISO: Tentando acessar aba '{aba_nome}' que não foi carregada. Criando em memória."
                )
                self.dfs[aba_nome] = pd.DataFrame(
                    columns=config.LAYOUT_PLANILHA[aba_nome]
                )
            else:
                print(f"ERRO: Tentando acessar aba desconhecida '{aba_nome}'.")
                return pd.DataFrame()  # Retorna DF vazio

        return self.dfs.get(aba_nome, pd.DataFrame()).copy()

    def update_dataframe(self, sheet_name: str, new_df: pd.DataFrame) -> None:
        """Atualiza um DataFrame inteiro em memória."""
        if sheet_name in self.dfs:
            self.dfs[sheet_name] = new_df
        else:
            print(
                f"ERRO: Tentativa de atualizar aba '{sheet_name}' que não existe no self.dfs."
            )

    def adicionar_registro(
        self,
        data: str,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
    ) -> None:
        """Adiciona uma nova transação à memória e recalcula os orçamentos."""
        # Assegura que estamos escrevendo na aba correta
        aba_transacoes = config.NomesAbas.TRANSACOES
        if aba_transacoes not in self.dfs:
            print(
                f"ERRO: Aba de transações '{aba_transacoes}' não encontrada em self.dfs."
            )
            return  # Não pode adicionar o registro

        df = self.dfs[aba_transacoes]
        novo_id = (
            (df["ID Transacao"].max() + 1)
            if not df.empty
            and "ID Transacao" in df.columns
            and df["ID Transacao"].notna().any()
            else 1
        )

        novo_registro = pd.DataFrame(
            [
                {
                    "ID Transacao": novo_id,
                    "Data": data,
                    "Tipo (Receita/Despesa)": tipo,
                    "Categoria": categoria,
                    "Descricao": descricao,
                    "Valor": valor,
                    "Status": status,
                }
            ],
            # Usa as colunas do config para garantir a ordem
            columns=config.LAYOUT_PLANILHA[aba_transacoes],
        )

        self.dfs[aba_transacoes] = pd.concat([df, novo_registro], ignore_index=True)
        self.recalculate_budgets()

    def adicionar_ou_atualizar_orcamento(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str = "",
    ) -> str:
        """Adiciona ou atualiza um orçamento em memória e recalcula."""
        aba_orcamentos = config.NomesAbas.ORCAMENTOS
        if aba_orcamentos not in self.dfs:
            return f"ERRO: Aba de orçamentos '{aba_orcamentos}' não encontrada."

        df = self.dfs[aba_orcamentos]

        # Garantir colunas essenciais
        if "Categoria" not in df.columns or "Período Orçamento" not in df.columns:
            print("ERRO: Aba de orçamentos mal formatada.")
            # Recria o DF com as colunas certas se estiver vazio
            if df.empty:
                df = pd.DataFrame(columns=config.LAYOUT_PLANILHA[aba_orcamentos])
            else:
                return "ERRO: Aba de orçamentos corrompida."

        categorias_existentes = df["Categoria"].astype(str).str.strip().str.lower()
        periodos_existentes = (
            df["Período Orçamento"].astype(str).str.strip().str.lower()
        )
        categoria_limpa = categoria.strip().lower()
        periodo_limpo = periodo.strip().lower()

        idx_existente = df[
            (categorias_existentes == categoria_limpa)
            & (periodos_existentes == periodo_limpo)
        ].index

        if not idx_existente.empty:
            idx = idx_existente[0]  # Pega o primeiro índice
            df.loc[idx, "Valor Limite Mensal"] = valor_limite
            df.loc[idx, "Observações"] = observacoes
            mensagem = f"Orçamento para '{categoria}' atualizado."
        else:
            novo_id = (
                (df["ID Orcamento"].max() + 1)
                if not df.empty
                and "ID Orcamento" in df.columns
                and df["ID Orcamento"].notna().any()
                else 1
            )
            novo_orcamento = pd.DataFrame(
                [
                    {
                        "ID Orcamento": novo_id,
                        "Categoria": categoria,
                        "Valor Limite Mensal": valor_limite,
                        "Período Orçamento": periodo,
                        "Observações": observacoes,
                    }
                ],
                columns=config.LAYOUT_PLANILHA[aba_orcamentos],
            )
            df = pd.concat([df, novo_orcamento], ignore_index=True).fillna(
                {
                    "Valor Gasto Atual": 0,
                    "Porcentagem Gasta (%)": 0,
                }  # fillna mais específico
            )
            mensagem = f"Novo orçamento para '{categoria}' criado."

        self.dfs[aba_orcamentos] = df
        self.recalculate_budgets()
        return mensagem

    def adicionar_ou_atualizar_divida(
        self,
        nome_divida: str,
        valor_original: float,
        taxa_juros_mensal: float,
        parcelas_totais: int,
        valor_parcela: float,
        parcelas_pagas: int = 0,
        data_proximo_pgto: str | None = None,  # Corrigido para Optional[str]
        observacoes: str = "",
    ) -> str:
        """
        Adiciona ou atualiza uma dívida na aba 'Minhas Dívidas'.
        Delega o cálculo do saldo devedor para o FinancialCalculator.
        """
        aba_dividas = config.NomesAbas.DIVIDAS
        if aba_dividas not in self.dfs:
            return f"ERRO: Aba de dívidas '{aba_dividas}' não encontrada."

        dividas_df = self.dfs[aba_dividas]

        # Garantir colunas essenciais
        if "Nome da Dívida" not in dividas_df.columns:
            if dividas_df.empty:
                dividas_df = pd.DataFrame(columns=config.LAYOUT_PLANILHA[aba_dividas])
            else:
                return "ERRO: Aba de dívidas corrompida."

        if data_proximo_pgto is None:
            data_proximo_pgto = ""  # Ou pd.NaT se preferir

        saldo_devedor_atual = self.calculator.calcular_saldo_devedor_atual(
            valor_parcela=valor_parcela,
            taxa_juros_mensal=taxa_juros_mensal,
            parcelas_totais=parcelas_totais,
            parcelas_pagas=parcelas_pagas,
        )

        dividas_existentes = (
            dividas_df["Nome da Dívida"].astype(str).str.strip().str.lower()
        )
        nome_divida_limpo = nome_divida.strip().lower()

        idx_existente = dividas_df[dividas_existentes == nome_divida_limpo].index

        if not idx_existente.empty:
            idx = idx_existente[0]
            dividas_df.loc[idx, "Saldo Devedor Atual"] = saldo_devedor_atual
            dividas_df.loc[idx, "Taxa Juros Mensal (%)"] = taxa_juros_mensal
            dividas_df.loc[idx, "Data Próximo Pgto"] = data_proximo_pgto
            dividas_df.loc[idx, "Parcelas Pagas"] = parcelas_pagas
            dividas_df.loc[idx, "Observações"] = observacoes
            # Atualiza outros campos caso tenham mudado
            dividas_df.loc[idx, "Valor Original"] = valor_original
            dividas_df.loc[idx, "Parcelas Totais"] = parcelas_totais
            dividas_df.loc[idx, "Valor Parcela"] = valor_parcela

            self.dfs[aba_dividas] = dividas_df
            mensagem = f"Dívida '{nome_divida}' atualizada. Saldo devedor: R$ {saldo_devedor_atual:,.2f}."
        else:
            novo_id = (
                (dividas_df["ID Divida"].max() + 1)
                if not dividas_df.empty
                and "ID Divida" in dividas_df.columns
                and dividas_df["ID Divida"].notna().any()
                else 1
            )
            nova_divida = pd.DataFrame(
                [
                    {
                        "ID Divida": novo_id,
                        "Nome da Dívida": nome_divida,
                        "Valor Original": valor_original,
                        "Saldo Devedor Atual": saldo_devedor_atual,
                        "Taxa Juros Mensal (%)": taxa_juros_mensal,
                        "Parcelas Totais": parcelas_totais,
                        "Parcelas Pagas": parcelas_pagas,
                        "Valor Parcela": valor_parcela,
                        "Data Próximo Pgto": data_proximo_pgto,
                        "Observações": observacoes,
                    }
                ],
                columns=config.LAYOUT_PLANILHA[aba_dividas],  # Usa o config
            )
            dividas_df = pd.concat([dividas_df, nova_divida], ignore_index=True)
            self.dfs[aba_dividas] = dividas_df
            mensagem = f"Nova dívida '{nome_divida}' registrada com saldo inicial de R$ {saldo_devedor_atual:,.2f}."

        print(f"LOG: {mensagem}")
        return str(mensagem)

    def adicionar_insight_ia(
        self,
        data_insight: str,
        tipo_insight: str,
        titulo_insight: str,
        detalhes_recomendacao: str,
        status: str = "Novo",
    ) -> None:
        """Adiciona um insight gerado pela IA na aba 'Consultoria da IA'."""
        aba_nome = config.NomesAbas.CONSULTORIA_IA
        if aba_nome not in self.dfs:
            print(f"ERRO: Aba '{aba_nome}' não existe para adicionar insight de IA.")
            return

        df_insight = self.dfs[aba_nome]
        novo_id = (
            (df_insight["ID Insight"].max() + 1)
            if not df_insight.empty
            and "ID Insight" in df_insight.columns
            and df_insight["ID Insight"].notna().any()
            else 1
        )

        novo_insight = pd.DataFrame(
            [
                {
                    "ID Insight": novo_id,
                    "Data do Insight": data_insight,
                    "Tipo de Insight": tipo_insight,
                    "Título do Insight": titulo_insight,
                    "Detalhes/Recomendação da IA": detalhes_recomendacao,
                    "Status (Novo/Lido/Concluído)": status,
                }
            ],
            columns=config.LAYOUT_PLANILHA[aba_nome],  # Usa o config
        )

        self.dfs[aba_nome] = pd.concat([df_insight, novo_insight], ignore_index=True)
        print(f"LOG: Insight de IA '{titulo_insight}' adicionado à aba '{aba_nome}'.")

    # --- MÉTODO PARA SALVAR PERFIL (QUE USAMOS ANTES) ---
    def salvar_dado_perfil(self, campo: str, valor: Any) -> str:
        """
        Adiciona ou atualiza um item na aba 'Perfil Financeiro'.
        Usa "Campo" como chave única.
        """
        aba_nome = config.NomesAbas.PERFIL_FINANCEIRO
        # Usa visualizar_dados para garantir que a aba seja criada em memória se não existir
        df_perfil = self.visualizar_dados(aba_nome)

        if "Campo" not in df_perfil.columns:
            # Se a aba foi criada agora ou está corrompida
            df_perfil = pd.DataFrame(columns=config.LAYOUT_PLANILHA[aba_nome])
            print(
                f"AVISO: Aba '{aba_nome}' recriada em memória pois estava mal formatada."
            )

        campo_limpo = str(campo).strip().lower()

        idx_existente = df_perfil[
            df_perfil["Campo"].astype(str).str.strip().str.lower() == campo_limpo
        ].index

        if not idx_existente.empty:
            idx = idx_existente[0]
            df_perfil.loc[idx, "Valor"] = valor
            mensagem = f"Perfil atualizado: '{campo}' definido como '{valor}'."
        else:
            novo_dado = pd.DataFrame(
                [{"Campo": campo, "Valor": valor, "Observações": ""}],
                columns=config.LAYOUT_PLANILHA[aba_nome],
            )
            df_perfil = pd.concat([df_perfil, novo_dado], ignore_index=True)
            mensagem = f"Perfil criado: '{campo}' definido como '{valor}'."

        self.dfs[aba_nome] = df_perfil
        self.save()  # Salva imediatamente
        print(f"LOG: {mensagem}")
        return mensagem

    # --- MÉTODOS DE ANÁLISE E CÁLCULO (DELEGADOS) ---
    def recalculate_budgets(self) -> None:
        """Delega o recálculo dos orçamentos para o FinancialCalculator."""
        df_orcamentos_atualizado = self.calculator.calcular_status_orcamentos(
            df_transacoes=self.dfs[config.NomesAbas.TRANSACOES],
            df_orcamentos=self.dfs[config.NomesAbas.ORCAMENTOS],
        )
        self.dfs[config.NomesAbas.ORCAMENTOS] = df_orcamentos_atualizado

    def get_summary(self) -> dict[str, float]:
        """Delega o cálculo do resumo para o FinancialCalculator."""
        return self.calculator.get_summary(self.dfs[config.NomesAbas.TRANSACOES])

    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        """Delega o cálculo das despesas por categoria para o FinancialCalculator."""
        return self.calculator.get_expenses_by_category(
            self.dfs[config.NomesAbas.TRANSACOES], top_n
        )

    def analisar_para_insights_proativos(self) -> list[dict[str, Any]]:
        """Orquestra a geração de insights proativos."""
        print("LOG: Orquestrando análise proativa para gerar insights.")
        self.recalculate_budgets()
        resumo = self.get_summary()
        saldo_total = resumo.get("saldo", 0.0)
        orcamentos_df = self.visualizar_dados(aba_nome=config.NomesAbas.ORCAMENTOS)

        insights_gerados = self.calculator.gerar_analise_proativa(
            orcamentos_df, saldo_total
        )

        if insights_gerados:
            print(f"LOG: {len(insights_gerados)} insights gerados. Registrando...")
            for insight in insights_gerados:
                self.adicionar_insight_ia(
                    data_insight=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    tipo_insight=insight["tipo_insight"],
                    titulo_insight=insight["titulo_insight"],
                    detalhes_recomendacao=insight["detalhes_recomendacao"],
                )
        else:
            print("LOG: Análise proativa concluída. Nenhum insight novo gerado.")

        return insights_gerados

    # --- NOVO MÉTODO (Adicionar no final da classe) ---
    def get_perfil_como_texto(self) -> str:
        """
        Lê a aba 'Perfil Financeiro' e formata os dados como uma string
        de contexto para ser injetada no prompt da IA.
        """
        try:
            df_perfil = self.visualizar_dados(config.NomesAbas.PERFIL_FINANCEIRO)
            if df_perfil.empty or "Campo" not in df_perfil.columns:
                return "O perfil do usuário ainda não foi preenchido."

            # Converte o DataFrame para um dicionário limpo, removendo valores nulos/vazios
            perfil_dict = df_perfil.dropna(subset=["Valor"])
            perfil_dict = perfil_dict[perfil_dict["Valor"] != ""]
            perfil_dict = pd.Series(
                perfil_dict.Valor.values, index=perfil_dict.Campo
            ).to_dict()

            if not perfil_dict:
                return "O perfil do usuário ainda não foi preenchido."

            # Formata como uma string bonita
            contexto_str = (
                "--- CONTEXTO DO PERFIL DO USUÁRIO (NÃO REPETIR/PERGUNTAR) ---\n"
            )
            for campo, valor in perfil_dict.items():
                contexto_str += f"- {campo}: {valor}\n"
            contexto_str += "--- FIM DO CONTEXTO ---"

            return contexto_str.strip()

        except Exception as e:
            print(f"ERRO ao ler perfil como texto: {e}")
            return "Não foi possível carregar o perfil do usuário."

    # --- FIM DO NOVO MÉTODO ---

    def _populate_initial_data(self) -> None:
        """Popula a planilha com dados de exemplo se estiver vazia."""
        print("--- DEBUG PM: Populando com dados de exemplo... ---")
        if self.dfs[config.NomesAbas.ORCAMENTOS].empty:
            orcamentos = [
                {
                    "Categoria": "Alimentação",
                    "Valor Limite Mensal": 600.0,
                    "Período Orçamento": "Mensal",
                },
                {
                    "Categoria": "Transporte",
                    "Valor Limite Mensal": 250.0,
                    "Período Orçamento": "Mensal",
                },
            ]
            for o in orcamentos:
                self.adicionar_ou_atualizar_orcamento(**o)  # Já recalcula

        if self.dfs[config.NomesAbas.TRANSACOES].empty:
            transacoes = [
                {
                    "data": "2024-07-01",
                    "tipo": "Receita",
                    "categoria": "Salário",
                    "descricao": "Pagamento",
                    "valor": 5000.0,
                },
                {
                    "data": "2024-07-05",
                    "tipo": "Despesa",
                    "categoria": "Moradia",
                    "descricao": "Aluguel",
                    "valor": 1500.0,
                },
            ]
            for t in transacoes:
                self.adicionar_registro(**t)  # Já recalcula

        # Garante que o perfil tenha os campos mínimos
        print("--- DEBUG PM: Garantindo campos de perfil... ---")
        self.salvar_dado_perfil("Renda Mensal Média", None)
        self.salvar_dado_perfil("Principal Objetivo", None)
