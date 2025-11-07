from sqlalchemy.orm import Session
from models.indicator import Indicator
from models.indicator_status import IndicatorStatus


class IndicatorService:
    def save_indicator(self, db: Session, indicator_data: dict) -> Indicator:
        indicator = Indicator(
            indicator_id=indicator_data["indicator_id"],
            indicator=indicator_data["indicator"],
            process_id=indicator_data["process_id"],
        )
        db.add(indicator)
        db.commit()
        db.refresh(indicator)
        return indicator

    def create_status_job(self, db: Session) -> IndicatorStatus:
        status_job = IndicatorStatus(status="in_progress")
        db.add(status_job)
        db.commit()
        db.refresh(status_job)
        return status_job
