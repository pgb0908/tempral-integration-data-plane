# tempral-integration-data-plane

n8n 스타일의 워크플로우 JSON을 [Temporal.io](https://temporal.io/) 위에서 실행하는 Flow Engine입니다.

## 개요

JSON으로 정의된 노드 DAG를 파싱하여 각 노드를 Temporal Activity로 실행합니다. 노드 간 데이터 라우팅, `$json`/`$node` 표현식 평가, 실행 상태 조회 및 취소 API를 제공합니다.

```
POST /workflows/execute  →  FlowWorkflow (Temporal)
                               └─ topological sort
                               └─ execute_node_activity × N
                               └─ 노드 간 데이터 라우팅
```

## 요구사항

- Python 3.11+
- [Temporal Server](https://docs.temporal.io/cli#start-dev-server) (로컬 실행용)

## 설치

```bash
pip install -e .

# 개발 의존성 포함
pip install -e ".[dev]"
```

## 실행

Temporal 로컬 서버를 먼저 시작합니다.

```bash
temporal server start-dev
```

이후 모드를 선택하여 실행합니다.

```bash
python main.py worker   # Temporal Worker만 실행
python main.py api      # FastAPI 서버만 실행 (port 8000)
python main.py both     # Worker + API 동시 실행
```

## API

### 워크플로우 실행

```bash
POST /workflows/execute
```

```json
{
  "workflow_definition": {
    "name": "My Workflow",
    "nodes": [...],
    "connections": {...}
  },
  "initial_data": [{"name": "World"}]
}
```

응답:

```json
{"workflow_id": "flow-xxxxxxxx-...", "status": "started"}
```

### 실행 상태 조회

```bash
GET /workflows/{workflow_id}/status
```

### 실행 결과 조회 (완료 대기)

```bash
GET /workflows/{workflow_id}/result
```

### 실행 취소

```bash
POST /workflows/{workflow_id}/cancel
```

## 워크플로우 JSON 형식

n8n 워크플로우 JSON 구조를 따릅니다.

```json
{
  "name": "Sample Workflow",
  "nodes": [
    {
      "id": "1",
      "name": "Start",
      "type": "n8n-nodes-base.manualTrigger",
      "parameters": {}
    },
    {
      "id": "2",
      "name": "SetGreeting",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "string": [
            {"name": "greeting", "value": "={{ \"Hello \" + $json.name }}"}
          ]
        }
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "SetGreeting", "type": "main", "index": 0}]]
    }
  }
}
```

## 지원 노드 타입

| 타입 | 설명 |
|---|---|
| `n8n-nodes-base.manualTrigger` | 시작 트리거, `initial_data` 주입 |
| `n8n-nodes-base.set` | 필드 추가/덮어쓰기 (`string`, `number`, `boolean`) |
| `n8n-nodes-base.httpRequest` | HTTP 요청 (item당 1건, httpx 사용) |
| `n8n-nodes-base.if` | 조건 분기 (port 0 = true, port 1 = false) |
| `n8n-nodes-base.noOp` | pass-through |
| `n8n-nodes-base.code` | sandboxed Python 코드 실행 |

## 표현식

`={{ ... }}` 형식으로 노드 파라미터 내에서 표현식을 사용할 수 있습니다.

| 표현식 | 설명 |
|---|---|
| `={{ $json.fieldName }}` | 현재 처리 중인 item의 필드 접근 |
| `={{ $json.a + " " + $json.b }}` | 문자열 연결 등 연산 |
| `={{ $node['NodeName'].json.field }}` | 이전 노드 결과 참조 |

## 구성도

```mermaid
graph TD
    main["main.py<br/>(진입점)"]

    subgraph api["flow_engine/api/"]
        app["app.py<br/>FastAPI + lifespan"]
        dep["dependencies.py<br/>Temporal Client 전역 관리"]
        r_wf["routes/workflow.py<br/>POST /workflows/execute"]
        r_ex["routes/execution.py<br/>status / result / cancel"]
    end

    subgraph temporal["flow_engine/temporal/"]
        wf["workflow.py<br/>FlowWorkflow<br/>(Query / Signal)"]
        act["activities.py<br/>execute_node_activity"]
        wrk["worker.py<br/>Worker 부트스트랩"]
    end

    subgraph parser["flow_engine/parser/"]
        wp["workflow_parser.py<br/>JSON → WorkflowDefinition"]
        gb["graph_builder.py<br/>DAG / 위상정렬 / 분기 라우팅"]
    end

    subgraph expr["flow_engine/expression/"]
        ev["evaluator.py<br/>$json · $node 평가기"]
        sb["sandbox.py<br/>AttrDict / NodeAccessor"]
    end

    subgraph nodes["flow_engine/nodes/"]
        base["base.py<br/>BaseNodeExecutor"]
        reg["registry.py<br/>타입 → Executor 매핑"]
        impl["trigger / set / if<br/>http / code / no_op"]
    end

    subgraph models["flow_engine/models/"]
        mn["node.py<br/>NodeDefinition · NodeType"]
        mw["workflow.py<br/>WorkflowDefinition"]
        me["execution.py<br/>ExecutionContext · NodeResult"]
    end

    main --> app
    main --> wrk
    app --> dep
    app --> r_wf
    app --> r_ex
    r_wf --> dep
    r_ex --> dep
    wrk --> wf
    wrk --> act
    wf --> wp
    wf --> gb
    wf --> act
    act --> reg
    reg --> impl
    impl --> base
    impl --> ev
    ev --> sb
    wp --> mw
    gb --> mn
    act --> me
```

## 호출 흐름도

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as FastAPI<br/>/workflows/execute
    participant TC as Temporal Client
    participant TS as Temporal Server<br/>(localhost:7233)
    participant WF as FlowWorkflow<br/>(Temporal Workflow)
    participant ACT as execute_node_activity<br/>(Temporal Activity)
    participant EX as NodeExecutor<br/>(trigger/set/if/http/code/noOp)

    Client->>API: POST /workflows/execute<br/>{ workflow_definition, initial_data }
    API->>API: WorkflowParser.parse()
    API->>TC: client.start_workflow(FlowWorkflow)
    TC->>TS: 워크플로우 등록
    API-->>Client: { workflow_id, status: "started" }

    TS->>WF: FlowWorkflow.run(request)
    WF->>WF: WorkflowParser.parse()
    WF->>WF: WorkflowGraph() → topological_sort()
    Note over WF: 실행 순서 결정 (Kahn's algorithm)

    loop 각 노드 (위상정렬 순)
        WF->>ACT: execute_activity(execute_node_activity,<br/>node, input_items, context)
        ACT->>ACT: get_executor(node.type)
        ACT->>EX: executor.execute(node, input_items, context)

        alt Set / Code 노드
            EX->>EX: ExpressionEvaluator.evaluate()<br/>($json, $node 표현식 처리)
        else HTTP Request 노드
            EX->>EX: httpx.AsyncClient.request()
        else IF 노드
            EX->>EX: 조건 평가 → port 0 (true) / port 1 (false)
        end

        EX-->>ACT: NodeResult { output_data, status }
        ACT-->>WF: result dict
        WF->>WF: 다음 노드로 output_data 라우팅<br/>node_inputs[next_node] += port_items
    end

    WF-->>TS: ExecutionContext (최종 결과)

    Client->>API: GET /workflows/{id}/result
    API->>TC: workflow_handle.result()
    TC->>TS: 결과 조회 (완료 대기)
    TS-->>TC: ExecutionContext
    TC-->>API: result
    API-->>Client: { workflow_id, result: ExecutionContext }
```

## 프로젝트 구조

```
tempral-integration-data-plane/
├── pyproject.toml
├── main.py                         # 진입점 (worker / api / both)
│
├── flow_engine/
│   ├── models/
│   │   ├── node.py                 # NodeDefinition, NodeType
│   │   ├── workflow.py             # WorkflowDefinition
│   │   └── execution.py           # ExecutionContext, NodeResult
│   │
│   ├── parser/
│   │   ├── workflow_parser.py      # JSON → WorkflowDefinition
│   │   └── graph_builder.py       # DAG 구성, 위상정렬, 분기 라우팅
│   │
│   ├── expression/
│   │   ├── evaluator.py           # $json, $node 표현식 평가기
│   │   └── sandbox.py             # AttrDict, NodeAccessor
│   │
│   ├── nodes/
│   │   ├── base.py                # BaseNodeExecutor
│   │   ├── trigger.py
│   │   ├── set_node.py
│   │   ├── http_request.py
│   │   ├── if_node.py
│   │   ├── no_op.py
│   │   ├── code_node.py
│   │   └── registry.py
│   │
│   ├── temporal/
│   │   ├── activities.py          # execute_node_activity
│   │   ├── workflow.py            # FlowWorkflow (Query/Signal)
│   │   └── worker.py
│   │
│   └── api/
│       ├── app.py
│       └── routes/
│           ├── workflow.py        # POST /workflows/execute
│           └── execution.py      # status / result / cancel
│
└── tests/
    ├── fixtures/sample_workflow.json
    ├── test_parser.py
    ├── test_expression.py
    └── test_nodes.py
```

## 테스트

```bash
pytest tests/ -v
```

## 의존성

- [temporalio](https://github.com/temporalio/sdk-python) — Temporal Python SDK
- [fastapi](https://fastapi.tiangolo.com/) — REST API
- [pydantic](https://docs.pydantic.dev/) v2 — 데이터 모델 및 직렬화
- [httpx](https://www.python-httpx.org/) — 비동기 HTTP 클라이언트
- [simpleeval](https://github.com/danthedeckie/simpleeval) — 표현식 평가
- [uvicorn](https://www.uvicorn.org/) — ASGI 서버
