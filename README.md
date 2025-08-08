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

## 1. Descripción breve del proyecto

La arquitectura modela un sistema **OmniOne OpenDID** desplegado en AWS, siguiendo buenas prácticas de seguridad en la nube.

- **Capa de presentación (Edge)**: Route 53, CloudFront, WAF y API Gateway (público y privado).  
- **Capa de seguridad transversal**: Servicio de firma aislado con KMS/HSM, Secrets Manager, GuardDuty, Security Hub y CloudTrail.  
- **Capa de aplicación**:  
  - **EKS (Kubernetes)** para servicios core DID (`issuer`, `verifier`, `legacy API middleware`) con mTLS (service mesh).  
  - **ECS Fargate** para servicios periféricos (`wallet`, `user`, `cApp`, `notification`).  
- **Integración asíncrona**: EventBridge y SQS para comunicación desacoplada.  
- **Capa de datos**: RDS PostgreSQL Multi-AZ, HyperLedger Fabric.  
- **Servicios externos**: SES para correo.

---

## 2. Recomendaciones de arquitectura y seguridad

### Recomendación 1 — Servicio de firma aislado + KMS/HSM
**Descripción:** Centralizar operaciones de firma/verificación en un microservicio que usa AWS KMS/HSM.  
**Factor de seguridad:** Claves privadas nunca expuestas; privilegios mínimos con IAM/KMS; auditoría en CloudTrail; rotación automática.

### Recomendación 2 — Gestión centralizada de secretos con rotación automática
**Descripción:** Uso de AWS Secrets Manager para credenciales, certificados y tokens.  
**Factor de seguridad:** Elimina secretos hardcodeados; rotación automática; trazabilidad.

### Recomendación 3 — Control de Egress y VPC Endpoints
**Descripción:** Denegar salida a Internet por defecto y usar VPC Endpoints/PrivateLink.  
**Factor de seguridad:** Minimiza exfiltración de datos; tráfico AWS sin pasar por Internet.


### Recomendación 4 — Arquitectura híbrida EKS + ECS Fargate
**Descripción:** Mantener servicios críticos en EKS y periféricos en ECS Fargate.  
**Factor de seguridad:** Menos parches y menor superficie de ataque en workloads periféricos; aislamiento por ENI/SG.

---

## 3. Cómo generar los diagramas

### Requisitos previos
- **Graphviz** instalado y su carpeta `bin` agregada al `PATH`.
- Python 3.8+ instalado.
- Librerías de Python necesarias:
```bash
pip install diagrams graphviz
```

### Diagrama base
```
cd diagrams/base-architecture
python -m venv .venv
. .venv/Scripts/Activate.ps1   # PowerShell
pip install diagrams graphviz
python architecture_diagram.py

# Imagen generada en: diagrams/base-architecture/output/omnione-architecture.png
```

### Diagrama seguro
```
cd diagrams/proposal-architecture
python -m venv .venv
. .venv/Scripts/Activate.ps1   # PowerShell
pip install diagrams graphviz
python architecture_secure_diagram.py
# Imagen generada en: diagrams/proposal-architecture/output/omnione-architecture-secure.png
```
