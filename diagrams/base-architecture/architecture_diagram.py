from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Internet
from diagrams.onprem.container import Docker
from diagrams.onprem.storage import Ceph
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Ing
from diagrams.k8s.infra import Node
from diagrams.k8s.storage import PV
from diagrams.aws.network import CloudFront, APIGateway, Route53
from diagrams.aws.security import WAF
from diagrams.aws.database import RDS
from diagrams.aws.engagement import SES

with Diagram(
    "OmniOne OpenDID - Architecture",
    filename="output/omnione-architecture",
    direction="LR",
    show=False,
):

    with Cluster("Public DNS & Security"):
        dns1 = Route53("DNS Zones")
        dns2 = Route53("DNS Zones")
        dns3 = Route53("DNS Zones")
        dns_policy = WAF("Security Policy")

    # ==== VPC ====
    with Cluster("VPC"):
        # ---- Capa de Presentación ----
        with Cluster("Presentation Layer"):
            cf = CloudFront("Amazon CloudFront")
            waf = WAF("Web Application Firewall (WAF)")
            api_gw = APIGateway("Amazon API Gateway")

        # ---- Capa de Aplicación usando K8s ----
        with Cluster("K8s"):
            ingress = Ing("Ingress")

            # Nodos
            node1 = Node("Node 01")
            noden = Node("Node n")

            #  Servicios
            with Cluster("Application Layer"):

                # Namespaces de microservicios
                with Cluster("verifier-services-ns"):
                    verifier = Pod("Verifier service")

                with Cluster("issuer-services-ns"):
                    issuer = Pod("Issuer service")

                with Cluster("wallet-services-ns"):
                    wallet = Pod("Wallet service")
                    capp = Pod("CApp service")  
                    user = Pod("User service")

                legacy_api = Pod("Legacy API middleware")

                # Volumen de certificados
                cert_vol = PV("Certificate Volume")

                with Cluster("trusted-ns"):
                    trust_agent = Pod("Trust agent")
                    trusted_notif = Pod("Trusted Notification service")

                # Servicios externos
                with Cluster("external-services-ns"):
                    notif = Pod("Notification service")

        # ---- Bases de Datos ----
        with Cluster("Database Layer"):
            rds = RDS("Amazon RDS")
            pg = PostgreSQL("PostgreSQL")
            hlf = Server("HyperLedger Fabric")

    # ==== Capa Legacy externa ====
    with Cluster("Legacy Layer"):
        legacy1 = Server("Legacy Service 1")
        legacy2 = Server("Legacy Service 2")

    # ==== Servicio de Mail  ====
    mail = SES("Mail service")

    # ==== Tráfico y Relaciones ====

    # DNS / Seguridad -> CloudFront/WAF
    dns1 >> cf
    dns2 >> cf
    dns3 >> cf
    dns_policy >> cf

    # Edge hacia presentación
    cf >> waf >> api_gw >> ingress

    # Ingress a servicios
    ingress >> wallet
    ingress >> capp
    ingress >> user

    # Flujos principales
    api_gw >> Edge(style="dashed") >> issuer
    issuer >> Edge(style="dashed") >> verifier
    verifier >> Edge(style="dashed") >> legacy_api

    trust_agent >> trusted_notif
    notifier_edge = user >> Edge(style="dotted") >> notif  # comunicación externa

    [wallet, capp, user] >> Edge(style="dotted") >> cert_vol

    [wallet, capp, user, issuer, verifier, legacy_api] >> rds
    rds >> pg
    rds >> hlf

    # Legacy layer relación con middleware
    legacy_api << Edge(style="dotted") << legacy1
    legacy_api << Edge(style="dotted") << legacy2

    # Mail service 
    notif >> Edge(style="dotted") >> mail

    # Nodos K8s
    ingress - Edge(style="invis") - node1
    node1 - Edge(style="invis") - noden
