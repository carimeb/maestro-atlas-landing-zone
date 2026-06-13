"""maestro_agent: camada de agentes do Maestro.

Fundacoes transversais: configuracao central (config), provedores plugaveis
(providers), seguranca e auditoria (security) e memoria (memory)."""

from .config import Settings, ConfigError

__all__ = ["Settings", "ConfigError"]
__version__ = "0.1.0"
