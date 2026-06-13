"""
Implementacoes de LLM sob o contrato LLMProvider.

Tres caminhos, mesmo desenho da camada de embeddings:

  - anthropic: Claude via API (extra [anthropic]).
  - openai: GPT via API (extra [openai]).
  - local: stub deterministico, sem rede. NAO raciocina: preenche um
    template com o contexto recebido. Existe para o fluxo do agente ser
    testavel offline; o raciocinio real exige anthropic ou openai.

O modelo e configuravel por MAESTRO_LLM_MODEL; sem ela, cada provedor usa
um default razoavel.
"""

from __future__ import annotations

from .base import register_llm


@register_llm("anthropic")
class AnthropicLLM:
    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, settings):
        import anthropic  # extra: maestro-agent[anthropic]
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model or self.DEFAULT_MODEL

    def complete(self, system: str, prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()


@register_llm("openai")
class OpenAILLM:
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, settings):
        from openai import OpenAI  # extra: maestro-agent[openai]
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model or self.DEFAULT_MODEL

    def complete(self, system: str, prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip()


@register_llm("local")
class LocalTemplateLLM:
    """Stub deterministico para desenvolvimento e teste offline."""

    def __init__(self, settings=None):
        pass

    def complete(self, system: str, prompt: str) -> str:
        n_facts = prompt.count("FATO ")
        return (
            f"[análise offline, sem LLM real] Diagnóstico baseado em {n_facts} "
            "fato(s) recuperado(s) da memória de longo prazo. Causa provável: "
            "query sem índice adequado gerando varredura de coleção. Ação "
            "recomendada: criar o índice apontado pelos fatos recuperados, "
            "sob aprovação humana."
        )
