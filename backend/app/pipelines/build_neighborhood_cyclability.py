from app.services.cyclability_service import CyclabilityService


def main() -> None:
    payload = CyclabilityService().rebuild()
    print(
        "Neighborhood cyclability generated:",
        f"version={payload['metadata'].get('version')}",
        f"neighborhoods={len(payload.get('neighborhoods', []))}",
    )


if __name__ == "__main__":
    main()
