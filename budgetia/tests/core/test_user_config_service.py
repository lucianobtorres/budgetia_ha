from pathlib import Path

import pytest

from src import config
from src.core.user_config_service import UserConfigService

# A fixture 'mock_env_and_config' de conftest.py será usada automaticamente


@pytest.fixture
def service(tmp_path: Path) -> UserConfigService:
    """Retorna uma instância limpa do UserConfigService para 'test_user'."""
    # O 'tmp_path' aqui é o mesmo 'tmp_path' usado pelo mock_env_and_config
    return UserConfigService("test_user")


def test_init_creates_user_directory(
    service: UserConfigService, tmp_path: Path
) -> None:
    """Testa se o __init__ cria a pasta do usuário."""
    expected_dir = tmp_path / "users" / "test_user"
    assert expected_dir.is_dir()
    assert service.config_dir == expected_dir


def test_save_and_load_config_is_encrypted_and_decrypted(
    service: UserConfigService,
) -> None:
    """
    Teste crucial de Criptografia:
    Verifica se o arquivo salvo NÃO é plaintext e se o load() o descriptografa.
    """
    test_data = {"chave": "valor_secreto"}

    # Ação: Salvar
    service.save_config(test_data)

    # Verificação 1: O arquivo existe
    assert service.config_file_path.exists()

    # Verificação 2: O conteúdo NÃO é plaintext
    raw_content = service.config_file_path.read_text("utf-8")
    assert "valor_secreto" not in raw_content
    assert "{" not in raw_content  # Prova que não é JSON

    # Verificação 3: O load() descriptografa corretamente
    loaded_data = service.load_config()
    assert loaded_data == test_data


def test_load_config_handles_empty_file(service: UserConfigService) -> None:
    """Testa se load_config() retorna {} para um arquivo vazio."""
    service.config_file_path.touch()  # Cria um arquivo vazio
    loaded_data = service.load_config()
    assert loaded_data == {}


def test_load_config_handles_corrupted_file(service: UserConfigService) -> None:
    """Testa se load_config() retorna {} para um arquivo corrompido."""
    service.config_file_path.write_bytes(b"dados_corrompidos")
    loaded_data = service.load_config()
    assert loaded_data == {}


def test_get_and_save_planilha_path(service: UserConfigService, tmp_path: Path) -> None:
    """Testa a lógica de salvar e obter o caminho da planilha."""
    # Cria um arquivo dummy para simular um caminho de arquivo local válido
    dummy_file = tmp_path / "minha_planilha.xlsx"
    dummy_file.touch()
    test_path = str(dummy_file)

    # 1. Começa vazio
    assert service.get_planilha_path() is None

    # 2. Salva o caminho
    service.save_planilha_path(test_path)

    # 3. Verifica se foi salvo
    assert service.get_planilha_path() == test_path

    # 4. Verifica se o config.json subjacente foi salvo corretamente
    loaded_data = service.load_config()
    assert loaded_data[config.PLANILHA_KEY] == test_path


def test_get_mapeamento_and_save_mapeamento(service: UserConfigService) -> None:
    """Testa a lógica de salvar e obter o mapeamento."""
    test_map = {"coluna_A": "Data", "strategy_module": "meu_modulo"}

    # 1. Começa vazio
    assert service.get_mapeamento() is None

    # 2. Salva o mapeamento
    service.save_mapeamento(test_map)

    # 3. Verifica se foi salvo
    assert service.get_mapeamento() == test_map


def test_clear_config_resets_onboarding_but_keeps_identity(
    service: UserConfigService,
) -> None:
    """
    Teste de Ciclo de Vida (LGPD):
    Verifica se clear_config() apaga o user_strategy.py e reseta
    as chaves de onboarding, mas mantém as chaves de identidade.
    """
    # 1. Criar os arquivos e dados de "lixo"
    initial_config = {
        "planilha_path": "/caminho/teste.xlsx",
        "onboarding_state": "COMPLETE",
        "google_oauth_tokens": "token_secreto_do_google",
    }
    service.save_config(initial_config)
    service.strategy_file_path.touch()  # Cria o arquivo .py

    # 2. Verificar se eles existem
    assert service.config_file_path.exists()
    assert service.strategy_file_path.exists()

    # 3. Executar a Ação
    service.clear_config()

    # 4. Verificar se o arquivo de estratégia foi excluído
    assert not service.strategy_file_path.exists()

    # 5. Verificar se o arquivo de config AINDA existe, mas foi limpo
    assert service.config_file_path.exists()
    cleaned_config = service.load_config()

    # 6. Verificar se as chaves de onboarding foram removidas
    assert "planilha_path" not in cleaned_config
    assert "onboarding_state" not in cleaned_config

    # 7. Verificar se a chave de identidade foi MANTIDA
    assert cleaned_config["google_oauth_tokens"] == "token_secreto_do_google"
