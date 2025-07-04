from sqlalchemy.orm import Session
from models.indicator import Indicator
from schemas.indicator import IndicatorCreate

class IndicatorService:
    def save_indicator(self, db: Session, indicator_data: dict) -> Indicator:
        indicator = Indicator(indicator=indicator_data)
        db.add(indicator)
        db.commit()
        db.refresh(indicator)
        return indicator 