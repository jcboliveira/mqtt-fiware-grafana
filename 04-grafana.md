# 4. Aceder e configurar o Grafana

## Abrir a interface

O Grafana publica a porta `3000` do servidor. A partir de outro computador, substitua `IP_DO_SERVIDOR` pelo endereço IP ou hostname real do servidor:

```text
http://IP_DO_SERVIDOR:3000
```

Por exemplo:

```text
http://192.168.1.50:3000
```

## Credenciais

As credenciais iniciais definidas no `compose.yaml` são:

- Utilizador: `admin`
- Password: `12345`

A datasource PostgreSQL `CrateDB` é criada automaticamente pelo `fiware-bootstrap`.

Para confirmar:

1. Abrir **Connections > Data sources**.
2. Selecionar **CrateDB**.
3. Confirmar host `crate:5432`, base de dados `doc` e executar o teste de ligação.

## Dashboard meteorológica

A dashboard `FIWARE - Monitorização Meteorológica` é criada automaticamente ao iniciar o ambiente. Abra **Dashboards > FIWARE > FIWARE - Monitorização Meteorológica**.

A primeira secção, **Média de todas as estações**, abre sempre no topo e apresenta os valores globais. As secções recolhíveis seguintes funcionam como abas por estação; o seletor **Estações** permite escolher quais ficam disponíveis. As novas estações são incluídas automaticamente.

A dashboard inclui:

- chuva acumulada por hora, em gráfico de barras;
- últimas medições de temperatura, humidade, vento, precipitação e índice UV;
- indicadores e evolução de cada estação;
- médias horárias de temperatura, humidade e vento para todas as estações;
- precipitação média horária de todas as estações.

A chuva acumulada usa `SUM(precipitation)`, assumindo que cada mensagem contém a quantidade de chuva incremental, em milímetros, desde a leitura anterior.

## Dashboard de qualidade do ar

A dashboard independente `FIWARE - Qualidade do Ar` está em **Dashboards > FIWARE > FIWARE - Qualidade do Ar**. Também começa pela secção **Média de todas as estações** e inclui secções recolhíveis por estação, com medições instantâneas e evolução horária de PM1, PM2.5, PM10, NO2, O3 e AQI.

## Dashboard de ruído

A dashboard independente `FIWARE - Ruído` está em **Dashboards > FIWARE > FIWARE - Ruído**. Apresenta o nível sonoro equivalente `LAeq` em dB, com média global atual, evolução horária, mapa das estações e secções recolhíveis por estação.

## Grafana Cloud

As dashboards também podem ser usadas numa stack Grafana Cloud. Como o hostname `crate` só existe na rede Docker local, o Grafana Cloud precisa de uma ligação à rede onde está o CrateDB.

### Ligar ao CrateDB

O método recomendado é o [Private Data Source Connect (PDC)](https://grafana.com/docs/grafana-cloud/connect-externally-hosted/private-data-source-connect/), que cria uma ligação cifrada sem expor a porta PostgreSQL à Internet.

1. Na stack Grafana Cloud, abra **Connections > Private data source connect** e crie uma ligação PDC.
2. Instale e execute o agente PDC no servidor que executa o Docker. Permita o destino `127.0.0.1:5432`; essa é a porta CrateDB publicada pelo `compose.yaml`.
3. Abra **Connections > Add new connection**, escolha **PostgreSQL** e selecione **Add new data source**.
4. Dê à datasource o nome `CrateDB` e selecione a ligação PDC criada.
5. Configure os campos:

| Campo | Valor |
| --- | --- |
| Host | `127.0.0.1:5432` |
| Database | `doc` |
| User | `crate` |
| TLS/SSL mode | `disable` |

6. Clique em **Save & test**. O teste deve confirmar a ligação ao CrateDB.

Não exponha a porta `5432` publicamente com a configuração atual: o ambiente de demonstração não configura autenticação nem TLS para o CrateDB. Para usar um endpoint público, configure autenticação, TLS e regras de firewall antes de o indicar na datasource Cloud.

### Importar as dashboards

1. Na stack Grafana Cloud, abra **Dashboards > New > Import dashboard**.
2. Escolha **Upload dashboard JSON** e importe [fiware-monitorizacao.json](mqtt-grafana/grafana/dashboards/fiware-monitorizacao.json).
3. Quando solicitado, associe todas as queries à datasource `CrateDB` criada anteriormente e clique em **Import**.
4. Repita o processo para [fiware-qualidade-ar.json](mqtt-grafana/grafana/dashboards/fiware-qualidade-ar.json).
5. Repita o processo para [fiware-ruido.json](mqtt-grafana/grafana/dashboards/fiware-ruido.json).

As dashboards importadas mantêm o seletor de estações, as secções por estação e a secção inicial com a média de todas as estações. No Grafana Cloud, as estações são obtidas diretamente do CrateDB através da ligação PDC.

## Criar uma dashboard personalizada

1. Abrir **Dashboards > New > New dashboard**.
2. Escolher **Add visualization**.
3. Selecionar **CrateDB**.
4. No editor **Code**, usar:

```sql
SELECT
  time_index AS "time",
  temperature,
  local
FROM doc.etweather
WHERE $__timeFilter(time_index)
ORDER BY time_index
```

5. Selecionar **Time series**.
6. Escolher **Last 24 hours**.
7. Definir o título `Temperatura por estação`.
8. Clicar em **Apply** e guardar a dashboard como `FIWARE - Monitorização`.

Para filtrar uma estação, acrescente:

```sql
AND local = 'Bolhão'
```

## Painel de qualidade do ar

Adicione outra visualização com esta query:

```sql
SELECT
  time_index AS "time",
  pm25,
  local
FROM doc.etairqualityobserved
WHERE $__timeFilter(time_index)
ORDER BY time_index
```

Escolha **Time series** e defina a unidade como `µg/m³`.
