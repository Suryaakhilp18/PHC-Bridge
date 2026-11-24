from typing import Dict, Any, List
from backend.models.referral import Referral

class JourneySummarizer:
    @staticmethod
    def summarize_journey(referral: Referral) -> Dict[str, Any]:
        """
        Synthesizes verified factual timeline events into a clear executive journey summary.
        Explicitly distinguishes documented facts from administrative AI summaries.
        """
        facts = []
        pending = []
        
        p = referral.patient
        patient_desc = f"{p.full_name} ({p.age}y/{p.sex}, Code: {p.patient_code})" if p else "Patient"
        
        # Documented timeline facts
        facts.append({
            "stage": "Referral Origin",
            "detail": f"Initiated at {referral.referring_facility.name if referral.referring_facility else 'PHC'} by Dr. {referral.referring_doctor.full_name if referral.referring_doctor else 'MO'}.",
            "date": referral.created_at.strftime("%d %b %Y %H:%M")
        })
        
        if referral.acknowledged_at:
            facts.append({
                "stage": "Hospital Receipt",
                "detail": f"Confirmed by receiving team at {referral.receiving_facility.name if referral.receiving_facility else 'Hospital'}.",
                "date": referral.acknowledged_at.strftime("%d %b %Y %H:%M")
            })
        else:
            pending.append(f"Awaiting hospital acknowledgement by {referral.receiving_facility.name if referral.receiving_facility else 'Hospital'}.")
            
        if referral.outcome:
            facts.append({
                "stage": "Specialist Consultation",
                "detail": f"Consultation conducted by Dr. {referral.outcome.doctor_name}. Outcome: '{referral.outcome.outcome_notes}'",
                "date": referral.outcome.created_at.strftime("%d %b %Y %H:%M")
            })
        elif referral.status == "Acknowledged":
            pending.append("Patient handoff received; consultation outcome pending documentation.")
            
        if referral.back_referral:
            br = referral.back_referral
            facts.append({
                "stage": "Back-Referral Established",
                "detail": f"Return instructions: '{br.follow_up_instructions}'. Scheduled target: {br.follow_up_date.strftime('%d %b %Y') if br.follow_up_date else 'As needed'}.",
                "date": br.created_at.strftime("%d %b %Y %H:%M")
            })
            
        if referral.follow_up_tasks:
            for task in referral.follow_up_tasks:
                facts.append({
                    "stage": f"Follow-up ({task.status})",
                    "detail": f"Assigned to {task.assigned_to_name or 'CHO'} for {task.due_date.strftime('%d %b %Y')}. Notes: {task.notes or 'Routine review'}",
                    "date": task.created_at.strftime("%d %b %Y %H:%M")
                })
                if task.status != "Completed":
                    pending.append(f"Follow-up task by {task.assigned_to_name or 'CHO'} due {task.due_date.strftime('%d %b %Y')}.")

        # Generate summary
        narrative_parts = [
            f"{patient_desc} was referred with priority '{referral.priority}' due to '{referral.reason}'."
        ]
        if referral.status == "Referred":
            narrative_parts.append("Referral is currently dispatched and awaiting receipt confirmation.")
        elif referral.status == "Acknowledged":
            narrative_parts.append("Handoff has been acknowledged by the district hospital; consultation is in queue.")
        elif referral.status == "Completed":
            narrative_parts.append("Hospital consultation completed. Care instructions recorded.")
            if referral.back_referral:
                narrative_parts.append("Back-referral created to maintain continuity of care at the originating PHC.")
                
        if pending:
            narrative_parts.append(f"Current open action items: {'; '.join(pending)}")
            
        return {
            "referral_id": referral.id,
            "patient_summary": patient_desc,
            "timeline_facts": facts,
            "ai_generated_summary": " ".join(narrative_parts),
            "pending_actions": pending
        }
