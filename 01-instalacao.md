# 1. Pré-requisitos e compilação

## Pré-requisitos

- Docker Engine instalado e em execução.
- Docker Compose disponível através de `docker compose`.
- Acesso ao diretório `/root`.

## Compilar o container MQTT

O `Dockerfile` e o código Python estão em `/root/fiware-mqtt`:

```bash
cd /root/fiware-mqtt
docker build -t fiware-mqtt:local .
```

A imagem instala `requests`, `paho-mqtt` e `python-dateutil` e inicia automaticamente `fiware-mqtt.py`.
