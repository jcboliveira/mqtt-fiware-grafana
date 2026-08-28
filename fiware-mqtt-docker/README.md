# FIWARE MQTT Docker

Este diretório disponibiliza **duas soluções alternativas** para levar dados FIWARE para MQTT:

1. **FIWARE -> MQTT**: um único container consulta todas as estações e publica diretamente no broker.
2. **FIWARE -> manager -> workers -> MQTT**: o manager descobre as estações e cria um container worker por estação. Cada worker consulta a sua entidade e publica no broker.

As duas soluções mantêm os tópicos MQTT originais. Escolha apenas uma para evitar publicação duplicada.

## Diferença de topologia e arquitetura

As duas opções acedem à mesma fonte FIWARE e publicam no mesmo broker MQTT, mas organizam os processos de forma diferente:

| Aspeto | `fiware-mqtt` | `fiware-mqtt-docker` |
|---|---|---|
| Topologia | FIWARE -> um container -> MQTT | FIWARE -> manager -> vários workers -> MQTT |
| Representação das estações | Todas as estações são tratadas pelo mesmo processo | Cada estação é simulada por um container worker próprio |
| Descoberta | O próprio processo consulta e processa todas as entidades | O manager descobre as estações e gere o ciclo de vida dos workers |
| Recolha de dados | Um container recolhe os dados de todas as estações | Cada worker consulta apenas a entidade da sua estação |
| Isolamento | Sem isolamento entre estações | Falhas e reinícios ficam isolados por estação |
| Escalabilidade | Aumenta a carga dentro de um único container | Adiciona ou remove workers conforme as estações disponíveis |

Assim, `fiware-mqtt` **simula toda a rede num só container**, enquanto `fiware-mqtt-docker` **simula a existência física/lógica de cada estação**, criando um worker Docker por cada estação encontrada. O manager não publica os dados das estações: a sua função é descobrir, criar, atualizar, iniciar e remover workers. Os workers são os responsáveis pela consulta FIWARE e pela publicação MQTT.

## Solução 1: FIWARE -> MQTT

Esta é a solução original, com um único processo a consultar as entidades `WeatherObserved` e `AirQualityObserved` e a publicar diretamente todos os dados.

Os ficheiros da solução original estão em `/root/fiware-mqtt`:

```bash
cd /root/fiware-mqtt
docker build -t fiware-mqtt:local .
docker run -d --name fiware-mqtt --restart unless-stopped --network host fiware-mqtt:local
```

## Solução 2: FIWARE -> manager -> workers -> MQTT

Nesta solução, o `station-manager` consulta o URL FIWARE, verifica as estações disponíveis e cria automaticamente um container por estação. Os workers consultam as respetivas entidades e publicam nos mesmos tópicos MQTT.

### Arranque

O broker original deve estar acessível em `127.0.0.1:1883` no host. Se estiver no compose `/root/mqtt-grafana`, inicie-o primeiro:

```bash
cd /root/mqtt-grafana
docker compose up -d mosquitto

cd /root/fiware-mqtt-docker
docker compose build
docker compose up -d station-manager
```

O `network_mode: host` mantém o broker definido originalmente em `127.0.0.1:1883`. O manager cria containers como `fiware-station-weather-nome` e `fiware-station-airquality-nome`, remove workers de estações que deixem de ser anunciadas e volta a tentar após falhas temporárias.

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