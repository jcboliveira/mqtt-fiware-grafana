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

## Criar a primeira dashboard

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
