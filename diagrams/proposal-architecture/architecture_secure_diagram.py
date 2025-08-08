from diagrams import Diagram, Cluster, Edge

# AWS
from diagrams.aws.network import CloudFront, APIGateway, Route53
from diagrams.aws.security import WAF, KMS, Shield, SecretsManager
from diagrams.aws.integration import Eventbridge, SQS
from diagrams.aws.database import RDS
from diagrams.aws.engagement import SES
from diagrams.aws.management import Cloudtrail, Cloudwatch
from diagrams.aws.general import General  # para VPC Endpoints (ícono genérico)

# K8s
from diagrams.k8s.network import Ing
from diagrams.k8s.compute import Pod
from diagrams.k8s.infra import Node
from diagrams.k8s.storage import PV

# Genéricos
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL


graph_opts = {
    "rankdir": "LR",       # izquierda -> derecha
    "splines": "ortho",    # líneas rectas en ángulo
    "nodesep": "0.45",     # separación entre nodos
    "ranksep": "0.6",      # separación entre filas
    "pad": "0.2",
}

node_opts = {
    "shape": "box",
}

edge_opts = {
    "arrowsize": "0.8",
}


with Diagram(
    "OmniOne OpenDID - Secure Architecture (Compact)",
    filename="output/omnione-architecture-secure",
    show=False,
    graph_attr=graph_opts,
    node_attr=node_opts,
    edge_attr=edge_opts,
):

    # ======= Fila 1: DNS/Edge + API público =======
    with Cluster("Public DNS & Edge", graph_attr={"rank": "same"}):
        dns_a = Route53("DNS Zone A")
        dns_b = Route53("DNS Zone B")
        shield = Shield("Shield Advanced (opcional)")
        waf_edge = WAF("WAF (managed)")
        cf = CloudFront("CloudFront")

    api_gw_pub = APIGateway("API Gateway (Público)")

    # Alineación horizontal de la primera fila
    dns_a >> cf
    dns_b >> cf
    shield >> waf_edge >> cf
    cf >> api_gw_pub

    # ======= Fila 2: VPC (presentación privada + seguridad + workloads) =======
    with Cluster("VPC", graph_attr={"rank": "same"}):

        # Subfila 2A: Seguridad (columna delgada)
        with Cluster("Security Layer", graph_attr={"rank": "same"}):
            kms = KMS("AWS KMS / HSM\n(Sign/Verify)")
            secrets = SecretsManager("Secrets Manager\n(rotación)")
            cloudtrail = Cloudtrail("CloudTrail\n(auditoría)")
            cw_logs = Cloudwatch("CloudWatch\n(logs/metrics)")
            sec_guard = General("GuardDuty\n(detección)")
            sec_hub = General("Security Hub\n(postura)")

        # Subfila 2B: VPC Endpoints (columna delgada)
        with Cluster("VPC Endpoints / PrivateLink", graph_attr={"rank": "same"}):
            vpce_s3 = General("VPC Endpoint: S3")
            vpce_kms = General("VPC Endpoint: KMS")
            vpce_secrets = General("VPC Endpoint: Secrets")
            vpce_cw = General("VPC Endpoint: CloudWatch")

        # Subfila 2C: API privada (centrado)
        api_gw_priv = APIGateway("API Gateway (Privado)")

        # Subfila 2D: EKS Core (bloque central)
        with Cluster("EKS - Core DID", graph_attr={"rank": "same"}):
            # Mantener estos en misma fila para compactar
            ingress = Ing("Ingress / Service Mesh (mTLS)")
            node_a = Node("Node A")
            node_b = Node("Node B")

            with Cluster("issuer-services-ns", graph_attr={"rank": "same"}):
                issuer = Pod("Issuer service")

            with Cluster("verifier-services-ns", graph_attr={"rank": "same"}):
                verifier = Pod("Verifier service")

            legacy_api = Pod("Legacy API middleware")
            cert_vol = PV("Certificate Volume (ro)")

            # Alineaciones invisibles dentro de EKS (horizontal)
            ingress - Edge(style="invis") - issuer
            issuer - Edge(style="invis") - verifier
            verifier - Edge(style="invis") - legacy_api
            # Nodos abajo pero alineados horizontalmente
            ingress - Edge(style="invis") - node_a
            node_a - Edge(style="invis") - node_b

        # Subfila 2E: ECS Periférico (a la derecha de EKS)
        with Cluster("ECS Fargate - Peripheral Services", graph_attr={"rank": "same"}):
            wallet = Server("Task: Wallet")
            user = Server("Task: User")
            capp = Server("Task: CApp")
            notif = Server("Task: Notification")

            # Alinear horizontal
            wallet - Edge(style="invis") - user
            user - Edge(style="invis") - capp
            capp - Edge(style="invis") - notif

        # Subfila 2F: Async/Events (columna a la derecha)
        with Cluster("Async / Events", graph_attr={"rank": "same"}):
            bus = Eventbridge("EventBridge")
            queue = SQS("SQS (retries/DLQ)")
            bus - Edge(style="invis") - queue

        # Subfila 2G: Data Layer (muy a la derecha, misma fila)
        with Cluster("Data Layer", graph_attr={"rank": "same"}):
            rds = RDS("RDS PostgreSQL (Multi-AZ)")
            pg = PostgreSQL("Logical DB")
            fabric = Server("HyperLedger Fabric\n(gestionado o dedicado)")

            rds - Edge(style="invis") - pg
            pg - Edge(style="invis") - fabric

    # ======= Fila 3: Servicio de correo (extremo derecho) =======
    mail = SES("Mail service (externo)")

    # ---------- Conexiones compactas ----------

    # Público -> Ingress (expuestos)
    api_gw_pub >> ingress
    # Privado -> Ingress (tráfico interno)
    api_gw_priv >> ingress

    # EKS core
    ingress >> [issuer, verifier, legacy_api]

    # ECS periférico consume API privada (no toca Ingress)
    [wallet, user, capp] >> api_gw_priv

    # Servicio de firma aislado (alineado cerca de EKS)
    signing = Server("Signing Service (aislado)")
    [issuer, verifier, legacy_api] >> signing >> kms

    # Secretos y VPC endpoints (punteados, compactos)
    for svc in [issuer, verifier, legacy_api, wallet, user, capp, notif]:
        svc >> Edge(style="dotted") >> secrets
        svc >> Edge(style="dotted") >> vpce_kms
        svc >> Edge(style="dotted") >> vpce_secrets
        svc >> Edge(style="dotted") >> vpce_cw

    # Event-driven (de core a notif)
    [issuer, verifier] >> bus >> queue >> notif
    notif >> Edge(style="dotted") >> mail

    # Certs sólo en core
    [issuer, verifier] >> Edge(style="dotted") >> cert_vol

    # Acceso a datos (uno a muchos, pero compactado)
    [issuer, verifier, legacy_api, wallet, user, capp] >> rds
    rds >> pg
    rds >> fabric

    # Telemetría / auditoría
    for comp in [api_gw_pub, api_gw_priv, ingress, issuer, verifier, wallet, user, capp, notif, legacy_api, signing]:
        comp >> Edge(style="dotted") >> cw_logs
    [kms, secrets, api_gw_pub, api_gw_priv] >> cloudtrail

    # Alineaciones invisibles entre grandes bloques (para mantener todo en una sola "fila")
    cf - Edge(style="invis") - api_gw_pub
    api_gw_pub - Edge(style="invis") - api_gw_priv
    api_gw_priv - Edge(style="invis") - ingress
    ingress - Edge(style="invis") - wallet
    wallet - Edge(style="invis") - bus
    bus - Edge(style="invis") - rds
    rds - Edge(style="invis") - mail
