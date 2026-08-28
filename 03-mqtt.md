# 3. Executar e validar o MQTT

## Soluções disponíveis

Existem duas arquiteturas alternativas para transmitir dados FIWARE por MQTT:

1. **FIWARE -> MQTT**: um único container consulta todas as estações `WeatherObserved` e `AirQualityObserved` e publica diretamente no broker.
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

## Iniciar o publicador FIWARE-MQTT

O script conecta ao broker em `127.0.0.1:1883`, sem utilizador e sem password. Como esse endereço dentro do container aponta para o próprio container, use a rede do host no Linux:

```bash
docker run -d \
  --name fiware-mqtt \
  --restart unless-stopped \
  --network host \
  fiware-mqtt:local
```

Se o container já existir, use `docker start fiware-mqtt`.

## Consultar os logs

```bash
docker logs -f fiware-mqtt
```

## Observar mensagens MQTT

```bash
docker exec -it fiware-mosquitto \
  mosquitto_sub -h 127.0.0.1 -p 1883 -t 'fiware/#' -v
```

Exemplos de tópicos:

```text
fiware/weather/bolhao/temperature 21.5
fiware/weather/bolhao/relativeHumidity 63.1
fiware/airquality/polo_asprela/pm25 2.0
```

O container `fiware-mqtt-json-bridge` subscreve `fiware/#` e envia os valores para o Orion:

```bash
docker logs -f fiware-mqtt-json-bridge
```

## Parar o publicador

```bash
docker stop fiware-mqtt
docker rm fiware-mqtt
```
