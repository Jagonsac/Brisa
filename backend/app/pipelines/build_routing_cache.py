from app.services.edge_weight_service import EdgeWeightService


def main() -> None:
    payload = EdgeWeightService().rebuild()
    print(f"Edge metrics generated: version={payload.get('version')} edges={len(payload.get('edges', {}))}")


if __name__ == "__main__":
    main()
