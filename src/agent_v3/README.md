# Agent V3 - CLI Interativa

**Status**: ✅ Funcional  
**Última Atualização**: 2025-12-05

---

## 🎯 Visão Geral

O Agent V3 fornece uma CLI interativa para análise e correção de protocolos clínicos com sistema de aprendizado contínuo.

---

## 📁 Estrutura

```
src/agent_v3/
├── cli/                    # CLI Interativa
│   ├── interactive_cli.py  # Motor principal
│   ├── display_manager.py  # Formatação de saída
│   └── task_manager.py     # Gerenciamento de tarefas
│
├── applicator/             # Reconstrução de Protocolos
│   ├── protocol_reconstructor.py
│   └── version_utils.py
│
├── analysis/               # Análise (referência para enhanced.py)
│   └── enhanced_analyzer.py
│
├── cost_control/           # Controle de Custos
│   └── cost_estimator.py
│
└── output/                 # Protocolos reconstruídos
```

---

## 🚀 Uso

```bash
# Executar CLI interativa
python run_v3_cli.py
```

---

## 📚 Recursos

- **Documentação principal**: `../../README.md`
- **Roadmap**: `../../docs/roadmap.md`
- **Histórico**: `../../docs/dev_history.md`
