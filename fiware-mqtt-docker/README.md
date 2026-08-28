# FIWARE MQTT Docker

Este diretório disponibiliza **duas soluções alternativas** para levar dados FIWARE para MQTT:

1. **FIWARE -> MQTT**: um único container consulta todas as estações e publica diretamente no broker.
2. **FIWARE -> manager -> workers -> MQTT**: o manager descobre as estações e cria um container worker por estação. Cada worker consulta a sua entidade e publica no broker.

As duas soluções mantêm os tópicos MQTT originais. Escolha apenas uma para evitar publicação duplicada.

## Solução 1: FIWARE -> MQTT

Esta é a solução original, com um único processo a consultar as entidades `WeatherObserved`, `AirQualityObserved` e `NoiseLevelObserved` e a publicar diretamente todos os dados.

Os ficheiros da solução original estão em `/root/fiware-mqtt`:

```bash
cd /root/fiware-mqtt
docker build -t fiware-mqtt:local .
docker run -d --name fiware-mqtt --restart unless-stopped --network host fiware-mqtt:local
```

## Solução 2: FIWARE -> manager -> workers -> MQTT

Nesta solução, o `station-manager` consulta o URL FIWARE, verifica as estações disponíveis e cria automaticamente um container por estação. Os workers consultam as respetivas entidades e publicam nos mesmos tópicos MQTT, incluindo `fiware/noise/<estação>/LAeq` para o nível sonoro equivalente em dB.

### Arranque

O broker original deve estar acessível em `127.0.0.1:1883` no host. Se estiver no compose `/root/mqtt-grafana`, inicie-o primeiro:

```bash
cd /root/mqtt-grafana
docker compose up -d mosquitto

cd /root/fiware-mqtt-docker
docker compose build
docker compose up -d station-manager
```

O `network_mode: host` mantém o broker definido originalmente em `127.0.0.1:1883`. O manager cria containers como `fiware-station-weather-nome`, `fiware-station-airquality-nome` e `fiware-station-noise-nome`, remove workers de estações que deixem de ser anunciadas e volta a tentar após falhas temporárias.

### Verificação

```bash
docker logs -f fiware-mqtt-manager
docker ps --filter label=fiware-mqtt.managed=true
docker exec -it fiware-mosquitto mosquitto_sub -h 127.0.0.1 -p 1883 -t 'fiware/#' -v
```

### Parar os containers

Para parar o manager e os workers das estações, execute:

```bash
cd /root/fiware-mqtt-docker
docker compose down
docker ps -q --filter label=fiware-mqtt.managed=true | xargs -r docker stop
```

O `docker compose down` para os serviços definidos no Compose. Os workers são criados dinamicamente pelo manager, por isso são parados separadamente através da label `fiware-mqtt.managed=true`.

Para parar todos os containers em execução no host, incluindo o broker e os restantes serviços FIWARE:

```bash
docker ps -q | xargs -r docker stop
```

O URL FIWARE, broker, porta e intervalo podem ser alterados pelas variáveis `FIWARE_URL`, `MQTT_HOST`, `MQTT_PORT` e `DISCOVERY_INTERVAL` no `compose.yaml`.