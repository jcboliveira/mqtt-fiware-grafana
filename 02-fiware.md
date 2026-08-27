# 2. Arrancar o ambiente FIWARE

## Iniciar os serviços

O Compose inicia Mosquitto, MongoDB, Orion, IoT Agent, QuantumLeap, CrateDB, Grafana e os serviços auxiliares:

```bash
cd /root/mqtt-grafana
docker compose up -d
```

## Verificar o estado

```bash
docker compose ps
```

O container `fiware-bootstrap` termina normalmente depois de criar os recursos FIWARE e a datasource do Grafana.

## Consultar o bootstrap

```bash
docker logs fiware-bootstrap
```
