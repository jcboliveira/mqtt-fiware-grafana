# 5. Consultas e manutenção

## Views disponíveis

- `doc.etweather`: temperatura, humidade, vento, precipitação e UV.
- `doc.etairqualityobserved`: PM10, PM2.5, PM1, AQI, NO2 e O3.
- `doc.etnoiselevelobserved`: nível sonoro equivalente `LAeq`, em dB, e localização das estações.

## Testar dados no CrateDB

```bash
docker exec fiware-crate curl -sS http://127.0.0.1:4200/_sql \
  -H 'Content-Type: application/json' \
  --data-binary '{"stmt":"SELECT * FROM doc.etweather LIMIT 5"}'
```

Depois de iniciar um dos publicadores MQTT com suporte a ruído, confirme o histórico com:

```bash
docker exec fiware-crate curl -sS http://127.0.0.1:4200/_sql \
  -H 'Content-Type: application/json' \
  --data-binary '{"stmt":"SELECT time_index, local, laeq FROM doc.etnoiselevelobserved LIMIT 5"}'
```

## Parar o ambiente

```bash
cd /root/mqtt-grafana
docker compose down
```

Para parar e remover também os volumes, apagando dashboards e dados persistidos:

```bash
docker compose down -v
```

Use `down -v` apenas para reiniciar o ambiente do zero.
