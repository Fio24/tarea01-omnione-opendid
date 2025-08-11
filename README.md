# Tarea 01 – OmniOne OpenDID: Arquitectura Segura y Recomendaciones

Este repositorio contiene dos versiones del diagrama de arquitectura de **OmniOne OpenDID**:

- **Base Architecture**: Diagrama inicial de referencia, modelado según la arquitectura vista en clase.  
- **Secure Architecture (Proposal)**: Versión propuesta con mejoras de seguridad y arquitectura, explicadas en este README.

La herramienta utilizada para generar ambos diagramas es [`diagrams`](https://diagrams.mingrammer.com/) en Python.

---

## 📂 Estructura del repositorio

TAREA01-OMNIONE-OPENDID/
│
├── diagrams/
│ ├── base-architecture/
│ │ ├── architecture_diagram.py # Script para generar diagrama base
│ │ └── output/
│ │ └── omnione-architecture.png # Imagen del diagrama base (generada)
│ │
│ ├── proposal-architecture/
│ ├── architecture_secure_diagram.py # Script para generar diagrama seguro
│ └── output/
│ └── omnione-architecture-secure.png # Imagen diagrama seguro (generada)
│
└── README.md


---

---

## 1) Descripción breve del proyecto

La solución modela **OmniOne OpenDID** desplegado en AWS con enfoque en separación de capas, principios de mínimo privilegio y controles de perímetro y observabilidad.

### 1.1 Diagrama Base (visto en clase)
Corresponde al script `architecture_diagram.py` y refleja la arquitectura trabajada en clase:

- **Public DNS & Security**: *Route 53* (múltiples zonas) + *AWS WAF* como política de seguridad a nivel de borde.
- **VPC**
  - **Presentation Layer**: *CloudFront* (CDN y caché), *WAF*, *API Gateway* (entrada a servicios).
  - **Kubernetes (EKS)**: Ingress (exposición interna), nodos (`Node 01`, `Node n`) y pods por **namespaces**:
    - `verifier-services-ns`: `Verifier service`
    - `issuer-services-ns`: `Issuer service`
    - `wallet-services-ns`: `Wallet`, `CApp`, `User`
    - Servicios transversales: `Legacy API middleware`, `Trusted Notification service`, `Trust agent`
    - Volumen de certificados: `Certificate Volume (PV)`
  - **Database Layer**: `Amazon RDS`, `PostgreSQL` y `HyperLedger Fabric`.
- **Legacy Layer**: servicios heredados externos integrados vía `Legacy API middleware`.
- **Servicios externos**: *SES* para correo.
- **Flujos principales**:
  - DNS/WAF → CloudFront → API Gateway → Ingress
  - `issuer` ⇄ `verifier` ⇄ `legacy_api`
  - Apps (`wallet`, `capp`, `user`) consumen vía Ingress/API; escriben en RDS y leen/escriben certificados en `PV`.
  - `legacy_api` integra con `Legacy Service 1/2`.
  - `notif` → `SES` para correo.


---

## 2) Propuesta de Arquitectura Segura (Secure Architecture)

El script `architecture_secure_diagram.py` busca mejorar controles defensivos, segmentación y servicios gestionados en la arquitectura base. A continuación, se describe **qué se añade o cambia** y **cuál es el factor de seguridad** concreto.

### 2.1 Perímetro y exposición controlada
- **Shield Advanced + WAF administrado + CloudFront** al frente de **API Gateway Público**.
  - **Factor de seguridad**: Protección DDoS a nivel L3/L7, reglas administradas y bloqueo de OWASP Top 10; reducción de superficie de ataque en orígenes.

### 2.2 API dual: público y privado
- **API Gateway (Privado)** dentro de la VPC para comunicación **interna** (p. ej., servicios periféricos) y **API Gateway (Público)** solo para endpoints estrictamente necesarios.
  - **Factor de seguridad**: Menos exposición pública; segmentación de tráfico; políticas de IAM más estrictas.

### 2.3 Servicio de firma aislado + KMS/HSM
- **Signing Service** dedicado para operaciones *sign/verify* que delega en **AWS KMS/HSM**.
  - **Factor de seguridad**: Las claves privadas **nunca** salen del HSM; control de acceso granular (IAM/KMS), auditoría (CloudTrail) y rotación de llaves.

### 2.4 Gestión de secretos centralizada
- **AWS Secrets Manager** para credenciales, certificados y tokens con rotación automática.
  - **Factor de seguridad**: Elimina secretos embebidos en código; versionamiento y rotación; trazabilidad de uso.

### 2.5 Controles de *egress* y *PrivateLink*
- **VPC Endpoints / PrivateLink** (S3, KMS, Secrets, CloudWatch) y **denegar salida a Internet por defecto**.
  - **Factor de seguridad**: Evita exfiltración; tráfico hacia servicios AWS sin pasar por Internet público.

### 2.6 Workloads: núcleo en EKS, periféricos en ECS Fargate
- **EKS (Core DID)**: `issuer`, `verifier`, `legacy_api`, `Ingress` con **service mesh/mTLS**.
- **ECS Fargate (Periféricos)**: `wallet`, `user`, `cApp`, `notification` como *tasks* sin administrar nodos.
  - **Factor de seguridad**: Menor superficie de ataque y menor esfuerzo de *patching* en periféricos.

### 2.7 Integración asíncrona y resiliencia
- **EventBridge** + **SQS** (reintentos, DLQ) para eventos entre `issuer/verifier` y `notification`.
  - **Factor de seguridad**: Desacopla y evita presión sobre APIs; contención de fallos y *backpressure*; menor riesgo de denegación por picos.

### 2.8 Capa de datos y certificados
- **RDS PostgreSQL Multi-AZ** como base transaccional; **HyperLedger Fabric** para capacidades DID/ledger; volumen de certificados **solo para core** (`issuer`, `verifier`) en **solo-lectura cuando aplique**.
  - **Factor de seguridad**: Alta disponibilidad; separación de responsabilidades y principio de mínimo privilegio en acceso a credenciales/certificados.

### 2.9 Observabilidad y cumplimiento
- **CloudWatch (logs/métricas)**, **CloudTrail (auditoría)**, **GuardDuty (detección)**, **Security Hub (postura)**.
  - **Factor de seguridad**: Telemetría centralizada, detección de anomalías, evidencias de auditoría y alertamiento.


---

## 3) Cómo generar los diagramas


### 3.1 Requisitos previos
- **Graphviz** instalado (agregar `bin` al `PATH`).
- **Python 3.8+**.
- Instalar librerías:
```bash
pip install diagrams graphviz
```

### Diagrama base
```
cd diagrams/base-architecture
python architecture_diagram.py
# Imagen generada en: diagrams/base-architecture/output/omnione-architecture.png
```

### Diagrama seguro
```
cd diagrams/proposal-architecture
python architecture_secure_diagram.py
# Imagen generada en: diagrams/proposal-architecture/output/omnione-architecture-secure.png
```
