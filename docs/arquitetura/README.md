# Arquitetura

Diagramas gerados a partir do Sinapse (o segundo cérebro do Pedro). Cada projeto tem três vistas,
cada uma numa notação padrão:

1. **Quem usa e para quê**: UML, diagrama de casos de uso.
2. **O processo principal**: BPMN 2.0, com raias por quem executa.
3. **A arquitetura**: modelo C4, nível 2 (containers).

## Mary House · gestão de serviços domésticos

Sistema interno em Django da agência Mary House: cadastra contratantes, prestadoras e serviços, amarra tudo num agendamento com status e mostra painel, relatórios e histórico. Encerrado em 03/09/2026; a proposta de levar para Worker não foi adiante.

### Quem usa e para quê (UML)

![Casos de uso · Mary House · gestão de serviços domésticos](./maryhouse-1-casos-de-uso.svg)

### Do pedido do contratante ao serviço concluído (BPMN 2.0)

![Processo · Mary House · gestão de serviços domésticos](./maryhouse-2-processo.svg)

### Arquitetura (C4, containers)

![Arquitetura · Mary House · gestão de serviços domésticos](./maryhouse-3-arquitetura.svg)

Editável: [`maryhouse.excalidraw`](./maryhouse.excalidraw), abre em [excalidraw.com](https://excalidraw.com) ou no VS Code com a extensão Excalidraw.

A fonte destes arquivos é o vault do Sinapse (`09-DESENHOS/`); alterações feitas aqui são sobrescritas na próxima publicação.
