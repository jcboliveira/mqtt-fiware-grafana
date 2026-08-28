# 3. Executar e validar o MQTT

## Soluções disponíveis

Existem duas arquiteturas alternativas para transmitir dados FIWARE por MQTT:

1. **FIWARE -> MQTT**: um único container consulta todas as estações `WeatherObserved`, `AirQualityObserved` e `NoiseLevelObserved` e publica diretamente no broker.
2. **FIWARE -> manager -> workers -> MQTT**: o manager consulta o FIWARE, descobre as estações e cria um worker Docker por cada estação. Cada worker consulta apenas a sua estação e publica no broker.

As duas soluções usam a mesma fonte FIWARE, o mesmo broker e os mesmos tópicos MQTT. Deve ser iniciada apenas uma, para evitar publicação duplicada.

### Diferenças de topologia e arquitetura

| Aspeto | `fiware-mqtt` | `fiware-mqtt-docker` |
|---|---|---|
| Topologia | FIWARE -> um container -> MQTT | FIWARE -> manager -> vários workers -> MQTT |
| Representação das estações | Todas as estações são tratadas pelo mesmo processo | Cada estação é simulada por um container worker próprio |
| Descoberta | O próprio processo consulta e processa todas as entidades | O manager descobre as estações e gere o ciclo de vida dos workers |
| Recolha de dados | Um container recolhe os dados de todas as estações | Cada worker consulta apenas a entidade da sua estação |
| Isolamento | Sem isolamento entre estações | Falhas e reinícios ficam isolados por estação |
| Escalabilidade | Aumenta a carga dentro de um único container | Adiciona ou remove workers conforme as estações disponíveis |

Assim, `fiware-mqtt` **simula toda a rede num só container**, enquanto `fiware-mqtt-docker` **simula a existência física/lógica de cada estação**, criando um worker Docker por cada estação encontrada. O manager não publica os dados das estações: descobre, cria, atualiza, inicia e remove workers. Os workers consultam FIWARE e fazem a publicação MQTT.

### Porque existem as duas soluções?

As duas soluções permitem escolher entre simplicidade operacional e isolamento por estação. Mantêm os mesmos tópicos MQTT para que os consumidores não tenham de mudar quando se altera a arquitetura.

| Solução | Vantagens | Desvantagens | Indicada quando |
|---|---|---|---|
| `fiware-mqtt` | Menos contentores, configuração e consumo de recursos; mais simples de iniciar, observar e diagnosticar. | Uma falha ou reinício interrompe a publicação de todas as estações; o processo concentra toda a carga e não permite observar cada estação isoladamente. | Há poucas estações, os recursos são limitados ou pretende uma instalação simples. |
| `fiware-mqtt-docker` | Cada estação fica isolada num worker; falhas, logs e reinícios podem ser tratados por estação; acompanha automaticamente a entrada e saída de estações no FIWARE. | Requer Docker socket, manager e mais contentores; consome mais recursos e torna a operação e limpeza dos workers mais complexa. | É importante representar cada estação individualmente, isolar falhas ou acompanhar uma rede de estações dinâmica. |

Em ambos os casos, os dados publicados e os tópicos MQTT são equivalentes. Execute somente uma opção de cada vez, pois iniciar ambas duplica as mensagens no broker.

## Opção 1: FIWARE -> MQTT

Esta opção usa um único contentor para consultar todas as estações e publicar no broker. Antes de a iniciar, garanta que a imagem foi criada conforme descrito em `01-instalacao.md`.

O script conecta ao broker em `127.0.0.1:1883`, sem utilizador e sem password. Como esse endereço dentro do contentor aponta para o próprio contentor, use a rede do host no Linux:

```bash
docker run -d \
  --name fiware-mqtt \
  --restart unless-stopped \
  --network host \
  fiware-mqtt:local
```

Se o contentor já existir, use `docker start fiware-mqtt`.

### Consultar os logs

```bash
docker logs -f fiware-mqtt
```

### Observar mensagens MQTT

```bash
docker exec -it fiware-mosquitto \
  mosquitto_sub -h 127.0.0.1 -p 1883 -t 'fiware/#' -v
```

Exemplos de tópicos:

```text
fiware/weather/bolhao/temperature 21.5
fiware/weather/bolhao/relativeHumidity 63.1
fiware/airquality/polo_asprela/pm25 2.0
fiware/noise/aliados/LAeq 74.1
```

As medições de ruído usam `LAeq`, o nível sonoro equivalente em dB. Tal como os restantes tipos de dados, cada estação publica também `local`, `latitude`, `longitude`, `dateObserved` e `last_mqtt_update`.

O contentor `fiware-mqtt-json-bridge` subscreve `fiware/#` e envia os valores para o Orion:

```bash
docker logs -f fiware-mqtt-json-bridge
```

### Parar o publicador

```bash
docker stop fiware-mqtt
docker rm fiware-mqtt
```

## Opção 2: FIWARE -> manager -> workers -> MQTT

Esta opção cria um contentor manager que descobre as estações FIWARE e gere um worker por estação. Não a execute enquanto a opção 1 estiver ativa.

Confirme que o broker está em execução e, depois, construa e inicie o manager:

```bash
cd /root/mqtt-grafana
docker compose up -d mosquitto

cd /root/fiware-mqtt-docker
docker compose build
docker compose up -d station-manager
```

O `network_mode: host` permite que o manager e os workers acedam ao broker em `127.0.0.1:1883`. Os workers criados recebem a label `fiware-mqtt.managed=true`.

### Consultar os logs e workers

```bash
docker logs -f fiware-mqtt-manager
docker ps --filter label=fiware-mqtt.managed=true
```

### Observar mensagens MQTT

```bash
docker exec -it fiware-mosquitto \
  mosquitto_sub -h 127.0.0.1 -p 1883 -t 'fiware/#' -v
```

Os tópicos publicados são os mesmos da opção 1. Pode também confirmar os logs de um worker com:

```bash
docker logs -f <nome-do-worker>
```

### Parar o manager e os workers

```bash
cd /root/fiware-mqtt-docker
docker compose down
docker ps -q --filter label=fiware-mqtt.managed=true | xargs -r docker stop
```
