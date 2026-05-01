from app.services.safety_service import SafetyService


def main() -> None:
    service = SafetyService()
    service.rebuild()
    service.get_neighborhood_grid()


if __name__ == "__main__":
    main()
