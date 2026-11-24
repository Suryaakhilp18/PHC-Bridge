from typing import Dict, Any, List
from backend.ai.provider import AIProvider

class ReferralQualityAssistant:
    @staticmethod
    def analyze_referral(
        reason: str,
        priority: str,
        destination: str,
        age: int,
        sex: str
    ) -> Dict[str, Any]:
        """
        Reviews referral draft for administrative completeness and clarity.
        Strict rule: Never diagnoses or prescribes.
        """
        missing_fields = []
        recommendations = []
        score = 100
        
        # Check clarity and clinical justification length
        words = reason.strip().split()
        if len(words) < 5:
            missing_fields.append("Detailed presentation context (too brief)")
            recommendations.append("Provide more specific reason for referral, including duration and observed symptoms.")
            score -= 30
        elif len(words) < 10:
            recommendations.append("Consider specifying any previous medications tried or specific department needed.")
            score -= 10
            
        # Priority checks
        urgent_keywords = ["chest pain", "severe bleeding", "unconscious", "high fever with convulsion", "acute", "fracture", "respiratory distress"]
        has_urgent_signals = any(k in reason.lower() for k in urgent_keywords)
        if has_urgent_signals and priority == "Routine":
            missing_fields.append("Urgency misalignment")
            recommendations.append("Description contains acute symptoms. Review if priority should be upgraded to 'Urgent' or 'Emergency'.")
            score -= 25
            
        # Destination appropriateness
        if not destination or len(destination) < 3:
            missing_fields.append("Receiving facility designation")
            score -= 20
            
        if age > 65 and "geriatric" not in reason.lower():
            recommendations.append("Patient is a senior citizen; consider noting mobility or escort accompaniment requirements.")
            
        # Construct suggested wording
        suggested_wording = f"Patient ({age}y, {sex}) referred to {destination} for specialist evaluation regarding: '{reason.strip()}'. Baseline assessment completed at primary facility. Requested consultation and management recommendations."
        
        clarity_assessment = (
            "Excellent referral documentation with clear handoff context." if score >= 85
            else "Adequate referral note; consider addressing highlighted administrative fields." if score >= 60
            else "Referral note requires more administrative and clinical detail before hospital handoff."
        )
        
        return {
            "score": max(score, 10),
            "missing_fields": missing_fields,
            "clarity_assessment": clarity_assessment,
            "suggested_wording": suggested_wording,
            "recommendations": recommendations or ["Referral context meets standard referral guidelines."]
        }
