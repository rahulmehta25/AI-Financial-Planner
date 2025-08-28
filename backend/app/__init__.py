# Backend application package (avoid heavy imports at module load)

__all__: list[str] = []

def get_daily_operations_manager():
    from .automation import DailyOperationsManager
    return DailyOperationsManager