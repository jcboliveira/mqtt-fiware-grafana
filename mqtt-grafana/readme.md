# FIWARE MQTT e Grafana

Ambiente FIWARE que recolhe dados através de MQTT, armazena histórico em CrateDB e disponibiliza visualizações no Grafana.

Os dados MQTT são gerados por recolha da informação meteo e de qualidade de ar disponibilizada pela CMP.

## Documentação

1. [Pré-requisitos e compilação](01-instalacao.md)
2. [Arrancar o ambiente FIWARE/Grafana](02-fiware.md)
3. [Executar e validar o emissor de dados MQTT](03-mqtt.md)
4. [Aceder e configurar o Grafana](04-grafana.md)
5. [Consultas e manutenção](05-manutencao.md)

## Acesso rápido

Depois de iniciar os serviços, o Grafana está disponível na porta `3000` do servidor:

```text
http://IP_DO_SERVIDOR:3000
```

Substitua `IP_DO_SERVIDOR` pelo IP ou hostname real do servidor.

As instruções completas para compilar, executar, validar mensagens MQTT e criar a primeira dashboard estão nos ficheiros acima.
