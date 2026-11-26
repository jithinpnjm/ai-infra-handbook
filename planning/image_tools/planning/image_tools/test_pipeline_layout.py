def layout_pipeline():
    # 5 nodes
    # Node 1: Client
    # Node 2: Gateway
    # Node 3: TLS/L7 routing
    # Node 4: Endpoint picker
    # Node 5: Inference pods

    # Can we have:
    # x1: 40..170 (Client, w=130)
    # Gap 1: 170..490 (w=320) -> Contains the annotation box!
    # x2: 490..740 (Gateway, w=250)
    # Gap 2: 740..770 (w=30) -> Arrow 2
    # x3: 770..1030 (TLS/L7, w=260)
    # Gap 3: 1030..1060 (w=30) -> Arrow 3
    # x4: 1060..1300 (Picker, w=240)
    # Gap 4: 1300..1330 (w=30) -> Arrow 4
    # x5: 1330..1560 (Pods, w=230)
    pass
