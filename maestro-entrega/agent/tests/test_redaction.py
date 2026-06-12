import pytest
from maestro_agent.security.redaction import scan, ensure_clean, SecretDetected


def test_connection_string_com_senha_detectada():
    findings = scan("uri do cluster: mongodb+srv://admin:Hunter2@cluster0.mongodb.net")
    assert any(f.rule == "connection_string_com_credencial" for f in findings)


def test_api_key_detectada():
    assert scan("use a chave sk-ant-abc123def456ghi789jkl")


def test_pem_detectado():
    assert scan("-----BEGIN RSA PRIVATE KEY-----\nMIIE...")


def test_senha_atribuida_detectada():
    assert scan("acesso temporario: senha=Tr0c4r!")


def test_texto_operacional_limpo():
    assert scan("Indice { user_id: 1 } resolveu COLLSCAN na colecao transactions.") == []
    assert scan("Baseline de CPU em horario comercial: 55-65%.") == []


def test_excerpt_vem_mascarado():
    findings = scan("mongodb+srv://admin:Hunter2@h")
    assert "Hunter2" not in findings[0].excerpt


def test_ensure_clean_lanca():
    with pytest.raises(SecretDetected):
        ensure_clean("password=abc123")
