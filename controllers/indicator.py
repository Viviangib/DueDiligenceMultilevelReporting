from sqlalchemy.orm import Session
from services.indicator import IndicatorService

indicator_service = IndicatorService()

def save_indicator_controller(db: Session, indicator_data: dict):
    return indicator_service.save_indicator(db, indicator_data) 