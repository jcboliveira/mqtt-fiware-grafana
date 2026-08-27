# 3. Executar e validar o MQTT

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
