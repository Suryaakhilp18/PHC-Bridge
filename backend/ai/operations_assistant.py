import re
from datetime import date
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.referral import Referral
from backend.models.followup import FollowUpTask
from backend.models.facility import Facility

class OperationsAssistant:
    @staticmethod
    def answer_query(query: str, db: Session) -> Dict[str, Any]:
        """
        Executes strict database queries for healthcare operations questions.
        Never fabricates numerical data.
        """
        q = query.lower()
        supporting_metrics = {}
        sql_intent = "AGGREGATE_METRICS"
        
        # 1. Total referrals query
        total_referrals = db.query(Referral).count()
        pending_ack = db.query(Referral).filter(Referral.status == "Referred").count()
        acknowledged = db.query(Referral).filter(Referral.status == "Acknowledged").count()
        completed = db.query(Referral).filter(Referral.status == "Completed").count()
        back_referrals = db.query(Referral).filter(Referral.status == "Back-Referred").count() + \
                         db.query(Referral).join(Referral.back_referral).count()
                         
        today = date.today()
        overdue_followups = db.query(FollowUpTask).filter(
            FollowUpTask.due_date < today,
            FollowUpTask.status != "Completed"
        ).count()
        
        due_followups = db.query(FollowUpTask).filter(
            FollowUpTask.due_date <= today,
            FollowUpTask.status != "Completed"
        ).count()
        
        supporting_metrics = {
            "total_referrals": total_referrals,
            "awaiting_acknowledgement": pending_ack,
            "acknowledged": acknowledged,
            "completed": completed,
            "back_referrals": back_referrals,
            "due_followups": due_followups,
            "overdue_followups": overdue_followups,
        }
        
        if "pending" in q or "awaiting" in q or "unacknowledged" in q:
            sql_intent = "SELECT count(*) FROM referrals WHERE status = 'Referred'"
            answer = f"There are currently {pending_ack} referrals awaiting hospital acknowledgement out of {total_referrals} total referrals across the network."
        elif "overdue" in q or "follow" in q:
            sql_intent = "SELECT count(*) FROM follow_up_tasks WHERE due_date < current_date AND status != 'Completed'"
            answer = f"There are {overdue_followups} overdue follow-up tasks and {due_followups} total follow-ups due as of today."
        elif "back" in q or "continuity" in q:
            sql_intent = "SELECT count(*) FROM back_referrals"
            answer = f"A total of {back_referrals} back-referrals have been initiated to return patients from district hospitals back to their local PHCs for continuity of care."
        elif "completion" in q or "rate" in q:
            rate = round((completed / max(total_referrals, 1)) * 100, 1)
            sql_intent = "SELECT (completed * 100.0 / total) FROM referrals"
            answer = f"The overall referral completion rate is {rate}%, with {completed} completed consultations out of {total_referrals} total referrals."
        elif "phc" in q or "facility" in q or "workload" in q:
            sql_intent = "SELECT destination, count(*) FROM referrals GROUP BY destination"
            workloads = db.query(Referral.receiving_facility_id, func.count(Referral.id))\
                          .group_by(Referral.receiving_facility_id).all()
            facilities = {f.id: f.name for f in db.query(Facility).all()}
            workload_summary = [f"{facilities.get(w[0], 'Unknown')}: {w[1]} referrals" for w in workloads[:3]]
            answer = f"Facility workload breakdown across top receivers: {', '.join(workload_summary) if workload_summary else 'No workload recorded yet'}."
        else:
            answer = f"Across the PHC Bridge network, there are {total_referrals} total referrals ({pending_ack} pending acknowledgement, {completed} completed, and {back_referrals} back-referred). {due_followups} follow-up tasks are scheduled for review."
            
        return {
            "question": query,
            "answer": answer,
            "supporting_metrics": supporting_metrics,
            "sql_intent": sql_intent
        }
